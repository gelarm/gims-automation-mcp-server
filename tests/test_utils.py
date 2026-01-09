"""Tests for utility functions."""

import pytest

from gims_mcp.utils import build_folder_paths, build_item_paths, search_in_code


class TestBuildFolderPaths:
    """Tests for build_folder_paths function."""

    def test_empty_list(self):
        """Test with empty folder list."""
        result = build_folder_paths([])
        assert result == []

    def test_single_root_folder(self):
        """Test with a single root folder."""
        folders = [{"id": 1, "name": "root", "parent_folder_id": None}]
        result = build_folder_paths(folders)

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

        paths = {f["id"]: f["path"] for f in result}
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

        paths = {f["id"]: f["path"] for f in result}
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
