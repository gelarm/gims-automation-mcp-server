"""Entry point for GIMS MCP Server."""

import argparse
import asyncio
import logging
import sys

from .config import Config
from .server import run_server


def _parse_verify_ssl(value: str) -> bool:
    """Parse --verify-ssl argument value."""
    if value.lower() in ("false", "0", "no", "off"):
        return False
    if value.lower() in ("true", "1", "yes", "on"):
        return True
    raise argparse.ArgumentTypeError(
        f"Invalid value '{value}'. Use 'true', 'false', '1', '0', 'yes', 'no', 'on', or 'off'."
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="GIMS Automation MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
  GIMS_URL            URL of the GIMS server (e.g., https://gims.example.com)
  GIMS_ACCESS_TOKEN   JWT access token for authentication
  GIMS_REFRESH_TOKEN  JWT refresh token for automatic token renewal
  GIMS_VERIFY_SSL     SSL certificate verification (true/false, default: true)

Examples:
  gims-mcp-server --url https://gims.example.com --access-token eyJ... --refresh-token eyJ...
  gims-mcp-server --url https://gims.example.com --access-token eyJ... --refresh-token eyJ... --verify-ssl false
  GIMS_URL=https://gims.example.com GIMS_ACCESS_TOKEN=eyJ... GIMS_REFRESH_TOKEN=eyJ... gims-mcp-server
        """,
    )
    parser.add_argument(
        "--url",
        help="GIMS server URL (or set GIMS_URL env var)",
    )
    parser.add_argument(
        "--access-token",
        help="JWT access token (or set GIMS_ACCESS_TOKEN env var)",
    )
    parser.add_argument(
        "--refresh-token",
        help="JWT refresh token for automatic renewal (or set GIMS_REFRESH_TOKEN env var)",
    )
    parser.add_argument(
        "--verify-ssl",
        type=_parse_verify_ssl,
        metavar="BOOL",
        help="Verify SSL certificates (true/false, default: true). Use 'false' for self-signed certificates.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    try:
        config = Config.from_args(
            url=args.url,
            access_token=args.access_token,
            refresh_token=args.refresh_token,
            verify_ssl=args.verify_ssl,
        )
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Run the server
    asyncio.run(run_server(config))


if __name__ == "__main__":
    main()
