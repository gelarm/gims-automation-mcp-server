"""Tests for log tools."""

import pytest

from gims_mcp.tools.logs import (
    _apply_filter,
    _check_end_markers,
    _parse_log_line,
    get_log_tools,
    handle_log_tool,
)


class TestGetLogTools:
    """Tests for get_log_tools function."""

    def test_returns_list_of_tools(self):
        """Test that get_log_tools returns a list."""
        tools = get_log_tools()
        assert isinstance(tools, list)
        assert len(tools) == 1

    def test_all_tools_have_required_fields(self):
        """Test that all tools have name, description, and inputSchema."""
        tools = get_log_tools()
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_tool_names(self):
        """Test that all expected tools are present."""
        tools = get_log_tools()
        names = {tool.name for tool in tools}
        expected = {"get_script_execution_log"}
        assert names == expected

    def test_get_script_execution_log_schema(self):
        """Test that get_script_execution_log has correct schema."""
        tools = get_log_tools()
        tool = tools[0]
        assert tool.name == "get_script_execution_log"
        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "scr_id" in schema["properties"]
        assert "timeout" in schema["properties"]
        assert "end_markers" in schema["properties"]
        assert "filter_pattern" in schema["properties"]
        assert "keep_timestamp" in schema["properties"]
        assert schema["required"] == ["scr_id"]


class TestParseLogLine:
    """Tests for _parse_log_line function."""

    def test_parse_log_line_removes_prefix(self):
        """Test that prefix is removed when keep_timestamp=False."""
        line = "2026-01-11 04:23:33,350 [INFO] Hello world"
        result = _parse_log_line(line, keep_timestamp=False)
        assert result == "Hello world"

    def test_parse_log_line_keeps_prefix(self):
        """Test that prefix is kept when keep_timestamp=True."""
        line = "2026-01-11 04:23:33,350 [INFO] Hello world"
        result = _parse_log_line(line, keep_timestamp=True)
        assert result == line

    def test_parse_log_line_different_levels(self):
        """Test parsing with different log levels."""
        test_cases = [
            ("2026-01-11 04:23:33,350 [DEBUG] Debug message", "Debug message"),
            ("2026-01-11 04:23:33,350 [WARNING] Warning message", "Warning message"),
            ("2026-01-11 04:23:33,350 [ERROR] Error message", "Error message"),
            ("2026-01-11 04:23:33,350 [CRITICAL] Critical message", "Critical message"),
        ]
        for line, expected in test_cases:
            result = _parse_log_line(line, keep_timestamp=False)
            assert result == expected

    def test_parse_log_line_no_prefix(self):
        """Test that lines without prefix are returned as-is."""
        line = "Plain text without prefix"
        result = _parse_log_line(line, keep_timestamp=False)
        assert result == line

    def test_parse_log_line_partial_prefix(self):
        """Test that lines with partial prefix are returned as-is."""
        line = "2026-01-11 04:23:33 Without milliseconds"
        result = _parse_log_line(line, keep_timestamp=False)
        assert result == line


class TestCheckEndMarkers:
    """Tests for _check_end_markers function."""

    def test_marker_found(self):
        """Test that returns True when marker is found."""
        assert _check_end_markers("Script completed END SCRIPT", ["END SCRIPT"])

    def test_marker_not_found(self):
        """Test that returns False when marker is not found."""
        assert not _check_end_markers("Script running", ["END SCRIPT"])

    def test_multiple_markers(self):
        """Test with multiple markers."""
        markers = ["END SCRIPT", "SCRIPT ERROR", "Timed out"]
        assert _check_end_markers("Operation failed: SCRIPT ERROR", markers)
        assert _check_end_markers("Connection Timed out", markers)
        assert not _check_end_markers("Script running", markers)

    def test_empty_markers(self):
        """Test with empty markers list."""
        assert not _check_end_markers("Any text", [])

    def test_marker_case_sensitive(self):
        """Test that marker check is case sensitive."""
        assert not _check_end_markers("end script", ["END SCRIPT"])


class TestApplyFilter:
    """Tests for _apply_filter function."""

    def test_filter_none(self):
        """Test that None filter matches everything."""
        assert _apply_filter("Any text", None)

    def test_filter_match(self):
        """Test that matching filter returns True."""
        assert _apply_filter("Error: connection failed", "Error")
        assert _apply_filter("Error: connection failed", "connection")

    def test_filter_no_match(self):
        """Test that non-matching filter returns False."""
        assert not _apply_filter("Success", "Error")

    def test_filter_regex(self):
        """Test that regex patterns work."""
        assert _apply_filter("Error code: 404", r"Error code: \d+")
        assert not _apply_filter("Error code: abc", r"Error code: \d+")

    def test_filter_case_sensitive(self):
        """Test that filter is case sensitive by default."""
        assert not _apply_filter("error", "Error")

    def test_filter_invalid_regex(self):
        """Test that invalid regex is treated as literal."""
        # Invalid regex with unmatched bracket
        assert _apply_filter("test [invalid", "[invalid")
        assert not _apply_filter("test valid", "[invalid")


class TestHandleLogTool:
    """Tests for handle_log_tool function."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_none(self, client):
        """Test that unknown tool returns None."""
        result = await handle_log_tool("unknown_tool", {}, client)
        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_get_script_execution_log_not_found(self, client, mock_api):
        """Test get_script_execution_log with non-existent script."""
        mock_api.get("/scripts/script_log_url/999/").mock(
            return_value=pytest.importorskip("httpx").Response(404, json={"detail": "Not found"})
        )

        result = await handle_log_tool("get_script_execution_log", {"scr_id": 999}, client)

        assert result is not None
        assert "404" in result[0].text
        assert "not found" in result[0].text.lower()
        await client.close()
