"""MCP Tools for Script Execution Logs."""

import asyncio
import json
import re
import time

from mcp.types import TextContent, Tool

from ..client import GimsApiError, GimsClient
from ..utils import format_error, get_max_response_size

# Regex pattern to match log line prefix: "2026-01-11 04:23:33,350 [INFO] "
LOG_LINE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[[^\]]+\] ")

# Default end markers
DEFAULT_END_MARKERS = ["END SCRIPT"]


def get_log_tools() -> list[Tool]:
    """Get the list of log tools."""
    return [
        Tool(
            name="get_script_execution_log",
            description=(
                "Get script execution log via SSE stream. "
                "Waits for end marker or timeout. "
                "Use this to collect script output after manual script execution in GIMS."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "scr_id": {
                        "type": "integer",
                        "description": "Script ID in GIMS",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (overrides GIMS_LOG_STREAM_TIMEOUT)",
                    },
                    "end_markers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "End markers to stop log collection. Default: ['END SCRIPT']",
                    },
                    "filter_pattern": {
                        "type": "string",
                        "description": "Python regex to filter log lines (applied after end marker check)",
                    },
                    "keep_timestamp": {
                        "type": "boolean",
                        "description": "Keep timestamp and log level in output (default: false)",
                    },
                },
                "required": ["scr_id"],
            },
        ),
    ]


async def handle_log_tool(
    name: str,
    arguments: dict,
    client: GimsClient,
) -> list[TextContent] | None:
    """Handle log tool calls. Returns None if tool not handled."""
    try:
        if name == "get_script_execution_log":
            return await _get_script_execution_log(client, arguments)
    except GimsApiError as e:
        return [TextContent(type="text", text=f"Error: {e.message}\nDetail: {e.detail}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {format_error(e)}")]
    return None


def _parse_log_line(line: str, keep_timestamp: bool = False) -> str:
    """Parse a log line, optionally removing timestamp and log level.

    Args:
        line: The raw log line.
        keep_timestamp: If True, return line as-is. If False, remove prefix.

    Returns:
        The parsed log line (payload only if keep_timestamp=False).
    """
    if keep_timestamp:
        return line

    match = LOG_LINE_PATTERN.match(line)
    if match:
        return line[match.end():]
    return line


def _check_end_markers(text: str, markers: list[str]) -> bool:
    """Check if text contains any of the end markers.

    Args:
        text: The text to check.
        markers: List of end markers to look for.

    Returns:
        True if any marker is found in text.
    """
    for marker in markers:
        if marker in text:
            return True
    return False


def _apply_filter(text: str, pattern: str | None) -> bool:
    """Check if text matches the filter pattern.

    Args:
        text: The text to check.
        pattern: Optional regex pattern.

    Returns:
        True if pattern is None or text matches pattern.
    """
    if pattern is None:
        return True
    try:
        compiled = re.compile(pattern)
        return compiled.search(text) is not None
    except re.error:
        # Invalid regex - treat as literal substring
        return pattern in text


async def _get_script_execution_log(
    client: GimsClient,
    arguments: dict,
) -> list[TextContent]:
    """Get script execution log via SSE stream.

    Args:
        client: The GIMS client.
        arguments: Tool arguments.

    Returns:
        List with single TextContent containing the log.
    """
    scr_id = arguments["scr_id"]
    timeout = arguments.get("timeout", client.config.log_stream_timeout)
    end_markers = arguments.get("end_markers", DEFAULT_END_MARKERS)
    filter_pattern = arguments.get("filter_pattern")
    keep_timestamp = arguments.get("keep_timestamp", False)

    # Get max response size
    max_size = get_max_response_size()

    # Get log URL
    try:
        log_url = await client.get_script_log_url(scr_id)
    except GimsApiError as e:
        if e.status_code == 404:
            return [TextContent(type="text", text=f"Error 404: Script with ID {scr_id} not found")]
        raise

    # Add tail=0 to stream only NEW entries (start from end of file).
    # tail=N means "show last N lines" - so tail=0 means "show 0 historical lines".
    # Without this parameter, logviewer defaults to tail=10 (last 10 lines).
    if "?" in log_url:
        log_url += "&tail=0"
    else:
        log_url += "?tail=0"

    # Collect log lines
    buffer: list[str] = []
    buffer_size = 0
    end_marker_found = False
    timeout_reached = False
    size_limit_reached = False
    connection_error: str | None = None

    start_time = time.monotonic()
    retry_delay = 2.0  # seconds between reconnection attempts
    max_retries = int(timeout / retry_delay) + 1  # Allow retries until timeout

    for _ in range(max_retries):
        # Check if overall timeout reached
        elapsed = time.monotonic() - start_time
        if elapsed >= timeout:
            timeout_reached = True
            break

        remaining_timeout = timeout - elapsed

        try:
            received_any_data = False
            async for data in client.stream_sse(log_url, remaining_timeout):
                received_any_data = True

                # Check timeout
                if time.monotonic() - start_time >= timeout:
                    timeout_reached = True
                    break

                # Parse SSE data - it's JSON with "content" field
                try:
                    parsed = json.loads(data)
                    content = parsed.get("content", "")
                except (json.JSONDecodeError, TypeError):
                    # Not JSON or invalid - use as-is
                    content = data

                if not content:
                    continue

                # Process each line in content
                for line in content.splitlines():
                    if not line.strip():
                        continue

                    # Check for end markers (before filtering!)
                    if _check_end_markers(line, end_markers):
                        end_marker_found = True
                        # Still add the line with end marker
                        parsed_line = _parse_log_line(line, keep_timestamp)
                        if _apply_filter(parsed_line, filter_pattern):
                            line_size = len(parsed_line.encode("utf-8")) + 1  # +1 for newline
                            if buffer_size + line_size <= max_size:
                                buffer.append(parsed_line)
                                buffer_size += line_size
                        break

                    # Parse and filter line
                    parsed_line = _parse_log_line(line, keep_timestamp)

                    # Apply filter
                    if not _apply_filter(parsed_line, filter_pattern):
                        continue

                    # Check size limit
                    line_size = len(parsed_line.encode("utf-8")) + 1  # +1 for newline
                    if buffer_size + line_size > max_size:
                        size_limit_reached = True
                        break

                    buffer.append(parsed_line)
                    buffer_size += line_size

                if end_marker_found or size_limit_reached or timeout_reached:
                    break

            # Exit retry loop if we found what we need or timed out
            if end_marker_found or size_limit_reached or timeout_reached:
                break

            # If connection closed without data and we have time left, wait and retry
            if not received_any_data:
                remaining = timeout - (time.monotonic() - start_time)
                if remaining > retry_delay:
                    await asyncio.sleep(retry_delay)
                    continue  # Retry connection
                else:
                    # Not enough time left for retry, wait for remaining time
                    if remaining > 0:
                        await asyncio.sleep(remaining)
                    timeout_reached = True
                    break
            else:
                # We received data but connection closed - check if we should wait for more
                if buffer:
                    # We have some data, connection just closed normally
                    break
                # No useful data received, retry
                remaining = timeout - (time.monotonic() - start_time)
                if remaining > retry_delay:
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    timeout_reached = True
                    break

        except GimsApiError as e:
            connection_error = f"SSE connection error: {e.message}"
            # On connection error, wait and retry
            remaining = timeout - (time.monotonic() - start_time)
            if remaining > retry_delay:
                await asyncio.sleep(retry_delay)
                connection_error = None  # Clear error if we're retrying
                continue
            break
        except asyncio.TimeoutError:
            timeout_reached = True
            break
        except Exception as e:
            connection_error = f"Unexpected error: {format_error(e)}"
            break

    # Build result
    result_lines = buffer

    # Add warnings if needed
    warnings: list[str] = []
    if timeout_reached and not end_marker_found:
        warnings.append(f"WARNING: Timeout ({timeout}s) reached without end marker")
    if size_limit_reached:
        warnings.append(f"WARNING: Size limit ({max_size // 1024}KB) reached")
    if connection_error:
        warnings.append(f"WARNING: {connection_error}")

    # Combine result
    log_content = "\n".join(result_lines)
    if warnings:
        log_content = "\n".join(warnings) + "\n\n" + log_content

    return [TextContent(type="text", text=log_content if log_content else "No log data received")]
