"""Tests for datasource type tools."""

import json
import pytest
import respx
from httpx import Response

from gims_mcp.tools.datasource_types import get_datasource_type_tools, handle_datasource_type_tool


class TestGetDatasourceTypeTools:
    """Tests for get_datasource_type_tools function."""

    def test_returns_list_of_tools(self):
        """Test that get_datasource_type_tools returns a list."""
        tools = get_datasource_type_tools()
        assert isinstance(tools, list)
        assert len(tools) == 22

    def test_all_tools_have_required_fields(self):
        """Test that all tools have name, description, and inputSchema."""
        tools = get_datasource_type_tools()
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_tool_names(self):
        """Test that all expected tools are present."""
        tools = get_datasource_type_tools()
        names = {tool.name for tool in tools}
        expected = {
            "list_datasource_type_folders",
            "create_datasource_type_folder",
            "update_datasource_type_folder",
            "delete_datasource_type_folder",
            "list_datasource_types",
            "get_datasource_type",
            "create_datasource_type",
            "update_datasource_type",
            "delete_datasource_type",
            "list_datasource_type_properties",
            "create_datasource_type_property",
            "update_datasource_type_property",
            "delete_datasource_type_property",
            "list_datasource_type_methods",
            "create_datasource_type_method",
            "update_datasource_type_method",
            "delete_datasource_type_method",
            "list_method_parameters",
            "create_method_parameter",
            "update_method_parameter",
            "delete_method_parameter",
            "search_datasource_type_code",
        }
        assert names == expected


class TestHandleDatasourceTypeTool:
    """Tests for handle_datasource_type_tool function."""

    @pytest.mark.asyncio
    async def test_list_datasource_type_folders(self, client, mock_api, sample_folders):
        """Test list_datasource_type_folders tool."""
        mock_api.get("/datasource_types/folder/").mock(return_value=Response(200, json=sample_folders))

        result = await handle_datasource_type_tool("list_datasource_type_folders", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "folders" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_create_datasource_type_folder(self, client, mock_api):
        """Test create_datasource_type_folder tool."""
        new_folder = {"id": 4, "name": "new_folder", "parent_folder_id": None}
        mock_api.post("/datasource_types/folder/").mock(return_value=Response(201, json=new_folder))

        result = await handle_datasource_type_tool(
            "create_datasource_type_folder", {"name": "new_folder"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "new_folder"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_datasource_type_folder(self, client, mock_api):
        """Test delete_datasource_type_folder tool."""
        mock_api.delete("/datasource_types/folder/1/").mock(return_value=Response(204))

        result = await handle_datasource_type_tool(
            "delete_datasource_type_folder", {"folder_id": 1}, client
        )

        assert result is not None
        assert "deleted successfully" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_list_datasource_types(self, client, mock_api, sample_folders, sample_datasource_types):
        """Test list_datasource_types tool."""
        mock_api.get("/datasource_types/folder/").mock(return_value=Response(200, json=sample_folders))
        mock_api.get("/datasource_types/ds_type/").mock(return_value=Response(200, json=sample_datasource_types))

        result = await handle_datasource_type_tool("list_datasource_types", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "types" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_get_datasource_type(self, client, mock_api, sample_datasource_types):
        """Test get_datasource_type tool."""
        ds_type = sample_datasource_types[0]
        properties = [{"id": 1, "name": "host", "label": "host", "mds_type_id": 1}]
        methods = [{"id": 1, "name": "connect", "label": "connect", "mds_type_id": 1}]
        params = [{"id": 1, "label": "timeout", "method_id": 1}]

        mock_api.get("/datasource_types/ds_type/1/").mock(return_value=Response(200, json=ds_type))
        mock_api.get("/datasource_types/properties/").mock(return_value=Response(200, json=properties))
        mock_api.get("/datasource_types/method/").mock(return_value=Response(200, json=methods))
        mock_api.get("/datasource_types/method_params/").mock(return_value=Response(200, json=params))

        result = await handle_datasource_type_tool("get_datasource_type", {"type_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "type" in data
        assert "properties" in data
        assert "methods" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_create_datasource_type(self, client, mock_api):
        """Test create_datasource_type tool."""
        new_type = {"id": 3, "name": "NewType", "description": "New type", "version": "1.0"}
        mock_api.post("/datasource_types/ds_type/").mock(return_value=Response(201, json=new_type))

        result = await handle_datasource_type_tool(
            "create_datasource_type", {"name": "NewType", "description": "New type"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "NewType"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_datasource_type(self, client, mock_api):
        """Test delete_datasource_type tool."""
        mock_api.delete("/datasource_types/ds_type/1/").mock(return_value=Response(204))

        result = await handle_datasource_type_tool("delete_datasource_type", {"type_id": 1}, client)

        assert result is not None
        assert "deleted successfully" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_list_datasource_type_properties(self, client, mock_api):
        """Test list_datasource_type_properties tool."""
        properties = [
            {"id": 1, "name": "host", "label": "host", "mds_type_id": 1},
            {"id": 2, "name": "port", "label": "port", "mds_type_id": 1},
        ]
        mock_api.get("/datasource_types/properties/").mock(return_value=Response(200, json=properties))

        result = await handle_datasource_type_tool(
            "list_datasource_type_properties", {"mds_type_id": 1}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "properties" in data
        assert len(data["properties"]) == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_create_datasource_type_property(self, client, mock_api):
        """Test create_datasource_type_property tool."""
        new_prop = {"id": 3, "name": "timeout", "label": "timeout", "mds_type_id": 1}
        mock_api.post("/datasource_types/properties/").mock(return_value=Response(201, json=new_prop))

        result = await handle_datasource_type_tool(
            "create_datasource_type_property",
            {
                "mds_type_id": 1,
                "name": "timeout",
                "label": "timeout",
                "value_type_id": 2,
                "section_name_id": 1,
            },
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "timeout"
        await client.close()

    @pytest.mark.asyncio
    async def test_list_datasource_type_methods(self, client, mock_api):
        """Test list_datasource_type_methods tool."""
        methods = [{"id": 1, "name": "connect", "label": "connect", "mds_type_id": 1}]
        mock_api.get("/datasource_types/method/").mock(return_value=Response(200, json=methods))

        result = await handle_datasource_type_tool(
            "list_datasource_type_methods", {"mds_type_id": 1}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "methods" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_create_datasource_type_method(self, client, mock_api):
        """Test create_datasource_type_method tool."""
        new_method = {"id": 2, "name": "disconnect", "label": "disconnect", "code": "pass"}
        mock_api.post("/datasource_types/method/").mock(return_value=Response(201, json=new_method))

        result = await handle_datasource_type_tool(
            "create_datasource_type_method",
            {"mds_type_id": 1, "name": "disconnect", "label": "disconnect"},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "disconnect"
        await client.close()

    @pytest.mark.asyncio
    async def test_list_method_parameters(self, client, mock_api):
        """Test list_method_parameters tool."""
        params = [{"id": 1, "label": "timeout", "method_id": 1}]
        mock_api.get("/datasource_types/method_params/").mock(return_value=Response(200, json=params))

        result = await handle_datasource_type_tool("list_method_parameters", {"method_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "parameters" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_search_datasource_type_code(self, client, mock_api, sample_datasource_types):
        """Test search_datasource_type_code tool."""
        methods = [
            {"id": 1, "name": "connect", "code": "def connect(): pass", "mds_type_id": 1},
            {"id": 2, "name": "query", "code": "def query(sql): return execute(sql)", "mds_type_id": 1},
        ]
        mock_api.get("/datasource_types/ds_type/").mock(return_value=Response(200, json=sample_datasource_types))
        mock_api.get("/datasource_types/method/").mock(return_value=Response(200, json=methods))

        result = await handle_datasource_type_tool(
            "search_datasource_type_code", {"query": "execute"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "results" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_none(self, client):
        """Test that unknown tool returns None."""
        result = await handle_datasource_type_tool("unknown_tool", {}, client)
        assert result is None
        await client.close()
