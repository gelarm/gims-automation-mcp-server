"""Utility functions for GIMS MCP Server."""

import re
from typing import Any


def build_folder_paths(folders: list[dict], id_field: str = "id", parent_field: str = "parent_folder_id") -> list[dict]:
    """Build full paths for folders in a flat list.

    Args:
        folders: List of folder dictionaries
        id_field: Name of the ID field
        parent_field: Name of the parent folder ID field

    Returns:
        List of folders with 'path' field added
    """
    # Build lookup dict
    folder_map = {f[id_field]: f for f in folders}

    def get_path(folder: dict) -> str:
        parts = [folder["name"]]
        parent_id = folder.get(parent_field)
        while parent_id is not None and parent_id in folder_map:
            parent = folder_map[parent_id]
            parts.insert(0, parent["name"])
            parent_id = parent.get(parent_field)
        return "/" + "/".join(parts)

    result = []
    for folder in folders:
        folder_copy = dict(folder)
        folder_copy["path"] = get_path(folder)
        result.append(folder_copy)

    return result


def build_item_paths(
    items: list[dict],
    folders: list[dict],
    folder_id_field: str = "folder_id",
    folder_lookup_field: str = "id",
) -> list[dict]:
    """Build full paths for items based on their folder.

    Args:
        items: List of item dictionaries
        folders: List of folder dictionaries with 'path' field
        folder_id_field: Name of the folder ID field in items
        folder_lookup_field: Name of the ID field in folders

    Returns:
        List of items with 'path' field added
    """
    # Build folder path lookup
    folder_paths = {f[folder_lookup_field]: f.get("path", "/") for f in folders}

    result = []
    for item in items:
        item_copy = dict(item)
        folder_id = item.get(folder_id_field)
        if folder_id is not None and folder_id in folder_paths:
            folder_path = folder_paths[folder_id]
            item_copy["path"] = f"{folder_path}/{item['name']}"
        else:
            item_copy["path"] = f"/{item['name']}"
        result.append(item_copy)

    return result


def search_in_code(items: list[dict], query: str, code_field: str = "code", case_sensitive: bool = False) -> list[dict]:
    """Search for a pattern in code fields.

    Args:
        items: List of items with code field
        query: Search query (substring or regex pattern)
        code_field: Name of the code field
        case_sensitive: Whether search should be case-sensitive

    Returns:
        List of matching items with match info
    """
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE

    try:
        pattern = re.compile(query, flags)
    except re.error:
        # If not a valid regex, escape and use as literal string
        pattern = re.compile(re.escape(query), flags)

    for item in items:
        code = item.get(code_field, "")
        if not code:
            continue

        matches = list(pattern.finditer(code))
        if matches:
            result = dict(item)
            result["match_count"] = len(matches)
            result["matches"] = []
            for match in matches[:5]:  # Limit to first 5 matches
                start = max(0, match.start() - 50)
                end = min(len(code), match.end() + 50)
                context = code[start:end]
                result["matches"].append({
                    "position": match.start(),
                    "context": context,
                })
            results.append(result)

    return results


def format_error(error: Exception) -> str:
    """Format an exception for display to the user."""
    return f"{type(error).__name__}: {str(error)}"


def truncate_code(code: str, max_lines: int = 100) -> tuple[str, bool]:
    """Truncate code to a maximum number of lines.

    Args:
        code: The code string
        max_lines: Maximum number of lines

    Returns:
        Tuple of (truncated_code, was_truncated)
    """
    lines = code.split("\n")
    if len(lines) <= max_lines:
        return code, False
    return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)", True
