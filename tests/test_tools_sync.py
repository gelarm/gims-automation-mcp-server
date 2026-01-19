"""Tests for Git sync tools."""

import json
import pytest
import respx
from httpx import Response

from gims_mcp.tools.sync import get_sync_tools, handle_sync_tool


class TestGetSyncTools:
    """Tests for get_sync_tools function."""

    def test_returns_list_of_tools(self):
        """Test that get_sync_tools returns a list."""
        tools = get_sync_tools()
        assert isinstance(tools, list)
        assert len(tools) == 8

    def test_all_tools_have_required_fields(self):
        """Test that all tools have name, description, and inputSchema."""
        tools = get_sync_tools()
        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

    def test_tool_names(self):
        """Test that all expected tools are present."""
        tools = get_sync_tools()
        names = {tool.name for tool in tools}
        expected = {
            "export_script",
            "import_script",
            "export_datasource_type",
            "import_datasource_type",
            "export_activator_type",
            "import_activator_type",
            "validate_python_code",
            "compare_with_git",
        }
        assert names == expected


class TestValidatePythonCodeTool:
    """Tests for validate_python_code tool."""

    @pytest.mark.asyncio
    async def test_valid_code(self, client):
        """Test validation of valid Python code."""
        result = await handle_sync_tool(
            "validate_python_code",
            {"code": "def hello():\n    print('Hello')"},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["valid"] is True
        assert data["error"] is None
        await client.close()

    @pytest.mark.asyncio
    async def test_invalid_code(self, client):
        """Test validation of invalid Python code."""
        result = await handle_sync_tool(
            "validate_python_code",
            {"code": "def broken(\n    pass"},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["valid"] is False
        assert data["error"] is not None
        assert "Синтаксическая ошибка" in data["error"]
        await client.close()

    @pytest.mark.asyncio
    async def test_empty_code(self, client):
        """Test validation of empty code."""
        result = await handle_sync_tool(
            "validate_python_code",
            {"code": ""},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["valid"] is True
        await client.close()


class TestExportScriptTool:
    """Tests for export_script tool."""

    @pytest.mark.asyncio
    async def test_export_by_id(self, client, mock_api):
        """Test exporting script by ID."""
        script = {
            "id": 1,
            "name": "Test Script",
            "code": 'print("hello")',
            "folder_id": None,
            "description": "A test",
            "updated_at": "2026-01-15T10:00:00Z",
        }
        mock_api.get("/scripts/script/1/").mock(return_value=Response(200, json=script))

        result = await handle_sync_tool("export_script", {"script_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "files" in data
        assert "meta.yaml" in data["files"]
        assert "code.py" in data["files"]
        assert data["files"]["code.py"] == 'print("hello")'
        assert "suggested_folder" in data
        assert data["suggested_folder"] == "test_script"
        await client.close()

    @pytest.mark.asyncio
    async def test_export_by_name(self, client, mock_api, sample_scripts):
        """Test exporting script by name."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))
        mock_api.get("/scripts/script/1/").mock(
            return_value=Response(200, json={
                "id": 1,
                "name": "test_script",
                "code": "print('hello')",
                "folder_id": 2,
            })
        )

        result = await handle_sync_tool("export_script", {"script_name": "test_script"}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "files" in data
        await client.close()

    @pytest.mark.asyncio
    async def test_export_not_found(self, client, mock_api):
        """Test exporting non-existent script."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=[]))

        result = await handle_sync_tool("export_script", {"script_name": "nonexistent"}, client)

        assert result is not None
        assert "не найден" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_export_no_params(self, client):
        """Test export without any parameters."""
        result = await handle_sync_tool("export_script", {}, client)

        assert result is not None
        assert "Укажите" in result[0].text
        await client.close()


class TestImportScriptTool:
    """Tests for import_script tool."""

    @pytest.mark.asyncio
    async def test_import_new_script(self, client, mock_api):
        """Test importing a new script."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=[]))
        mock_api.post("/scripts/script/").mock(
            return_value=Response(201, json={"id": 10, "name": "New Script"})
        )

        meta_yaml = "name: New Script\ncode_file: code.py"
        code = 'print("hello")'

        result = await handle_sync_tool(
            "import_script",
            {"meta_yaml": meta_yaml, "code": code},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["action"] == "created"
        assert data["script_id"] == 10
        await client.close()

    @pytest.mark.asyncio
    async def test_import_invalid_syntax(self, client):
        """Test importing script with invalid Python syntax."""
        meta_yaml = "name: Broken Script\ncode_file: code.py"
        code = "def broken(\n    pass"

        result = await handle_sync_tool(
            "import_script",
            {"meta_yaml": meta_yaml, "code": code},
            client,
        )

        assert result is not None
        assert "Ошибка синтаксиса" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_import_existing_without_update(self, client, mock_api):
        """Test importing when script already exists."""
        existing = [{"id": 5, "name": "Existing Script"}]
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=existing))

        meta_yaml = "name: Existing Script\ncode_file: code.py"
        code = 'print("hello")'

        result = await handle_sync_tool(
            "import_script",
            {"meta_yaml": meta_yaml, "code": code, "update_existing": False},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert "error" in data
        assert "уже существует" in data["error"]
        assert data["existing_id"] == 5
        await client.close()

    @pytest.mark.asyncio
    async def test_import_existing_with_update(self, client, mock_api):
        """Test updating existing script."""
        existing = [{"id": 5, "name": "Existing Script"}]
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=existing))
        mock_api.patch("/scripts/script/5/").mock(
            return_value=Response(200, json={"id": 5, "name": "Existing Script"})
        )

        meta_yaml = "name: Existing Script\ncode_file: code.py"
        code = 'print("updated")'

        result = await handle_sync_tool(
            "import_script",
            {"meta_yaml": meta_yaml, "code": code, "update_existing": True},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["action"] == "updated"
        assert data["script_id"] == 5
        await client.close()


class TestCompareWithGitTool:
    """Tests for compare_with_git tool."""

    @pytest.mark.asyncio
    async def test_gims_newer(self, client, mock_api):
        """Test comparison when GIMS version is newer."""
        scripts = [{
            "id": 1,
            "name": "Test Script",
            "updated_at": "2026-01-20T10:00:00Z",
        }]
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=scripts))

        result = await handle_sync_tool(
            "compare_with_git",
            {
                "component_type": "script",
                "gims_name": "Test Script",
                "git_exported_at": "2026-01-15T10:00:00Z",
            },
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["status"] == "gims_newer"
        assert data["recommendation"] == "export"
        await client.close()

    @pytest.mark.asyncio
    async def test_git_newer(self, client, mock_api):
        """Test comparison when Git version is newer."""
        scripts = [{
            "id": 1,
            "name": "Test Script",
            "updated_at": "2026-01-10T10:00:00Z",
        }]
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=scripts))

        result = await handle_sync_tool(
            "compare_with_git",
            {
                "component_type": "script",
                "gims_name": "Test Script",
                "git_exported_at": "2026-01-15T10:00:00Z",
            },
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["status"] == "git_newer"
        assert data["recommendation"] == "import"
        await client.close()

    @pytest.mark.asyncio
    async def test_in_sync(self, client, mock_api):
        """Test comparison when versions are in sync."""
        scripts = [{
            "id": 1,
            "name": "Test Script",
            "updated_at": "2026-01-15T10:00:00+00:00",
        }]
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=scripts))

        result = await handle_sync_tool(
            "compare_with_git",
            {
                "component_type": "script",
                "gims_name": "Test Script",
                "git_exported_at": "2026-01-15T10:00:00Z",
            },
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["status"] == "in_sync"
        await client.close()

    @pytest.mark.asyncio
    async def test_not_found_in_gims(self, client, mock_api):
        """Test comparison when component not found in GIMS."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=[]))

        result = await handle_sync_tool(
            "compare_with_git",
            {
                "component_type": "script",
                "gims_name": "Missing Script",
                "git_exported_at": "2026-01-15T10:00:00Z",
            },
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["status"] == "not_found_in_gims"
        assert data["recommendation"] == "import"
        await client.close()

    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client):
        """Test comparison with invalid date format."""
        result = await handle_sync_tool(
            "compare_with_git",
            {
                "component_type": "script",
                "gims_name": "Test",
                "git_exported_at": "invalid-date",
            },
            client,
        )

        assert result is not None
        assert "Неверный формат даты" in result[0].text
        await client.close()

    @pytest.mark.asyncio
    async def test_unknown_component_type(self, client):
        """Test comparison with unknown component type."""
        result = await handle_sync_tool(
            "compare_with_git",
            {
                "component_type": "unknown_type",
                "gims_name": "Test",
                "git_exported_at": "2026-01-15T10:00:00Z",
            },
            client,
        )

        assert result is not None
        assert "Неизвестный тип компонента" in result[0].text
        await client.close()


class TestExportDatasourceTypeTool:
    """Tests for export_datasource_type tool."""

    @pytest.mark.asyncio
    async def test_export_by_id(self, client, mock_api):
        """Test exporting datasource type by ID."""
        ds_type = {
            "id": 1,
            "name": "PostgreSQL",
            "description": "PostgreSQL monitor",
            "version": "1.0",
        }
        mock_api.get("/datasource_types/ds_type/1/").mock(return_value=Response(200, json=ds_type))
        mock_api.get("/datasource_types/properties/").mock(return_value=Response(200, json=[]))
        mock_api.get("/datasource_types/method/").mock(return_value=Response(200, json=[]))

        result = await handle_sync_tool("export_datasource_type", {"type_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "files" in data
        assert "meta.yaml" in data["files"]
        assert "properties.yaml" in data["files"]
        assert data["suggested_folder"] == "postgresql"
        await client.close()

    @pytest.mark.asyncio
    async def test_export_not_found(self, client, mock_api):
        """Test exporting non-existent datasource type."""
        mock_api.get("/datasource_types/ds_type/").mock(return_value=Response(200, json=[]))

        result = await handle_sync_tool("export_datasource_type", {"type_name": "nonexistent"}, client)

        assert result is not None
        assert "не найден" in result[0].text
        await client.close()


class TestExportActivatorTypeTool:
    """Tests for export_activator_type tool."""

    @pytest.mark.asyncio
    async def test_export_by_id(self, client, mock_api):
        """Test exporting activator type by ID."""
        act_type = {
            "id": 1,
            "name": "HTTP Poller",
            "description": "Poll HTTP endpoints",
            "code": "# poll code",
            "version": "1.0",
        }
        mock_api.get("/activator_types/activator_type/1/").mock(return_value=Response(200, json=act_type))
        mock_api.get("/activator_types/properties/").mock(return_value=Response(200, json=[]))

        result = await handle_sync_tool("export_activator_type", {"type_id": 1}, client)

        assert result is not None
        data = json.loads(result[0].text)
        assert "files" in data
        assert "meta.yaml" in data["files"]
        assert "code.py" in data["files"]
        assert "properties.yaml" in data["files"]
        assert data["files"]["code.py"] == "# poll code"
        await client.close()


class TestImportDatasourceTypeTool:
    """Tests for import_datasource_type tool."""

    @pytest.mark.asyncio
    async def test_import_new_type(self, client, mock_api):
        """Test importing a new datasource type."""
        mock_api.get("/datasource_types/ds_type/").mock(return_value=Response(200, json=[]))
        mock_api.post("/datasource_types/ds_type/").mock(
            return_value=Response(201, json={"id": 10, "name": "New Type"})
        )

        files = {
            "meta.yaml": "name: New Type\ndescription: A new type",
            "properties.yaml": "properties: []",
        }

        result = await handle_sync_tool(
            "import_datasource_type",
            {"files": files},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["action"] == "created"
        assert data["type_id"] == 10
        await client.close()

    @pytest.mark.asyncio
    async def test_import_with_invalid_method_code(self, client):
        """Test importing with invalid Python in method."""
        files = {
            "meta.yaml": "name: New Type",
            "properties.yaml": "properties: []",
            "methods/broken/meta.yaml": "name: Broken\nlabel: broken",
            "methods/broken/code.py": "def broken(\n    pass",
            "methods/broken/params.yaml": "parameters: []",
        }

        result = await handle_sync_tool(
            "import_datasource_type",
            {"files": files},
            client,
        )

        assert result is not None
        assert "Ошибка синтаксиса" in result[0].text
        assert "broken" in result[0].text
        await client.close()


class TestImportActivatorTypeTool:
    """Tests for import_activator_type tool."""

    @pytest.mark.asyncio
    async def test_import_new_type(self, client, mock_api):
        """Test importing a new activator type."""
        mock_api.get("/activator_types/activator_type/").mock(return_value=Response(200, json=[]))
        mock_api.post("/activator_types/activator_type/").mock(
            return_value=Response(201, json={"id": 10, "name": "New Activator"})
        )

        files = {
            "meta.yaml": "name: New Activator\ndescription: A new activator",
            "code.py": "# activator code",
            "properties.yaml": "properties: []",
        }

        result = await handle_sync_tool(
            "import_activator_type",
            {"files": files},
            client,
        )

        assert result is not None
        data = json.loads(result[0].text)
        assert data["action"] == "created"
        assert data["type_id"] == 10
        await client.close()

    @pytest.mark.asyncio
    async def test_import_with_invalid_code(self, client):
        """Test importing with invalid Python code."""
        files = {
            "meta.yaml": "name: Broken Activator",
            "code.py": "def broken(\n    pass",
            "properties.yaml": "properties: []",
        }

        result = await handle_sync_tool(
            "import_activator_type",
            {"files": files},
            client,
        )

        assert result is not None
        assert "Ошибка синтаксиса" in result[0].text
        await client.close()


class TestHandleSyncToolUnknown:
    """Tests for unknown tool handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_none(self, client):
        """Test that unknown tool returns None."""
        result = await handle_sync_tool("unknown_tool", {}, client)
        assert result is None
        await client.close()
