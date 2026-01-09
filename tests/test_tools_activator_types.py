"""Tests for activator type tools."""

import json
import pytest
import respx
from httpx import Response

from gims_mcp.tools.activator_types import get_activator_type_tools, handle_activator_type_tool


class TestGetActivatorTypeTools:
    """Tests for get_activator_type_tools function."""

    def test_returns_list_of_tools(self):
        """Test that get_activator_type_tools returns a list."""
        tools = get_activator_type_tools()
        assert isinstance(tools, list)
        assert len(tools) == 14

    def test_all_tools_have_required_fields(self):
        """Test that all tools have name, description, and inputSchema."""
        tools = get_activator_type_tools()
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_tool_names(self):
        """Test that all expected tools are present."""
        tools = get_activator_type_tools()
        names = {tool.name for tool in tools}
        expected = {
            "list_activator_type_folders",
            "create_activator_type_folder",
            "update_activator_type_folder",
            "delete_activator_type_folder",
            "list_activator_types",
            "get_activator_type",
            "create_activator_type",
            "update_activator_type",
            "delete_activator_type",
            "list_activator_type_properties",
            "create_activator_type_property",
            "update_activator_type_property",
            "delete_activator_type_property",
            "search_activator_types",
        }
        assert names == expected


class TestHandleActivatorTypeTool:
    """Tests for handle_activator_type_tool function."""

    @pytest.mark.asyncio
    async def test_list_activator_type_folders(self, client, mock_api, sample_folders):
        """Test list_activator_type_folders tool."""
        mock_api.get("/activator_type/folder/").mock(return_value=Response(200, json=sample_folders))

        result = await handle_activator_type_tool("list_activator_type_folders", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "folders" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_create_activator_type_folder(self, client, mock_api):
        """Test create_activator_type_folder tool."""
        new_folder = {"id": 4, "name": "new_folder", "parent_folder_id": None}
        mock_api.post("/activator_type/folder/").mock(return_value=Response(201, json=new_folder))

        result = await handle_activator_type_tool(
            "create_activator_type_folder", {"name": "new_folder"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "new_folder"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_activator_type_folder(self, client, mock_api):
        """Test delete_activator_type_folder tool."""
        mock_api.delete("/activator_type/folder/1/").mock(return_value=Response(204))

        result = await handle_activator_type_tool(
            "delete_activator_type_folder", {"folder_id": 1}, client
        )

        assert result is not None
        assert "deleted successfully" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_list_activator_types(self, client, mock_api, sample_folders, sample_activator_types):
        """Test list_activator_types tool."""
        mock_api.get("/activator_type/folder/").mock(return_value=Response(200, json=sample_folders))
        mock_api.get("/activator_types/activator_type/").mock(
            return_value=Response(200, json=sample_activator_types)
        )

        result = await handle_activator_type_tool("list_activator_types", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "types" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_get_activator_type(self, client, mock_api, sample_activator_types):
        """Test get_activator_type tool."""
        act_type = sample_activator_types[0]
        properties = [{"id": 1, "name": "interval", "label": "interval", "activator_type_id": 1}]

        mock_api.get("/activator_types/activator_type/1/").mock(return_value=Response(200, json=act_type))
        mock_api.get("/activator_types/properties/").mock(return_value=Response(200, json=properties))

        result = await handle_activator_type_tool("get_activator_type", {"type_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "type" in data
        assert "properties" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_create_activator_type(self, client, mock_api):
        """Test create_activator_type tool."""
        new_type = {"id": 3, "name": "NewActivator", "code": "pass", "version": "1.0"}
        mock_api.post("/activator_types/activator_type/").mock(return_value=Response(201, json=new_type))

        result = await handle_activator_type_tool(
            "create_activator_type", {"name": "NewActivator"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "NewActivator"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_activator_type(self, client, mock_api):
        """Test delete_activator_type tool."""
        mock_api.delete("/activator_types/activator_type/1/").mock(return_value=Response(204))

        result = await handle_activator_type_tool("delete_activator_type", {"type_id": 1}, client)

        assert result is not None
        assert "deleted successfully" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_list_activator_type_properties(self, client, mock_api):
        """Test list_activator_type_properties tool."""
        properties = [{"id": 1, "name": "interval", "label": "interval", "activator_type_id": 1}]
        mock_api.get("/activator_types/properties/").mock(return_value=Response(200, json=properties))

        result = await handle_activator_type_tool(
            "list_activator_type_properties", {"activator_type_id": 1}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "properties" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_create_activator_type_property(self, client, mock_api):
        """Test create_activator_type_property tool."""
        new_prop = {"id": 2, "name": "cron", "label": "cron", "activator_type_id": 1}
        mock_api.post("/activator_types/properties/").mock(return_value=Response(201, json=new_prop))

        result = await handle_activator_type_tool(
            "create_activator_type_property",
            {
                "activator_type_id": 1,
                "name": "cron",
                "label": "cron",
                "value_type_id": 1,
                "section_name_id": 1,
            },
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "cron"
        await client.close()

    @pytest.mark.asyncio
    async def test_search_activator_types(self, client, mock_api, sample_activator_types):
        """Test search_activator_types tool searching by code."""
        full_types = [
            {"id": 1, "name": "ScheduleActivator", "code": "def run(): schedule()"},
            {"id": 2, "name": "TriggerActivator", "code": "def run(): trigger()"},
        ]
        mock_api.get("/activator_types/activator_type/").mock(
            return_value=Response(200, json=sample_activator_types)
        )
        mock_api.get("/activator_types/activator_type/1/").mock(
            return_value=Response(200, json=full_types[0])
        )
        mock_api.get("/activator_types/activator_type/2/").mock(
            return_value=Response(200, json=full_types[1])
        )

        result = await handle_activator_type_tool(
            "search_activator_types", {"query": "schedule", "search_in": "code"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "results" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_none(self, client):
        """Test that unknown tool returns None."""
        result = await handle_activator_type_tool("unknown_tool", {}, client)
        assert result is None
        await client.close()
