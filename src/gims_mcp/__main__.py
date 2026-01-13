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
  GIMS_URL                   URL of the GIMS server (e.g., https://gims.example.com)
  GIMS_ACCESS_TOKEN          JWT access token for authentication
  GIMS_REFRESH_TOKEN         JWT refresh token for automatic token renewal
  GIMS_VERIFY_SSL            SSL certificate verification (true/false, default: true)
  GIMS_MAX_RESPONSE_SIZE_KB  Maximum response size in KB (default: 10)
  GIMS_LOG_STREAM_TIMEOUT    Log stream timeout in seconds (default: 60)

Examples:
  gims-mcp-server --url https://gims.example.com --access-token eyJ... --refresh-token eyJ...
  gims-mcp-server --url https://gims.example.com --access-token eyJ... --refresh-token eyJ... --verify-ssl false
  gims-mcp-server --max-response-size 20  # Increase limit to 20KB (~5000 tokens)
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
        "--max-response-size",
        type=int,
        metavar="KB",
        help="Maximum response size in kilobytes (default: 10). "
             "Approximate token conversion: 1KB ~ 250 tokens (ASCII) or 170 tokens (Cyrillic). "
             "Example: 10KB ~ 2500 tokens, 20KB ~ 5000 tokens.",
    )
    parser.add_argument(
        "--log-stream-timeout",
        type=int,
        metavar="SECONDS",
        help="Log stream timeout in seconds (default: 60). "
             "Maximum time to wait for script execution log via SSE.",
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
            max_response_size_kb=args.max_response_size,
            log_stream_timeout=args.log_stream_timeout,
        )
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Run the server
    asyncio.run(run_server(config))


if __name__ == "__main__":
    main()
