"""Tests for script tools."""

import json
import pytest
import respx
from httpx import Response

from gims_mcp.tools.scripts import get_script_tools, handle_script_tool


class TestGetScriptTools:
    """Tests for get_script_tools function."""

    def test_returns_list_of_tools(self):
        """Test that get_script_tools returns a list."""
        tools = get_script_tools()
        assert isinstance(tools, list)
        assert len(tools) == 11  # Including get_script_code

    def test_all_tools_have_required_fields(self):
        """Test that all tools have name, description, and inputSchema."""
        tools = get_script_tools()
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_tool_names(self):
        """Test that all expected tools are present."""
        tools = get_script_tools()
        names = {tool.name for tool in tools}
        expected = {
            "list_script_folders",
            "create_script_folder",
            "update_script_folder",
            "delete_script_folder",
            "list_scripts",
            "get_script",
            "get_script_code",
            "create_script",
            "update_script",
            "delete_script",
            "search_scripts",
        }
        assert names == expected


class TestHandleScriptTool:
    """Tests for handle_script_tool function."""

    @pytest.mark.asyncio
    async def test_list_script_folders(self, client, mock_api, sample_folders):
        """Test list_script_folders tool."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(200, json=sample_folders))

        result = await handle_script_tool("list_script_folders", {}, client)

        assert result is not None
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "folders" in data
        # 3 sample folders + 1 synthetic root folder
        assert len(data["folders"]) == 4
        # First folder should be synthetic root
        assert data["folders"][0]["is_root"] is True
        assert data["folders"][0]["path"] == "/"
        await client.close()

    @pytest.mark.asyncio
    async def test_create_script_folder(self, client, mock_api):
        """Test create_script_folder tool."""
        new_folder = {"id": 4, "name": "new_folder", "parent_folder_id": 1}
        mock_api.post("/scripts/folder/").mock(return_value=Response(201, json=new_folder))

        result = await handle_script_tool(
            "create_script_folder", {"name": "new_folder", "parent_folder_id": 1}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "new_folder"
        await client.close()

    @pytest.mark.asyncio
    async def test_update_script_folder(self, client, mock_api):
        """Test update_script_folder tool."""
        updated = {"id": 1, "name": "updated_name", "parent_folder_id": None}
        mock_api.patch("/scripts/folder/1/").mock(return_value=Response(200, json=updated))

        result = await handle_script_tool(
            "update_script_folder", {"folder_id": 1, "name": "updated_name"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "updated_name"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_script_folder(self, client, mock_api):
        """Test delete_script_folder tool."""
        mock_api.delete("/scripts/folder/1/").mock(return_value=Response(204))

        result = await handle_script_tool("delete_script_folder", {"folder_id": 1}, client)

        assert result is not None
        assert "deleted successfully" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_list_scripts(self, client, mock_api, sample_folders, sample_scripts):
        """Test list_scripts tool."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(200, json=sample_folders))
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))

        result = await handle_script_tool("list_scripts", {}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "scripts" in data
        assert len(data["scripts"]) == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_list_scripts_filtered(self, client, mock_api, sample_folders, sample_scripts):
        """Test list_scripts tool with folder filter."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(200, json=sample_folders))
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))

        result = await handle_script_tool("list_scripts", {"folder_id": 2}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert len(data["scripts"]) == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_get_script(self, client, mock_api, sample_scripts):
        """Test get_script tool - code should be filtered."""
        mock_api.get("/scripts/script/1/").mock(return_value=Response(200, json=sample_scripts[0]))

        result = await handle_script_tool("get_script", {"script_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "test_script"
        # Code should be filtered
        assert data["code"] == "[FILTERED]"
        await client.close()

    @pytest.mark.asyncio
    async def test_get_script_code(self, client, mock_api, sample_scripts):
        """Test get_script_code tool - returns full code."""
        mock_api.get("/scripts/script/1/").mock(return_value=Response(200, json=sample_scripts[0]))

        result = await handle_script_tool("get_script_code", {"script_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert data["id"] == 1
        assert data["name"] == "test_script"
        # Code should be present
        assert data["code"] == sample_scripts[0]["code"]
        await client.close()

    @pytest.mark.asyncio
    async def test_create_script(self, client, mock_api):
        """Test create_script tool."""
        new_script = {"id": 3, "name": "new_script", "code": "print('hello')", "folder_id": 1}
        mock_api.post("/scripts/script/").mock(return_value=Response(201, json=new_script))

        result = await handle_script_tool(
            "create_script", {"name": "new_script", "code": "print('hello')", "folder_id": 1}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "new_script"
        await client.close()

    @pytest.mark.asyncio
    async def test_update_script(self, client, mock_api):
        """Test update_script tool."""
        updated = {"id": 1, "name": "updated_name", "code": "print('updated')", "folder_id": 1}
        mock_api.patch("/scripts/script/1/").mock(return_value=Response(200, json=updated))

        result = await handle_script_tool(
            "update_script", {"script_id": 1, "name": "updated_name", "code": "print('updated')"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["name"] == "updated_name"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_script(self, client, mock_api):
        """Test delete_script tool."""
        mock_api.delete("/scripts/script/1/").mock(return_value=Response(204))

        result = await handle_script_tool("delete_script", {"script_id": 1}, client)

        assert result is not None
        assert "deleted successfully" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_search_scripts_by_code(self, client, mock_api):
        """Test search_scripts tool searching by code."""
        search_results = [{"id": 1, "name": "test_script", "count": 2}]
        mock_api.get("/scripts/search_code/").mock(return_value=Response(200, json=search_results))

        result = await handle_script_tool(
            "search_scripts", {"query": "print", "search_in": "code"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "results" in data
        assert len(data["results"]) == 1
        await client.close()

    @pytest.mark.asyncio
    async def test_search_scripts_by_name(self, client, mock_api, sample_scripts):
        """Test search_scripts tool searching by name."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))

        result = await handle_script_tool(
            "search_scripts", {"query": "health", "search_in": "name"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "results" in data
        # Should find "check_health"
        assert any("health" in r.get("name", "").lower() for r in data["results"])
        await client.close()

    @pytest.mark.asyncio
    async def test_search_scripts_both(self, client, mock_api, sample_scripts):
        """Test search_scripts tool searching in both code and name."""
        search_results = [{"id": 1, "name": "test_script", "count": 1}]
        mock_api.get("/scripts/search_code/").mock(return_value=Response(200, json=search_results))
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))

        result = await handle_script_tool(
            "search_scripts", {"query": "test", "search_in": "both"}, client
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "results" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_none(self, client):
        """Test that unknown tool returns None."""
        result = await handle_script_tool("unknown_tool", {}, client)
        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_error_handling(self, client, mock_api):
        """Test error handling in tools."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(401, json={"detail": "Invalid token"}))

        result = await handle_script_tool("list_script_folders", {}, client)

        assert result is not None
        assert "Error" in result[0].text
        await client.close()
