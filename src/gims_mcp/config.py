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


@dataclass
class Config:
    """Server configuration."""

    url: str
    token: str
    timeout: float = 30.0
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        url = os.environ.get("GIMS_URL", "")
        token = os.environ.get("GIMS_TOKEN", "")
        verify_ssl = _parse_bool_env(os.environ.get("GIMS_VERIFY_SSL"), default=True)

        if not url:
            raise ValueError("GIMS_URL environment variable is required")
        if not token:
            raise ValueError("GIMS_TOKEN environment variable is required")

        return cls(url=url.rstrip("/"), token=token, verify_ssl=verify_ssl)

    @classmethod
    def from_args(
        cls,
        url: str | None = None,
        token: str | None = None,
        verify_ssl: bool | None = None,
    ) -> "Config":
        """Create config from CLI arguments, falling back to environment variables."""
        final_url = url or os.environ.get("GIMS_URL", "")
        final_token = token or os.environ.get("GIMS_TOKEN", "")

        # verify_ssl: CLI argument takes precedence, then env var, then default True
        if verify_ssl is not None:
            final_verify_ssl = verify_ssl
        else:
            final_verify_ssl = _parse_bool_env(os.environ.get("GIMS_VERIFY_SSL"), default=True)

        if not final_url:
            raise ValueError("GIMS URL is required (--url or GIMS_URL env)")
        if not final_token:
            raise ValueError("GIMS token is required (--token or GIMS_TOKEN env)")

        return cls(url=final_url.rstrip("/"), token=final_token, verify_ssl=final_verify_ssl)
