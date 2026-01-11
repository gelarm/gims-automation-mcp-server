"""Tests for utility functions."""

import pytest

from gims_mcp.utils import (
    build_folder_paths,
    build_item_paths,
    search_in_code,
    check_response_size,
    ResponseTooLargeError,
    DEFAULT_MAX_RESPONSE_SIZE,
    set_max_response_size,
    get_max_response_size,
)


class TestBuildFolderPaths:
    """Tests for build_folder_paths function."""

    def test_empty_list_with_root(self):
        """Test with empty folder list (includes synthetic root by default)."""
        result = build_folder_paths([])
        assert len(result) == 1
        assert result[0]["is_root"] is True
        assert result[0]["path"] == "/"
        assert result[0]["id"] is None

    def test_empty_list_without_root(self):
        """Test with empty folder list without synthetic root."""
        result = build_folder_paths([], include_root=False)
        assert result == []

    def test_single_root_folder(self):
        """Test with a single root folder."""
        folders = [{"id": 1, "name": "root", "parent_folder_id": None}]
        result = build_folder_paths(folders)

        assert len(result) == 2  # synthetic root + actual folder
        assert result[0]["is_root"] is True
        assert result[1]["path"] == "/root"

    def test_single_root_folder_without_root(self):
        """Test with a single root folder without synthetic root."""
        folders = [{"id": 1, "name": "root", "parent_folder_id": None}]
        result = build_folder_paths(folders, include_root=False)

        assert len(result) == 1
        assert result[0]["path"] == "/root"

    def test_nested_folders(self):
        """Test with nested folders."""
        folders = [
            {"id": 1, "name": "root", "parent_folder_id": None},
            {"id": 2, "name": "child", "parent_folder_id": 1},
            {"id": 3, "name": "grandchild", "parent_folder_id": 2},
        ]
        result = build_folder_paths(folders)

        assert len(result) == 4  # synthetic root + 3 folders
        paths = {f["id"]: f["path"] for f in result}
        assert paths[None] == "/"
        assert paths[1] == "/root"
        assert paths[2] == "/root/child"
        assert paths[3] == "/root/child/grandchild"

    def test_multiple_roots(self):
        """Test with multiple root folders."""
        folders = [
            {"id": 1, "name": "root1", "parent_folder_id": None},
            {"id": 2, "name": "root2", "parent_folder_id": None},
        ]
        result = build_folder_paths(folders)

        assert len(result) == 3  # synthetic root + 2 folders
        paths = {f["id"]: f["path"] for f in result}
        assert paths[None] == "/"
        assert paths[1] == "/root1"
        assert paths[2] == "/root2"


class TestBuildItemPaths:
    """Tests for build_item_paths function."""

    def test_items_with_folders(self):
        """Test building paths for items with folders."""
        folders = [
            {"id": 1, "name": "root", "path": "/root"},
            {"id": 2, "name": "child", "path": "/root/child"},
        ]
        items = [
            {"id": 10, "name": "item1", "folder_id": 1},
            {"id": 11, "name": "item2", "folder_id": 2},
        ]
        result = build_item_paths(items, folders)

        paths = {i["id"]: i["path"] for i in result}
        assert paths[10] == "/root/item1"
        assert paths[11] == "/root/child/item2"

    def test_items_without_folder(self):
        """Test items without folder (root level)."""
        folders = [{"id": 1, "name": "root", "path": "/root"}]
        items = [{"id": 10, "name": "item1", "folder_id": None}]
        result = build_item_paths(items, folders)

        assert result[0]["path"] == "/item1"


class TestSearchInCode:
    """Tests for search_in_code function."""

    def test_simple_search(self):
        """Test simple substring search."""
        items = [
            {"id": 1, "name": "item1", "code": "def hello():\n    print('hello')"},
            {"id": 2, "name": "item2", "code": "def world():\n    pass"},
        ]
        result = search_in_code(items, "hello")

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["match_count"] == 2  # 'hello' appears twice

    def test_case_insensitive_search(self):
        """Test case-insensitive search."""
        items = [
            {"id": 1, "name": "item1", "code": "Hello World"},
            {"id": 2, "name": "item2", "code": "HELLO world"},
        ]
        result = search_in_code(items, "hello", case_sensitive=False)

        assert len(result) == 2

    def test_case_sensitive_search(self):
        """Test case-sensitive search."""
        items = [
            {"id": 1, "name": "item1", "code": "Hello World"},
            {"id": 2, "name": "item2", "code": "hello world"},
        ]
        result = search_in_code(items, "Hello", case_sensitive=True)

        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_regex_search(self):
        """Test regex pattern search."""
        items = [
            {"id": 1, "name": "item1", "code": "def function_one():"},
            {"id": 2, "name": "item2", "code": "def function_two():"},
            {"id": 3, "name": "item3", "code": "class MyClass:"},
        ]
        result = search_in_code(items, r"def \w+\(\):")

        assert len(result) == 2

    def test_no_matches(self):
        """Test when no matches found."""
        items = [{"id": 1, "name": "item1", "code": "some code"}]
        result = search_in_code(items, "not_found")

        assert len(result) == 0

    def test_empty_code(self):
        """Test items with empty code."""
        items = [
            {"id": 1, "name": "item1", "code": ""},
            {"id": 2, "name": "item2", "code": None},
        ]
        result = search_in_code(items, "test")

        assert len(result) == 0

    def test_match_context(self):
        """Test that match context is included."""
        items = [{"id": 1, "name": "item1", "code": "prefix TARGET suffix"}]
        result = search_in_code(items, "TARGET")

        assert len(result) == 1
        assert "matches" in result[0]
        assert len(result[0]["matches"]) == 1
        assert "context" in result[0]["matches"][0]
        assert "TARGET" in result[0]["matches"][0]["context"]

    def test_code_excluded_by_default(self):
        """Test that code field is excluded from results by default."""
        items = [{"id": 1, "name": "item1", "code": "hello world"}]
        result = search_in_code(items, "hello")

        assert len(result) == 1
        assert "code" not in result[0]

    def test_code_included_when_requested(self):
        """Test that code field is included when include_code=True."""
        items = [{"id": 1, "name": "item1", "code": "hello world"}]
        result = search_in_code(items, "hello", include_code=True)

        assert len(result) == 1
        assert "code" in result[0]
        assert result[0]["code"] == "hello world"


class TestCheckResponseSize:
    """Tests for check_response_size function."""

    def test_small_response_returns_json(self):
        """Test that small responses are returned as JSON strings."""
        data = {"id": 1, "name": "test"}
        result = check_response_size(data)

        assert isinstance(result, str)
        assert '"id": 1' in result
        assert '"name": "test"' in result

    def test_large_response_raises_error(self):
        """Test that large responses raise ResponseTooLargeError."""
        # Create data larger than DEFAULT_MAX_RESPONSE_SIZE (10KB)
        large_data = {"data": "x" * 15000}

        with pytest.raises(ResponseTooLargeError) as exc_info:
            check_response_size(large_data)

        assert exc_info.value.size > DEFAULT_MAX_RESPONSE_SIZE
        assert exc_info.value.limit == DEFAULT_MAX_RESPONSE_SIZE
        assert "Response too large" in str(exc_info.value)

    def test_custom_limit(self):
        """Test that custom limit is respected."""
        data = {"data": "x" * 1000}

        # Should pass with default limit
        result = check_response_size(data)
        assert isinstance(result, str)

        # Should fail with small custom limit
        with pytest.raises(ResponseTooLargeError) as exc_info:
            check_response_size(data, limit=100)

        assert exc_info.value.limit == 100

    def test_unicode_handling(self):
        """Test that Unicode characters are handled correctly."""
        data = {"text": "Привет мир 你好世界"}
        result = check_response_size(data)

        assert "Привет мир" in result
        assert "你好世界" in result

    def test_configurable_limit(self):
        """Test that global limit can be configured."""
        # Save original limit
        original_limit = get_max_response_size()

        try:
            # Set custom limit (20KB)
            set_max_response_size(20)
            assert get_max_response_size() == 20 * 1024

            # Data that fits in 20KB but not 10KB
            data = {"data": "x" * 15000}

            # Should pass with new 20KB limit
            result = check_response_size(data)
            assert isinstance(result, str)

            # Reset to smaller limit
            set_max_response_size(5)
            assert get_max_response_size() == 5 * 1024

            # Should fail with 5KB limit
            with pytest.raises(ResponseTooLargeError) as exc_info:
                check_response_size(data)

            assert exc_info.value.limit == 5 * 1024
        finally:
            # Restore original limit
            set_max_response_size(original_limit // 1024)
