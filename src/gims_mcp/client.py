"""HTTP client for GIMS Automation API."""

import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from .config import Config


class GimsApiError(Exception):
    """Exception raised when GIMS API returns an error."""

    def __init__(self, status_code: int, message: str, detail: str | None = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"GIMS API Error ({status_code}): {message}")


class GimsAuthError(GimsApiError):
    """Exception raised when authentication fails and cannot be recovered."""

    pass


class GimsClient:
    """Async HTTP client for GIMS Automation API."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"{config.url}/automation"
        self._access_token = config.access_token
        self._refresh_token = config.refresh_token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
        return self._client

    async def _recreate_client(self) -> httpx.AsyncClient:
        """Close and recreate HTTP client with updated token."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token.

        Raises:
            GimsAuthError: If refresh token is expired or invalid.
            GimsApiError: If token refresh fails for other reasons.
        """
        refresh_url = f"{self.config.url}/security/token/refresh/"

        async with httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        ) as client:
            try:
                response = await client.post(
                    refresh_url,
                    json={"refresh": self._refresh_token},
                    headers={"Content-Type": "application/json"},
                )
            except httpx.RequestError as e:
                raise GimsApiError(
                    0,
                    "Ошибка аутентификации: не удалось обновить токен доступа",
                    f"Ошибка сети: {e}",
                )

            if response.status_code == 401:
                raise GimsAuthError(
                    401,
                    "Ошибка аутентификации: токен обновления недействителен. "
                    "Проверьте учётную запись и получите новые токены в GIMS.",
                )

            if response.status_code != 200:
                try:
                    data = response.json()
                    detail = data.get("detail", str(data))
                except Exception:
                    detail = response.text
                raise GimsApiError(
                    response.status_code,
                    "Ошибка аутентификации: не удалось обновить токен доступа",
                    detail,
                )

            try:
                data = response.json()
                self._access_token = data["access"]
                # refresh token is optional (only returned if ROTATE_REFRESH_TOKENS is True)
                if "refresh" in data:
                    self._refresh_token = data["refresh"]
            except (KeyError, ValueError) as e:
                raise GimsApiError(
                    response.status_code,
                    "Ошибка аутентификации: не удалось обновить токен доступа",
                    f"Неверный формат ответа: {e}",
                )

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response, raising errors if needed.

        Note: 401 errors should be handled by the request wrapper, not here.
        Filters non-JSON responses to prevent garbage in LLM context.
        """
        if response.status_code == 401:
            raise GimsApiError(401, "Authentication failed", "Token may be expired or invalid")
        if response.status_code == 403:
            raise GimsApiError(403, "Permission denied", "Insufficient permissions for this operation")
        if response.status_code == 404:
            raise GimsApiError(404, "Not found", "The requested resource was not found")
        if response.status_code >= 400:
            try:
                data = response.json()
                detail = data.get("detail", str(data))
            except Exception:
                detail = self._sanitize_error_response(response)
            raise GimsApiError(response.status_code, "API error", detail)

        if response.status_code == 204:
            return None

        # Validate Content-Type to prevent non-JSON garbage in LLM context
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise GimsApiError(
                response.status_code,
                "Invalid response format",
                f"Expected JSON (application/json), got '{content_type}'. "
                "Server may have returned an error page. Response body filtered.",
            )

        try:
            return response.json()
        except Exception as e:
            raise GimsApiError(
                response.status_code,
                "Failed to parse JSON response",
                f"Content-Type was '{content_type}' but body is not valid JSON: {e}",
            )

    def _sanitize_error_response(self, response: httpx.Response) -> str:
        """Sanitize error response to prevent HTML/garbage in LLM context.

        Returns a clean error message instead of raw HTML or large text.
        """
        content_type = response.headers.get("content-type", "")
        text = response.text

        # If it's HTML (error page from Nginx/Django), don't return the full content
        if "text/html" in content_type or text.strip().startswith(("<!DOCTYPE", "<html", "<HTML")):
            # Try to extract title from HTML
            import re

            title_match = re.search(r"<title[^>]*>([^<]+)</title>", text, re.IGNORECASE)
            if title_match:
                return f"Server returned HTML error page: {title_match.group(1).strip()}"
            return "Server returned HTML error page (content filtered)"

        # For other non-JSON responses, truncate if too long
        if len(text) > 500:
            return f"{text[:500]}... (truncated, {len(text)} bytes total)"

        return text

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> Any:
        """Make an HTTP request with automatic token refresh on 401.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            url: URL path (relative to base_url).
            json: JSON body for POST/PATCH requests.
            params: Query parameters.

        Returns:
            Parsed JSON response or None for 204.

        Raises:
            GimsAuthError: If authentication fails and cannot be recovered.
            GimsApiError: For other API errors.
        """
        client = await self._get_client()

        # First attempt
        response = await client.request(method, url, json=json, params=params)

        # If 401, try to refresh token and retry
        if response.status_code == 401:
            await self._refresh_access_token()
            client = await self._recreate_client()
            response = await client.request(method, url, json=json, params=params)

        return self._handle_response(response)

    # ==================== Scripts ====================

    async def list_script_folders(self) -> list[dict]:
        """Get all script folders."""
        return await self._request("GET", "/scripts/folder/")

    async def create_script_folder(self, name: str, parent_folder_id: int | None = None) -> dict:
        """Create a script folder."""
        data = {"name": name}
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        return await self._request("POST", "/scripts/folder/", json=data)

    async def update_script_folder(self, folder_id: int, name: str | None = None, parent_folder_id: int | None = None) -> dict:
        """Update a script folder."""
        data = {}
        if name is not None:
            data["name"] = name
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        return await self._request("PATCH", f"/scripts/folder/{folder_id}/", json=data)

    async def delete_script_folder(self, folder_id: int) -> None:
        """Delete a script folder."""
        return await self._request("DELETE", f"/scripts/folder/{folder_id}/")

    async def list_scripts(self, folder_id: int | None = None) -> list[dict]:
        """Get all scripts, optionally filtered by folder."""
        scripts = await self._request("GET", "/scripts/script/")
        if folder_id is not None:
            scripts = [s for s in scripts if s.get("folder_id") == folder_id]
        return scripts

    async def get_script(self, script_id: int) -> dict:
        """Get a script by ID."""
        return await self._request("GET", f"/scripts/script/{script_id}/")

    async def create_script(self, name: str, code: str = "", folder_id: int | None = None) -> dict:
        """Create a script."""
        data = {"name": name, "code": code}
        if folder_id is not None:
            data["folder_id"] = folder_id
        return await self._request("POST", "/scripts/script/", json=data)

    async def update_script(
        self, script_id: int, name: str | None = None, code: str | None = None, folder_id: int | None = None
    ) -> dict:
        """Update a script."""
        data = {}
        if name is not None:
            data["name"] = name
        if code is not None:
            data["code"] = code
        if folder_id is not None:
            data["folder_id"] = folder_id
        return await self._request("PATCH", f"/scripts/script/{script_id}/", json=data)

    async def delete_script(self, script_id: int) -> None:
        """Delete a script."""
        return await self._request("DELETE", f"/scripts/script/{script_id}/")

    async def search_scripts(self, search_code: str, case_sensitive: bool = False, exact_match: bool = False) -> list[dict]:
        """Search scripts by code."""
        params = {
            "search_code": search_code,
            "case_sensitive": "true" if case_sensitive else "false",
            "exact_match": "true" if exact_match else "false",
        }
        return await self._request("GET", "/scripts/search_code/", params=params)

    # ==================== DataSource Type Folders ====================

    async def list_datasource_type_folders(self) -> list[dict]:
        """Get all datasource type folders."""
        return await self._request("GET", "/datasource_types/folder/")

    async def create_datasource_type_folder(self, name: str, parent_folder_id: int | None = None) -> dict:
        """Create a datasource type folder."""
        data = {"name": name}
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        return await self._request("POST", "/datasource_types/folder/", json=data)

    async def update_datasource_type_folder(self, folder_id: int, name: str | None = None, parent_folder_id: int | None = None) -> dict:
        """Update a datasource type folder."""
        data = {}
        if name is not None:
            data["name"] = name
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        return await self._request("PATCH", f"/datasource_types/folder/{folder_id}/", json=data)

    async def delete_datasource_type_folder(self, folder_id: int) -> None:
        """Delete a datasource type folder."""
        return await self._request("DELETE", f"/datasource_types/folder/{folder_id}/")

    # ==================== DataSource Types ====================

    async def list_datasource_types(self) -> list[dict]:
        """Get all datasource types."""
        return await self._request("GET", "/datasource_types/ds_type/")

    async def get_datasource_type(self, type_id: int) -> dict:
        """Get a datasource type by ID."""
        return await self._request("GET", f"/datasource_types/ds_type/{type_id}/")

    async def create_datasource_type(
        self, name: str, description: str = "", version: str = "1.0", folder_id: int | None = None
    ) -> dict:
        """Create a datasource type."""
        data = {"name": name, "description": description, "version": version}
        if folder_id is not None:
            data["folder"] = folder_id
        return await self._request("POST", "/datasource_types/ds_type/", json=data)

    async def update_datasource_type(
        self,
        type_id: int,
        name: str | None = None,
        description: str | None = None,
        version: str | None = None,
        folder_id: int | None = None,
    ) -> dict:
        """Update a datasource type."""
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if version is not None:
            data["version"] = version
        if folder_id is not None:
            data["folder"] = folder_id
        return await self._request("PATCH", f"/datasource_types/ds_type/{type_id}/", json=data)

    async def delete_datasource_type(self, type_id: int) -> None:
        """Delete a datasource type."""
        return await self._request("DELETE", f"/datasource_types/ds_type/{type_id}/")

    # ==================== DataSource Type Properties ====================

    async def list_datasource_type_properties(self, mds_type_id: int) -> list[dict]:
        """Get all properties for a datasource type."""
        return await self._request("GET", "/datasource_types/properties/", params={"mds_type_id": mds_type_id})

    async def create_datasource_type_property(
        self,
        mds_type_id: int,
        name: str,
        label: str,
        value_type_id: int,
        section_name_id: int,
        description: str = "",
        default_value: str = "",
        is_required: bool = False,
        is_hidden: bool = False,
        default_dict_value_id: int | None = None,
    ) -> dict:
        """Create a datasource type property."""
        data = {
            "mds_type_id": mds_type_id,
            "name": name,
            "label": label,
            "value_type_id": value_type_id,
            "section_name_id": section_name_id,
            "description": description,
            "default_value": default_value,
            "is_required": is_required,
            "is_hidden": is_hidden,
            "default_dict_value_id": default_dict_value_id,
        }
        return await self._request("POST", "/datasource_types/properties/", json=data)

    async def update_datasource_type_property(self, property_id: int, **kwargs) -> dict:
        """Update a datasource type property."""
        return await self._request("PATCH", f"/datasource_types/properties/{property_id}/", json=kwargs)

    async def delete_datasource_type_property(self, property_id: int) -> None:
        """Delete a datasource type property."""
        return await self._request("DELETE", f"/datasource_types/properties/{property_id}/")

    # ==================== DataSource Type Methods ====================

    async def list_datasource_type_methods(self, mds_type_id: int) -> list[dict]:
        """Get all methods for a datasource type."""
        return await self._request("GET", "/datasource_types/method/", params={"mds_type_id": mds_type_id})

    async def get_datasource_type_method(self, method_id: int) -> dict:
        """Get a single datasource type method by ID."""
        return await self._request("GET", f"/datasource_types/method/{method_id}/")

    async def create_datasource_type_method(
        self, mds_type_id: int, name: str, label: str, code: str = "# Method code\npass", description: str = ""
    ) -> dict:
        """Create a datasource type method."""
        data = {
            "mds_type_id": mds_type_id,
            "name": name,
            "label": label,
            "code": code,
            "description": description,
        }
        return await self._request("POST", "/datasource_types/method/", json=data)

    async def update_datasource_type_method(self, method_id: int, **kwargs) -> dict:
        """Update a datasource type method."""
        return await self._request("PATCH", f"/datasource_types/method/{method_id}/", json=kwargs)

    async def delete_datasource_type_method(self, method_id: int) -> None:
        """Delete a datasource type method."""
        return await self._request("DELETE", f"/datasource_types/method/{method_id}/")

    # ==================== Method Parameters ====================

    async def list_method_parameters(self, method_id: int) -> list[dict]:
        """Get all parameters for a method."""
        return await self._request("GET", "/datasource_types/method_params/", params={"method_id": method_id})

    async def create_method_parameter(
        self,
        method_id: int,
        label: str,
        value_type_id: int,
        input_type: bool = True,
        default_value: str = "",
        description: str = "",
        is_hidden: bool = False,
        default_dict_value_id: int | None = None,
    ) -> dict:
        """Create a method parameter."""
        data = {
            "method_id": method_id,
            "label": label,
            "value_type_id": value_type_id,
            "input_type": input_type,
            "default_value": default_value,
            "description": description,
            "is_hidden": is_hidden,
            "default_dict_value_id": default_dict_value_id,
        }
        return await self._request("POST", "/datasource_types/method_params/", json=data)

    async def update_method_parameter(self, parameter_id: int, **kwargs) -> dict:
        """Update a method parameter."""
        return await self._request("PATCH", f"/datasource_types/method_params/{parameter_id}/", json=kwargs)

    async def delete_method_parameter(self, parameter_id: int) -> None:
        """Delete a method parameter."""
        return await self._request("DELETE", f"/datasource_types/method_params/{parameter_id}/")

    # ==================== Activator Type Folders ====================

    async def list_activator_type_folders(self) -> list[dict]:
        """Get all activator type folders."""
        return await self._request("GET", "/activator_type/folder/")

    async def create_activator_type_folder(self, name: str, parent_folder_id: int | None = None) -> dict:
        """Create an activator type folder."""
        data = {"name": name}
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        return await self._request("POST", "/activator_type/folder/", json=data)

    async def update_activator_type_folder(self, folder_id: int, name: str | None = None, parent_folder_id: int | None = None) -> dict:
        """Update an activator type folder."""
        data = {}
        if name is not None:
            data["name"] = name
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        return await self._request("PATCH", f"/activator_type/folder/{folder_id}/", json=data)

    async def delete_activator_type_folder(self, folder_id: int) -> None:
        """Delete an activator type folder."""
        return await self._request("DELETE", f"/activator_type/folder/{folder_id}/")

    # ==================== Activator Types ====================

    async def list_activator_types(self) -> list[dict]:
        """Get all activator types."""
        return await self._request("GET", "/activator_types/activator_type/")

    async def get_activator_type(self, type_id: int) -> dict:
        """Get an activator type by ID."""
        return await self._request("GET", f"/activator_types/activator_type/{type_id}/")

    async def create_activator_type(
        self,
        name: str,
        code: str = "# Print all built-in variables and functions for help\nprint_help()",
        description: str = "",
        version: str = "1.0",
        folder_id: int | None = None,
    ) -> dict:
        """Create an activator type."""
        data = {"name": name, "code": code, "description": description, "version": version}
        if folder_id is not None:
            data["folder"] = folder_id
        return await self._request("POST", "/activator_types/activator_type/", json=data)

    async def update_activator_type(self, type_id: int, **kwargs) -> dict:
        """Update an activator type."""
        return await self._request("PATCH", f"/activator_types/activator_type/{type_id}/", json=kwargs)

    async def delete_activator_type(self, type_id: int) -> None:
        """Delete an activator type."""
        return await self._request("DELETE", f"/activator_types/activator_type/{type_id}/")

    # ==================== Activator Type Properties ====================

    async def list_activator_type_properties(self, activator_type_id: int | None = None) -> list[dict]:
        """Get all activator type properties."""
        properties = await self._request("GET", "/activator_types/properties/")
        if activator_type_id is not None:
            properties = [p for p in properties if p.get("activator_type_id") == activator_type_id]
        return properties

    async def create_activator_type_property(
        self,
        activator_type_id: int,
        name: str,
        label: str,
        value_type_id: int,
        section_name_id: int,
        description: str = "",
        default_value: str = "",
        is_required: bool = False,
        is_hidden: bool = False,
        default_dict_value_id: int | None = None,
    ) -> dict:
        """Create an activator type property."""
        data = {
            "activator_type_id": activator_type_id,
            "name": name,
            "label": label,
            "value_type_id": value_type_id,
            "section_name_id": section_name_id,
            "description": description,
            "default_value": default_value,
            "is_required": is_required,
            "is_hidden": is_hidden,
            "default_dict_value_id": default_dict_value_id,
        }
        return await self._request("POST", "/activator_types/properties/", json=data)

    async def update_activator_type_property(self, property_id: int, **kwargs) -> dict:
        """Update an activator type property."""
        return await self._request("PATCH", f"/activator_types/properties/{property_id}/", json=kwargs)

    async def delete_activator_type_property(self, property_id: int) -> None:
        """Delete an activator type property."""
        return await self._request("DELETE", f"/activator_types/properties/{property_id}/")

    # ==================== References ====================

    async def list_value_types(self) -> list[dict]:
        """Get all value types."""
        return await self._request("GET", "/rest/value_types/")

    async def list_property_sections(self) -> list[dict]:
        """Get all property sections."""
        return await self._request("GET", "/rest/property_sections/")

    # ==================== Script Logs ====================

    async def get_script_log_url(self, script_id: int) -> str:
        """Get the SSE stream URL for a script's log.

        Args:
            script_id: The script ID.

        Returns:
            The full URL for the SSE log stream.

        Raises:
            GimsApiError: If script not found (404) or other API error.
        """
        result = await self._request("GET", f"/scripts/script_log_url/{script_id}/")
        # API returns {"url": ["<log_url>"]}
        urls = result.get("url", [])
        if not urls:
            raise GimsApiError(500, "Invalid response", "No log URL returned")
        return urls[0]

    async def stream_sse(
        self,
        url: str,
        timeout: float,
    ) -> AsyncIterator[str]:
        """Stream SSE events from a URL.

        Args:
            url: The SSE stream URL (can be relative or absolute).
            timeout: Total timeout in seconds.

        Yields:
            JSON content strings from SSE data events.

        Raises:
            GimsApiError: On connection or streaming errors.
        """
        # If URL is relative (starts with /), prepend GIMS base URL
        if url.startswith("/"):
            url = f"{self.config.url}{url}"

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "text/event-stream",
        }

        start_time = time.monotonic()
        # Use small read timeout to ensure periodic timeout checks
        # (logviewer sends keepalive every 10s, so 5s ensures we check twice per keepalive interval)
        read_timeout = 5.0

        async def _stream_with_client(client: httpx.AsyncClient) -> AsyncIterator[str]:
            """Inner generator that streams from given client."""
            async with client.stream("GET", url, headers=headers) as response:
                if response.status_code == 401:
                    # Try to refresh token
                    await self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"
                    raise httpx.RequestError("Token refreshed, need reconnect")

                if response.status_code != 200:
                    raise GimsApiError(
                        response.status_code,
                        "Failed to connect to log stream",
                        f"HTTP {response.status_code}",
                    )

                async for line in response.aiter_lines():
                    # Check timeout on every line (including keepalives)
                    if time.monotonic() - start_time >= timeout:
                        return  # Timeout reached
                    if line.startswith("data:"):
                        yield line[5:]  # Remove "data:" prefix

        while True:
            # Check overall timeout before each connection attempt
            if time.monotonic() - start_time >= timeout:
                return

            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(read_timeout, connect=10.0),
                    verify=self.config.verify_ssl,
                ) as client:
                    async for data in _stream_with_client(client):
                        yield data
                    # Stream ended normally (e.g., server closed connection)
                    return
            except httpx.ReadTimeout:
                # Read timeout - check if overall timeout reached, if not continue
                if time.monotonic() - start_time >= timeout:
                    return
                # Otherwise, reconnect and continue streaming
                continue
            except httpx.RequestError as e:
                # Token refresh or other error - retry if we have time
                if "Token refreshed" in str(e):
                    continue
                if time.monotonic() - start_time >= timeout:
                    return
                raise GimsApiError(0, "SSE connection error", str(e)) from e
