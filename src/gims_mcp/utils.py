"""Utility functions for GIMS MCP Server."""

import json
import re
from typing import Any

# Default maximum response size in bytes (10KB)
DEFAULT_MAX_RESPONSE_SIZE = 10 * 1024

# Configurable maximum response size (set by server on startup)
_max_response_size: int = DEFAULT_MAX_RESPONSE_SIZE


def set_max_response_size(size_kb: int) -> None:
    """Set the maximum response size limit.

    Args:
        size_kb: Maximum size in kilobytes
    """
    global _max_response_size
    _max_response_size = size_kb * 1024


def get_max_response_size() -> int:
    """Get the current maximum response size limit in bytes."""
    return _max_response_size


class ResponseTooLargeError(Exception):
    """Raised when response exceeds maximum allowed size."""

    def __init__(self, size: int, limit: int | None = None):
        self.size = size
        self.limit = limit if limit is not None else _max_response_size
        super().__init__(
            f"Response too large ({size // 1024}KB, limit {self.limit // 1024}KB). "
            "Please refine your query to reduce results."
        )


def check_response_size(data: Any, limit: int | None = None) -> str:
    """Check response size and return JSON string if within limit.

    Args:
        data: Data to serialize to JSON
        limit: Maximum size in bytes (uses global setting if not specified)

    Returns:
        JSON string if within limit

    Raises:
        ResponseTooLargeError: If response exceeds limit
    """
    effective_limit = limit if limit is not None else _max_response_size
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    size = len(json_str.encode("utf-8"))
    if size > effective_limit:
        raise ResponseTooLargeError(size, effective_limit)
    return json_str


def build_folder_paths(
    folders: list[dict],
    id_field: str = "id",
    parent_field: str = "parent_folder_id",
    include_root: bool = True,
) -> list[dict]:
    """Build full paths for folders in a flat list.

    Args:
        folders: List of folder dictionaries
        id_field: Name of the ID field
        parent_field: Name of the parent folder ID field
        include_root: Whether to include synthetic root folder entry

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

    # Add synthetic root folder entry
    if include_root:
        result.append({
            id_field: None,
            "name": "/",
            "path": "/",
            parent_field: None,
            "is_root": True,
            "note": "Root folder. Items with folder_id=null are placed here.",
        })

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


def search_in_code(
    items: list[dict],
    query: str,
    code_field: str = "code",
    case_sensitive: bool = False,
    include_code: bool = False,
) -> list[dict]:
    """Search for a pattern in code fields.

    Args:
        items: List of items with code field
        query: Search query (substring or regex pattern)
        code_field: Name of the code field to search in
        case_sensitive: Whether search should be case-sensitive
        include_code: Whether to include full 'code' field in results (default: False)

    Returns:
        List of matching items with match info (without 'code' field by default)
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
            # Create result - always exclude 'code' field unless include_code is True
            # (but keep other fields like 'name' even when searching by name)
            result = {k: v for k, v in item.items() if k != "code" or include_code}
            result["match_count"] = len(matches)
            result["matched_in"] = code_field
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
