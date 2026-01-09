"""HTTP client for GIMS Automation API."""

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


class GimsClient:
    """Async HTTP client for GIMS Automation API."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"{config.url}/automation"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.config.token}",
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

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response, raising errors if needed."""
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
                detail = response.text
            raise GimsApiError(response.status_code, f"API error", detail)

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except Exception:
            return response.text

    # ==================== Scripts ====================

    async def list_script_folders(self) -> list[dict]:
        """Get all script folders."""
        client = await self._get_client()
        response = await client.get("/scripts/folder/")
        return self._handle_response(response)

    async def create_script_folder(self, name: str, parent_folder_id: int | None = None) -> dict:
        """Create a script folder."""
        client = await self._get_client()
        data = {"name": name}
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        response = await client.post("/scripts/folder/", json=data)
        return self._handle_response(response)

    async def update_script_folder(self, folder_id: int, name: str | None = None, parent_folder_id: int | None = None) -> dict:
        """Update a script folder."""
        client = await self._get_client()
        data = {}
        if name is not None:
            data["name"] = name
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        response = await client.patch(f"/scripts/folder/{folder_id}/", json=data)
        return self._handle_response(response)

    async def delete_script_folder(self, folder_id: int) -> None:
        """Delete a script folder."""
        client = await self._get_client()
        response = await client.delete(f"/scripts/folder/{folder_id}/")
        return self._handle_response(response)

    async def list_scripts(self, folder_id: int | None = None) -> list[dict]:
        """Get all scripts, optionally filtered by folder."""
        client = await self._get_client()
        response = await client.get("/scripts/script/")
        scripts = self._handle_response(response)
        if folder_id is not None:
            scripts = [s for s in scripts if s.get("folder_id") == folder_id]
        return scripts

    async def get_script(self, script_id: int) -> dict:
        """Get a script by ID."""
        client = await self._get_client()
        response = await client.get(f"/scripts/script/{script_id}/")
        return self._handle_response(response)

    async def create_script(self, name: str, code: str = "", folder_id: int | None = None) -> dict:
        """Create a script."""
        client = await self._get_client()
        data = {"name": name, "code": code}
        if folder_id is not None:
            data["folder_id"] = folder_id
        response = await client.post("/scripts/script/", json=data)
        return self._handle_response(response)

    async def update_script(
        self, script_id: int, name: str | None = None, code: str | None = None, folder_id: int | None = None
    ) -> dict:
        """Update a script."""
        client = await self._get_client()
        data = {}
        if name is not None:
            data["name"] = name
        if code is not None:
            data["code"] = code
        if folder_id is not None:
            data["folder_id"] = folder_id
        response = await client.patch(f"/scripts/script/{script_id}/", json=data)
        return self._handle_response(response)

    async def delete_script(self, script_id: int) -> None:
        """Delete a script."""
        client = await self._get_client()
        response = await client.delete(f"/scripts/script/{script_id}/")
        return self._handle_response(response)

    async def search_scripts(self, search_code: str, case_sensitive: bool = False, exact_match: bool = False) -> list[dict]:
        """Search scripts by code."""
        client = await self._get_client()
        params = {
            "search_code": search_code,
            "case_sensitive": "true" if case_sensitive else "false",
            "exact_match": "true" if exact_match else "false",
        }
        response = await client.get("/scripts/search_code/", params=params)
        return self._handle_response(response)

    # ==================== DataSource Type Folders ====================

    async def list_datasource_type_folders(self) -> list[dict]:
        """Get all datasource type folders."""
        client = await self._get_client()
        response = await client.get("/datasource_types/folder/")
        return self._handle_response(response)

    async def create_datasource_type_folder(self, name: str, parent_folder_id: int | None = None) -> dict:
        """Create a datasource type folder."""
        client = await self._get_client()
        data = {"name": name}
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        response = await client.post("/datasource_types/folder/", json=data)
        return self._handle_response(response)

    async def update_datasource_type_folder(self, folder_id: int, name: str | None = None, parent_folder_id: int | None = None) -> dict:
        """Update a datasource type folder."""
        client = await self._get_client()
        data = {}
        if name is not None:
            data["name"] = name
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        response = await client.patch(f"/datasource_types/folder/{folder_id}/", json=data)
        return self._handle_response(response)

    async def delete_datasource_type_folder(self, folder_id: int) -> None:
        """Delete a datasource type folder."""
        client = await self._get_client()
        response = await client.delete(f"/datasource_types/folder/{folder_id}/")
        return self._handle_response(response)

    # ==================== DataSource Types ====================

    async def list_datasource_types(self) -> list[dict]:
        """Get all datasource types."""
        client = await self._get_client()
        response = await client.get("/datasource_types/ds_type/")
        return self._handle_response(response)

    async def get_datasource_type(self, type_id: int) -> dict:
        """Get a datasource type by ID."""
        client = await self._get_client()
        response = await client.get(f"/datasource_types/ds_type/{type_id}/")
        return self._handle_response(response)

    async def create_datasource_type(
        self, name: str, description: str = "", version: str = "1.0", folder_id: int | None = None
    ) -> dict:
        """Create a datasource type."""
        client = await self._get_client()
        data = {"name": name, "description": description, "version": version}
        if folder_id is not None:
            data["folder"] = folder_id
        response = await client.post("/datasource_types/ds_type/", json=data)
        return self._handle_response(response)

    async def update_datasource_type(
        self,
        type_id: int,
        name: str | None = None,
        description: str | None = None,
        version: str | None = None,
        folder_id: int | None = None,
    ) -> dict:
        """Update a datasource type."""
        client = await self._get_client()
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if version is not None:
            data["version"] = version
        if folder_id is not None:
            data["folder"] = folder_id
        response = await client.patch(f"/datasource_types/ds_type/{type_id}/", json=data)
        return self._handle_response(response)

    async def delete_datasource_type(self, type_id: int) -> None:
        """Delete a datasource type."""
        client = await self._get_client()
        response = await client.delete(f"/datasource_types/ds_type/{type_id}/")
        return self._handle_response(response)

    # ==================== DataSource Type Properties ====================

    async def list_datasource_type_properties(self, mds_type_id: int) -> list[dict]:
        """Get all properties for a datasource type."""
        client = await self._get_client()
        response = await client.get("/datasource_types/properties/", params={"mds_type_id": mds_type_id})
        return self._handle_response(response)

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
    ) -> dict:
        """Create a datasource type property."""
        client = await self._get_client()
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
        }
        response = await client.post("/datasource_types/properties/", json=data)
        return self._handle_response(response)

    async def update_datasource_type_property(self, property_id: int, **kwargs) -> dict:
        """Update a datasource type property."""
        client = await self._get_client()
        response = await client.patch(f"/datasource_types/properties/{property_id}/", json=kwargs)
        return self._handle_response(response)

    async def delete_datasource_type_property(self, property_id: int) -> None:
        """Delete a datasource type property."""
        client = await self._get_client()
        response = await client.delete(f"/datasource_types/properties/{property_id}/")
        return self._handle_response(response)

    # ==================== DataSource Type Methods ====================

    async def list_datasource_type_methods(self, mds_type_id: int) -> list[dict]:
        """Get all methods for a datasource type."""
        client = await self._get_client()
        response = await client.get("/datasource_types/method/", params={"mds_type_id": mds_type_id})
        return self._handle_response(response)

    async def get_datasource_type_method(self, method_id: int) -> dict:
        """Get a single datasource type method by ID."""
        client = await self._get_client()
        response = await client.get(f"/datasource_types/method/{method_id}/")
        return self._handle_response(response)

    async def create_datasource_type_method(
        self, mds_type_id: int, name: str, label: str, code: str = "# Method code\npass", description: str = ""
    ) -> dict:
        """Create a datasource type method."""
        client = await self._get_client()
        data = {
            "mds_type_id": mds_type_id,
            "name": name,
            "label": label,
            "code": code,
            "description": description,
        }
        response = await client.post("/datasource_types/method/", json=data)
        return self._handle_response(response)

    async def update_datasource_type_method(self, method_id: int, **kwargs) -> dict:
        """Update a datasource type method."""
        client = await self._get_client()
        response = await client.patch(f"/datasource_types/method/{method_id}/", json=kwargs)
        return self._handle_response(response)

    async def delete_datasource_type_method(self, method_id: int) -> None:
        """Delete a datasource type method."""
        client = await self._get_client()
        response = await client.delete(f"/datasource_types/method/{method_id}/")
        return self._handle_response(response)

    # ==================== Method Parameters ====================

    async def list_method_parameters(self, method_id: int) -> list[dict]:
        """Get all parameters for a method."""
        client = await self._get_client()
        response = await client.get("/datasource_types/method_params/", params={"method_id": method_id})
        return self._handle_response(response)

    async def create_method_parameter(
        self,
        method_id: int,
        label: str,
        value_type_id: int,
        input_type: bool = True,
        default_value: str = "",
        description: str = "",
        is_hidden: bool = False,
    ) -> dict:
        """Create a method parameter."""
        client = await self._get_client()
        data = {
            "method_id": method_id,
            "label": label,
            "value_type_id": value_type_id,
            "input_type": input_type,
            "default_value": default_value,
            "description": description,
            "is_hidden": is_hidden,
        }
        response = await client.post("/datasource_types/method_params/", json=data)
        return self._handle_response(response)

    async def update_method_parameter(self, parameter_id: int, **kwargs) -> dict:
        """Update a method parameter."""
        client = await self._get_client()
        response = await client.patch(f"/datasource_types/method_params/{parameter_id}/", json=kwargs)
        return self._handle_response(response)

    async def delete_method_parameter(self, parameter_id: int) -> None:
        """Delete a method parameter."""
        client = await self._get_client()
        response = await client.delete(f"/datasource_types/method_params/{parameter_id}/")
        return self._handle_response(response)

    # ==================== Activator Type Folders ====================

    async def list_activator_type_folders(self) -> list[dict]:
        """Get all activator type folders."""
        client = await self._get_client()
        response = await client.get("/activator_type/folder/")
        return self._handle_response(response)

    async def create_activator_type_folder(self, name: str, parent_folder_id: int | None = None) -> dict:
        """Create an activator type folder."""
        client = await self._get_client()
        data = {"name": name}
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        response = await client.post("/activator_type/folder/", json=data)
        return self._handle_response(response)

    async def update_activator_type_folder(self, folder_id: int, name: str | None = None, parent_folder_id: int | None = None) -> dict:
        """Update an activator type folder."""
        client = await self._get_client()
        data = {}
        if name is not None:
            data["name"] = name
        if parent_folder_id is not None:
            data["parent_folder_id"] = parent_folder_id
        response = await client.patch(f"/activator_type/folder/{folder_id}/", json=data)
        return self._handle_response(response)

    async def delete_activator_type_folder(self, folder_id: int) -> None:
        """Delete an activator type folder."""
        client = await self._get_client()
        response = await client.delete(f"/activator_type/folder/{folder_id}/")
        return self._handle_response(response)

    # ==================== Activator Types ====================

    async def list_activator_types(self) -> list[dict]:
        """Get all activator types."""
        client = await self._get_client()
        response = await client.get("/activator_types/activator_type/")
        return self._handle_response(response)

    async def get_activator_type(self, type_id: int) -> dict:
        """Get an activator type by ID."""
        client = await self._get_client()
        response = await client.get(f"/activator_types/activator_type/{type_id}/")
        return self._handle_response(response)

    async def create_activator_type(
        self,
        name: str,
        code: str = "# Print all built-in variables and functions for help\nprint_help()",
        description: str = "",
        version: str = "1.0",
        folder_id: int | None = None,
    ) -> dict:
        """Create an activator type."""
        client = await self._get_client()
        data = {"name": name, "code": code, "description": description, "version": version}
        if folder_id is not None:
            data["folder"] = folder_id
        response = await client.post("/activator_types/activator_type/", json=data)
        return self._handle_response(response)

    async def update_activator_type(self, type_id: int, **kwargs) -> dict:
        """Update an activator type."""
        client = await self._get_client()
        response = await client.patch(f"/activator_types/activator_type/{type_id}/", json=kwargs)
        return self._handle_response(response)

    async def delete_activator_type(self, type_id: int) -> None:
        """Delete an activator type."""
        client = await self._get_client()
        response = await client.delete(f"/activator_types/activator_type/{type_id}/")
        return self._handle_response(response)

    # ==================== Activator Type Properties ====================

    async def list_activator_type_properties(self, activator_type_id: int | None = None) -> list[dict]:
        """Get all activator type properties."""
        client = await self._get_client()
        response = await client.get("/activator_types/properties/")
        properties = self._handle_response(response)
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
    ) -> dict:
        """Create an activator type property."""
        client = await self._get_client()
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
        }
        response = await client.post("/activator_types/properties/", json=data)
        return self._handle_response(response)

    async def update_activator_type_property(self, property_id: int, **kwargs) -> dict:
        """Update an activator type property."""
        client = await self._get_client()
        response = await client.patch(f"/activator_types/properties/{property_id}/", json=kwargs)
        return self._handle_response(response)

    async def delete_activator_type_property(self, property_id: int) -> None:
        """Delete an activator type property."""
        client = await self._get_client()
        response = await client.delete(f"/activator_types/properties/{property_id}/")
        return self._handle_response(response)

    # ==================== References ====================

    async def list_value_types(self) -> list[dict]:
        """Get all value types."""
        client = await self._get_client()
        response = await client.get("/rest/value_types/")
        return self._handle_response(response)

    async def list_property_sections(self) -> list[dict]:
        """Get all property sections."""
        client = await self._get_client()
        response = await client.get("/rest/property_sections/")
        return self._handle_response(response)
