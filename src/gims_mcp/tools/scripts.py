"""MCP Tools for Scripts."""

import json
from mcp.types import Tool, TextContent

from ..client import GimsClient, GimsApiError
from ..utils import build_folder_paths, build_item_paths, search_in_code, format_error


async def handle_script_tool(name: str, arguments: dict, client: GimsClient) -> list[TextContent] | None:
    """Handle script tool calls. Returns None if tool not handled."""
    try:
        handlers = {
            "list_script_folders": _list_script_folders,
            "create_script_folder": _create_script_folder,
            "update_script_folder": _update_script_folder,
            "delete_script_folder": _delete_script_folder,
            "list_scripts": _list_scripts,
            "get_script": _get_script,
            "create_script": _create_script,
            "update_script": _update_script,
            "delete_script": _delete_script,
            "search_scripts": _search_scripts,
        }
        if name in handlers:
            return await handlers[name](client, arguments)
    except GimsApiError as e:
        return [TextContent(type="text", text=f"Error: {e.message}\nDetail: {e.detail}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {format_error(e)}")]
    return None


def get_script_tools() -> list[Tool]:
    """Get the list of script tools."""
    return [
        Tool(
            name="list_script_folders",
            description="List all script folders with their hierarchy paths",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="create_script_folder",
            description="Create a new script folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Folder name"},
                    "parent_folder_id": {"type": "integer", "description": "Parent folder ID (optional)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="update_script_folder",
            description="Update an existing script folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "integer", "description": "Folder ID to update"},
                    "name": {"type": "string", "description": "New folder name"},
                    "parent_folder_id": {"type": "integer", "description": "New parent folder ID"},
                },
                "required": ["folder_id"],
            },
        ),
        Tool(
            name="delete_script_folder",
            description="Delete a script folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "integer", "description": "Folder ID to delete"},
                },
                "required": ["folder_id"],
            },
        ),
        Tool(
            name="list_scripts",
            description="List all scripts with their folder paths",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "integer", "description": "Filter by folder ID (optional)"},
                },
            },
        ),
        Tool(
            name="get_script",
            description="Get a script by ID, including its code",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {"type": "integer", "description": "Script ID"},
                },
                "required": ["script_id"],
            },
        ),
        Tool(
            name="create_script",
            description="Create a new script",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Script name (unique)"},
                    "code": {"type": "string", "description": "Python code for the script"},
                    "folder_id": {"type": "integer", "description": "Folder ID (optional)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="update_script",
            description="Update an existing script",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {"type": "integer", "description": "Script ID to update"},
                    "name": {"type": "string", "description": "New script name"},
                    "code": {"type": "string", "description": "New Python code"},
                    "folder_id": {"type": "integer", "description": "New folder ID"},
                },
                "required": ["script_id"],
            },
        ),
        Tool(
            name="delete_script",
            description="Delete a script",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {"type": "integer", "description": "Script ID to delete"},
                },
                "required": ["script_id"],
            },
        ),
        Tool(
            name="search_scripts",
            description="Search scripts by code content and/or name",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (substring or regex)"},
                    "search_in": {
                        "type": "string",
                        "description": "Where to search: 'code', 'name', or 'both' (default: 'both')",
                        "enum": ["code", "name", "both"],
                    },
                    "case_sensitive": {"type": "boolean", "description": "Case-sensitive search (default: false)"},
                },
                "required": ["query"],
            },
        ),
    ]


# Handler implementations

async def _list_script_folders(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_script_folders()
    folders_with_paths = build_folder_paths(folders)
    return [TextContent(type="text", text=json.dumps({"folders": folders_with_paths}, indent=2, ensure_ascii=False))]


async def _create_script_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_script_folder(
        name=arguments["name"],
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_script_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.update_script_folder(
        folder_id=arguments["folder_id"],
        name=arguments.get("name"),
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_script_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_script_folder(folder_id=arguments["folder_id"])
    return [TextContent(type="text", text="Folder deleted successfully")]


async def _list_scripts(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_script_folders()
    folders_with_paths = build_folder_paths(folders)
    scripts = await client.list_scripts(folder_id=arguments.get("folder_id"))
    scripts_with_paths = build_item_paths(scripts, folders_with_paths)
    return [TextContent(type="text", text=json.dumps({"scripts": scripts_with_paths}, indent=2, ensure_ascii=False))]


async def _get_script(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.get_script(script_id=arguments["script_id"])
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _create_script(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_script(
        name=arguments["name"],
        code=arguments.get("code", ""),
        folder_id=arguments.get("folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_script(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.update_script(
        script_id=arguments["script_id"],
        name=arguments.get("name"),
        code=arguments.get("code"),
        folder_id=arguments.get("folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_script(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_script(script_id=arguments["script_id"])
    return [TextContent(type="text", text="Script deleted successfully")]


async def _search_scripts(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Search scripts by code and/or name.

    Combines:
    - API search by code (if search_in is 'code' or 'both')
    - Local search by name (if search_in is 'name' or 'both')
    """
    query = arguments["query"]
    search_in = arguments.get("search_in", "both")
    case_sensitive = arguments.get("case_sensitive", False)

    results = []
    found_ids = set()

    # Search by code via API
    if search_in in ("code", "both"):
        api_results = await client.search_scripts(
            search_code=query,
            case_sensitive=case_sensitive,
        )
        for r in api_results:
            if r.get("id") not in found_ids:
                r["matched_in"] = "code"
                results.append(r)
                found_ids.add(r.get("id"))

    # Search by name locally
    if search_in in ("name", "both"):
        scripts = await client.list_scripts()
        name_results = search_in_code(
            scripts,
            query,
            code_field="name",
            case_sensitive=case_sensitive,
        )
        for r in name_results:
            if r.get("id") not in found_ids:
                r["matched_in"] = "name"
                results.append(r)
                found_ids.add(r.get("id"))

    return [TextContent(type="text", text=json.dumps({"results": results}, indent=2, ensure_ascii=False))]
