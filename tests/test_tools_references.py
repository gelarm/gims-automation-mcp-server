"""Tests for reference tools."""

import json
import pytest
import respx
from httpx import Response

from gims_mcp.tools.references import get_reference_tools, handle_reference_tool


class TestGetReferenceTools:
    """Tests for get_reference_tools function."""

    def test_returns_list_of_tools(self):
        """Test that get_reference_tools returns a list."""
        tools = get_reference_tools()
        assert isinstance(tools, list)
        assert len(tools) == 2

    def test_all_tools_have_required_fields(self):
        """Test that all tools have name, description, and inputSchema."""
        tools = get_reference_tools()
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_tool_names(self):
        """Test that all expected tools are present."""
        tools = get_reference_tools()
        names = {tool.name for tool in tools}
        expected = {"list_value_types", "list_property_sections"}
        assert names == expected


class TestHandleReferenceTool:
    """Tests for handle_reference_tool function."""

    @pytest.mark.asyncio
    async def test_list_value_types(self, client, mock_api, sample_value_types):
        """Test list_value_types tool."""
        mock_api.get("/rest/value_types/").mock(return_value=Response(200, json=sample_value_types))

        result = await handle_reference_tool("list_value_types", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "value_types" in data
        assert len(data["value_types"]) == 3
        await client.close()

    @pytest.mark.asyncio
    async def test_list_property_sections(self, client, mock_api, sample_property_sections):
        """Test list_property_sections tool."""
        mock_api.get("/rest/property_sections/").mock(
            return_value=Response(200, json=sample_property_sections)
        )

        result = await handle_reference_tool("list_property_sections", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "property_sections" in data
        assert len(data["property_sections"]) == 3
        await client.close()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_none(self, client):
        """Test that unknown tool returns None."""
        result = await handle_reference_tool("unknown_tool", {}, client)
        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_error_handling(self, client, mock_api):
        """Test error handling in tools."""
        mock_api.get("/rest/value_types/").mock(
            return_value=Response(500, json={"detail": "Internal error"})
        )

        result = await handle_reference_tool("list_value_types", {}, client)

        assert result is not None
        assert "Error" in result[0].text
        await client.close()
