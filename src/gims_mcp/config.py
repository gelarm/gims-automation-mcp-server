"""Configuration management for GIMS MCP Server."""

import os
from dataclasses import dataclass


def _parse_bool_env(value: str | None, default: bool = True) -> bool:
    """Parse boolean from environment variable.

    Accepts: 'false', '0', 'no', 'off' as False (case-insensitive).
    Everything else (including empty/None) returns default.
    """
    if value is None:
        return default
    return value.lower() not in ("false", "0", "no", "off")


# Default response size limit in KB
DEFAULT_MAX_RESPONSE_SIZE_KB = 10


@dataclass
class Config:
    """Server configuration."""

    url: str
    access_token: str
    refresh_token: str
    timeout: float = 30.0
    verify_ssl: bool = True
    max_response_size_kb: int = DEFAULT_MAX_RESPONSE_SIZE_KB

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        url = os.environ.get("GIMS_URL", "")
        access_token = os.environ.get("GIMS_ACCESS_TOKEN", "")
        refresh_token = os.environ.get("GIMS_REFRESH_TOKEN", "")
        verify_ssl = _parse_bool_env(os.environ.get("GIMS_VERIFY_SSL"), default=True)
        max_response_size_kb = int(os.environ.get("GIMS_MAX_RESPONSE_SIZE_KB", DEFAULT_MAX_RESPONSE_SIZE_KB))

        if not url:
            raise ValueError("GIMS_URL environment variable is required")
        if not access_token:
            raise ValueError("GIMS_ACCESS_TOKEN environment variable is required")
        if not refresh_token:
            raise ValueError("GIMS_REFRESH_TOKEN environment variable is required")

        return cls(
            url=url.rstrip("/"),
            access_token=access_token,
            refresh_token=refresh_token,
            verify_ssl=verify_ssl,
            max_response_size_kb=max_response_size_kb,
        )

    @classmethod
    def from_args(
        cls,
        url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        verify_ssl: bool | None = None,
        max_response_size_kb: int | None = None,
    ) -> "Config":
        """Create config from CLI arguments, falling back to environment variables."""
        final_url = url or os.environ.get("GIMS_URL", "")
        final_access_token = access_token or os.environ.get("GIMS_ACCESS_TOKEN", "")
        final_refresh_token = refresh_token or os.environ.get("GIMS_REFRESH_TOKEN", "")

        # verify_ssl: CLI argument takes precedence, then env var, then default True
        if verify_ssl is not None:
            final_verify_ssl = verify_ssl
        else:
            final_verify_ssl = _parse_bool_env(os.environ.get("GIMS_VERIFY_SSL"), default=True)

        # max_response_size_kb: CLI argument takes precedence, then env var, then default
        if max_response_size_kb is not None:
            final_max_response_size_kb = max_response_size_kb
        else:
            final_max_response_size_kb = int(
                os.environ.get("GIMS_MAX_RESPONSE_SIZE_KB", DEFAULT_MAX_RESPONSE_SIZE_KB)
            )

        if not final_url:
            raise ValueError("GIMS URL is required (--url or GIMS_URL env)")
        if not final_access_token:
            raise ValueError("GIMS access token is required (--access-token or GIMS_ACCESS_TOKEN env)")
        if not final_refresh_token:
            raise ValueError("GIMS refresh token is required (--refresh-token or GIMS_REFRESH_TOKEN env)")

        return cls(
            url=final_url.rstrip("/"),
            access_token=final_access_token,
            refresh_token=final_refresh_token,
            verify_ssl=final_verify_ssl,
            max_response_size_kb=final_max_response_size_kb,
        )
