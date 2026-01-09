"""Tests for GIMS API client."""

import pytest
import respx
from httpx import Response

from gims_mcp.client import GimsClient, GimsApiError


class TestGimsClientScripts:
    """Tests for script-related client methods."""

    @pytest.mark.asyncio
    async def test_list_script_folders(self, client, mock_api, sample_folders):
        """Test listing script folders."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(200, json=sample_folders))

        result = await client.list_script_folders()

        assert result == sample_folders
        await client.close()

    @pytest.mark.asyncio
    async def test_create_script_folder(self, client, mock_api):
        """Test creating a script folder."""
        new_folder = {"id": 4, "name": "new_folder", "parent_folder_id": 1}
        mock_api.post("/scripts/folder/").mock(return_value=Response(201, json=new_folder))

        result = await client.create_script_folder(name="new_folder", parent_folder_id=1)

        assert result == new_folder
        await client.close()

    @pytest.mark.asyncio
    async def test_list_scripts(self, client, mock_api, sample_scripts):
        """Test listing scripts."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))

        result = await client.list_scripts()

        assert result == sample_scripts
        await client.close()

    @pytest.mark.asyncio
    async def test_list_scripts_filtered(self, client, mock_api, sample_scripts):
        """Test listing scripts filtered by folder."""
        mock_api.get("/scripts/script/").mock(return_value=Response(200, json=sample_scripts))

        result = await client.list_scripts(folder_id=2)

        assert len(result) == 1
        assert result[0]["folder_id"] == 2
        await client.close()

    @pytest.mark.asyncio
    async def test_get_script(self, client, mock_api, sample_scripts):
        """Test getting a single script."""
        mock_api.get("/scripts/script/1/").mock(return_value=Response(200, json=sample_scripts[0]))

        result = await client.get_script(script_id=1)

        assert result == sample_scripts[0]
        await client.close()

    @pytest.mark.asyncio
    async def test_create_script(self, client, mock_api):
        """Test creating a script."""
        new_script = {"id": 3, "name": "new_script", "code": "# new code", "folder_id": 1}
        mock_api.post("/scripts/script/").mock(return_value=Response(201, json=new_script))

        result = await client.create_script(name="new_script", code="# new code", folder_id=1)

        assert result == new_script
        await client.close()

    @pytest.mark.asyncio
    async def test_update_script(self, client, mock_api):
        """Test updating a script."""
        updated = {"id": 1, "name": "updated_name", "code": "# updated", "folder_id": 1}
        mock_api.patch("/scripts/script/1/").mock(return_value=Response(200, json=updated))

        result = await client.update_script(script_id=1, name="updated_name", code="# updated")

        assert result == updated
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_script(self, client, mock_api):
        """Test deleting a script."""
        mock_api.delete("/scripts/script/1/").mock(return_value=Response(204))

        result = await client.delete_script(script_id=1)

        assert result is None
        await client.close()

    @pytest.mark.asyncio
    async def test_search_scripts(self, client, mock_api):
        """Test searching scripts."""
        search_results = [{"id": 1, "count": 2}]
        mock_api.get("/scripts/search_code/").mock(return_value=Response(200, json=search_results))

        result = await client.search_scripts(search_code="print")

        assert result == search_results
        await client.close()


class TestGimsClientErrors:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, client, mock_api):
        """Test handling of 401 errors."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(401, json={"detail": "Invalid token"}))

        with pytest.raises(GimsApiError) as exc_info:
            await client.list_script_folders()

        assert exc_info.value.status_code == 401
        assert "Authentication failed" in exc_info.value.message
        await client.close()

    @pytest.mark.asyncio
    async def test_permission_error(self, client, mock_api):
        """Test handling of 403 errors."""
        mock_api.get("/scripts/folder/").mock(return_value=Response(403, json={"detail": "Forbidden"}))

        with pytest.raises(GimsApiError) as exc_info:
            await client.list_script_folders()

        assert exc_info.value.status_code == 403
        assert "Permission denied" in exc_info.value.message
        await client.close()

    @pytest.mark.asyncio
    async def test_not_found_error(self, client, mock_api):
        """Test handling of 404 errors."""
        mock_api.get("/scripts/script/999/").mock(return_value=Response(404, json={"detail": "Not found"}))

        with pytest.raises(GimsApiError) as exc_info:
            await client.get_script(script_id=999)

        assert exc_info.value.status_code == 404
        await client.close()

    @pytest.mark.asyncio
    async def test_validation_error(self, client, mock_api):
        """Test handling of 400 errors."""
        mock_api.post("/scripts/script/").mock(
            return_value=Response(400, json={"detail": "Name is required"})
        )

        with pytest.raises(GimsApiError) as exc_info:
            await client.create_script(name="")

        assert exc_info.value.status_code == 400
        await client.close()


class TestGimsClientReferences:
    """Tests for reference data client methods."""

    @pytest.mark.asyncio
    async def test_list_value_types(self, client, mock_api, sample_value_types):
        """Test listing value types."""
        mock_api.get("/rest/value_types/").mock(return_value=Response(200, json=sample_value_types))

        result = await client.list_value_types()

        assert result == sample_value_types
        await client.close()

    @pytest.mark.asyncio
    async def test_list_property_sections(self, client, mock_api, sample_property_sections):
        """Test listing property sections."""
        mock_api.get("/rest/property_sections/").mock(return_value=Response(200, json=sample_property_sections))

        result = await client.list_property_sections()

        assert result == sample_property_sections
        await client.close()
