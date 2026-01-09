"""MCP Tools for Activator Types."""

from mcp.types import Tool, TextContent

from ..client import GimsClient, GimsApiError
from ..utils import (
    build_folder_paths,
    build_item_paths,
    search_in_code,
    format_error,
    check_response_size,
    ResponseTooLargeError,
)


async def handle_activator_type_tool(name: str, arguments: dict, client: GimsClient) -> list[TextContent] | None:
    """Handle activator type tool calls. Returns None if tool not handled."""
    try:
        handlers = {
            "list_activator_type_folders": _list_activator_type_folders,
            "create_activator_type_folder": _create_activator_type_folder,
            "update_activator_type_folder": _update_activator_type_folder,
            "delete_activator_type_folder": _delete_activator_type_folder,
            "list_activator_types": _list_activator_types,
            "get_activator_type": _get_activator_type,
            "create_activator_type": _create_activator_type,
            "update_activator_type": _update_activator_type,
            "delete_activator_type": _delete_activator_type,
            "list_activator_type_properties": _list_activator_type_properties,
            "create_activator_type_property": _create_activator_type_property,
            "update_activator_type_property": _update_activator_type_property,
            "delete_activator_type_property": _delete_activator_type_property,
            "search_activator_types": _search_activator_types,
        }
        if name in handlers:
            return await handlers[name](client, arguments)
    except ResponseTooLargeError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except GimsApiError as e:
        return [TextContent(type="text", text=f"Error: {e.message}\nDetail: {e.detail}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {format_error(e)}")]
    return None


def get_activator_type_tools() -> list[Tool]:
    """Get the list of activator type tools."""
    return [
        # Folders
        Tool(
            name="list_activator_type_folders",
            description="List all activator type folders with their hierarchy paths",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="create_activator_type_folder",
            description="Create a new activator type folder",
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
            name="update_activator_type_folder",
            description="Update an activator type folder",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_id": {"type": "integer", "description": "Folder ID"},
                    "name": {"type": "string", "description": "New name"},
                    "parent_folder_id": {"type": "integer", "description": "New parent folder ID"},
                },
                "required": ["folder_id"],
            },
        ),
        Tool(
            name="delete_activator_type_folder",
            description="Delete an activator type folder",
            inputSchema={
                "type": "object",
                "properties": {"folder_id": {"type": "integer", "description": "Folder ID"}},
                "required": ["folder_id"],
            },
        ),
        # Types
        Tool(
            name="list_activator_types",
            description="List all activator types",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_activator_type",
            description="Get an activator type with its code and properties",
            inputSchema={
                "type": "object",
                "properties": {"type_id": {"type": "integer", "description": "Type ID"}},
                "required": ["type_id"],
            },
        ),
        Tool(
            name="create_activator_type",
            description="Create a new activator type",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Type name"},
                    "code": {"type": "string", "description": "Python code for the activator"},
                    "description": {"type": "string", "description": "Description"},
                    "version": {"type": "string", "description": "Version (default: 1.0)"},
                    "folder_id": {"type": "integer", "description": "Folder ID (optional)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="update_activator_type",
            description="Update an activator type (including its code)",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_id": {"type": "integer", "description": "Type ID"},
                    "name": {"type": "string", "description": "New name"},
                    "code": {"type": "string", "description": "New Python code"},
                    "description": {"type": "string", "description": "New description"},
                    "version": {"type": "string", "description": "New version"},
                    "folder_id": {"type": "integer", "description": "New folder ID"},
                },
                "required": ["type_id"],
            },
        ),
        Tool(
            name="delete_activator_type",
            description="Delete an activator type",
            inputSchema={
                "type": "object",
                "properties": {"type_id": {"type": "integer", "description": "Type ID"}},
                "required": ["type_id"],
            },
        ),
        # Properties
        Tool(
            name="list_activator_type_properties",
            description="List all properties of an activator type",
            inputSchema={
                "type": "object",
                "properties": {"activator_type_id": {"type": "integer", "description": "Activator type ID"}},
                "required": ["activator_type_id"],
            },
        ),
        Tool(
            name="create_activator_type_property",
            description="Create a new property for an activator type",
            inputSchema={
                "type": "object",
                "properties": {
                    "activator_type_id": {"type": "integer", "description": "Activator type ID"},
                    "name": {"type": "string", "description": "Property name"},
                    "label": {"type": "string", "description": "Property label (code identifier, English only)"},
                    "value_type_id": {"type": "integer", "description": "Value type ID"},
                    "section_name_id": {"type": "integer", "description": "Section ID"},
                    "description": {"type": "string", "description": "Description"},
                    "default_value": {"type": "string", "description": "Default value"},
                    "is_required": {"type": "boolean", "description": "Is required (default: false)"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden (default: false)"},
                },
                "required": ["activator_type_id", "name", "label", "value_type_id", "section_name_id"],
            },
        ),
        Tool(
            name="update_activator_type_property",
            description="Update an activator type property",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_id": {"type": "integer", "description": "Property ID"},
                    "name": {"type": "string", "description": "New name"},
                    "label": {"type": "string", "description": "New label"},
                    "description": {"type": "string", "description": "New description"},
                    "default_value": {"type": "string", "description": "New default value"},
                    "is_required": {"type": "boolean", "description": "Is required"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden"},
                },
                "required": ["property_id"],
            },
        ),
        Tool(
            name="delete_activator_type_property",
            description="Delete an activator type property",
            inputSchema={
                "type": "object",
                "properties": {"property_id": {"type": "integer", "description": "Property ID"}},
                "required": ["property_id"],
            },
        ),
        # Search
        Tool(
            name="search_activator_types",
            description="Search activator types by name and/or code. Default searches by name only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (substring or regex)"},
                    "search_in": {
                        "type": "string",
                        "description": "Where to search: 'name' (default), 'code', or 'both'",
                        "enum": ["name", "code", "both"],
                    },
                    "case_sensitive": {"type": "boolean", "description": "Case-sensitive search (default: false)"},
                },
                "required": ["query"],
            },
        ),
    ]


# Handler implementations

async def _list_activator_type_folders(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_activator_type_folders()
    folders_with_paths = build_folder_paths(folders)
    response = check_response_size({"folders": folders_with_paths})
    return [TextContent(type="text", text=response)]


async def _create_activator_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_activator_type_folder(
        name=arguments["name"],
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_activator_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.update_activator_type_folder(
        folder_id=arguments["folder_id"],
        name=arguments.get("name"),
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_activator_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_activator_type_folder(folder_id=arguments["folder_id"])
    return [TextContent(type="text", text="Folder deleted successfully")]


async def _list_activator_types(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_activator_type_folders()
    folders_with_paths = build_folder_paths(folders)
    types = await client.list_activator_types()
    # Remove code from list to reduce size
    types_no_code = [{k: v for k, v in t.items() if k != "code"} for t in types]
    types_with_paths = build_item_paths(types_no_code, folders_with_paths, folder_id_field="folder")
    response = check_response_size({"types": types_with_paths})
    return [TextContent(type="text", text=response)]


async def _get_activator_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    type_id = arguments["type_id"]
    act_type = await client.get_activator_type(type_id)
    properties = await client.list_activator_type_properties(type_id)
    result = {
        "type": act_type,
        "properties": properties,
    }
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _create_activator_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_activator_type(
        name=arguments["name"],
        code=arguments.get("code", "# Print all built-in variables and functions for help\nprint_help()"),
        description=arguments.get("description", ""),
        version=arguments.get("version", "1.0"),
        folder_id=arguments.get("folder_id"),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_activator_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    type_id = arguments.pop("type_id")
    result = await client.update_activator_type(type_id, **arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_activator_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_activator_type(type_id=arguments["type_id"])
    return [TextContent(type="text", text="Activator type deleted successfully")]


async def _list_activator_type_properties(client: GimsClient, arguments: dict) -> list[TextContent]:
    properties = await client.list_activator_type_properties(activator_type_id=arguments["activator_type_id"])
    response = check_response_size({"properties": properties})
    return [TextContent(type="text", text=response)]


async def _create_activator_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_activator_type_property(**arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_activator_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    property_id = arguments.pop("property_id")
    result = await client.update_activator_type_property(property_id, **arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_activator_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_activator_type_property(property_id=arguments["property_id"])
    return [TextContent(type="text", text="Property deleted successfully")]


async def _search_activator_types(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Search activator types by name and/or code."""
    query = arguments["query"]
    search_in = arguments.get("search_in", "name")  # Default to name search
    case_sensitive = arguments.get("case_sensitive", False)

    results = []
    found_ids = set()

    # Search by name (default)
    if search_in in ("name", "both"):
        types = await client.list_activator_types()
        name_results = search_in_code(
            types,
            query,
            code_field="name",
            case_sensitive=case_sensitive,
        )
        for r in name_results:
            if r.get("id") not in found_ids:
                # Remove code from results
                r_no_code = {k: v for k, v in r.items() if k != "code"}
                results.append(r_no_code)
                found_ids.add(r.get("id"))

    # Search by code
    if search_in in ("code", "both"):
        types = await client.list_activator_types()
        # Need to get full types with code
        for t in types:
            if t["id"] in found_ids:
                continue
            full_type = await client.get_activator_type(t["id"])
            code_results = search_in_code(
                [full_type],
                query,
                code_field="code",
                case_sensitive=case_sensitive,
            )
            if code_results:
                r = code_results[0]
                # Remove code from results
                r_no_code = {k: v for k, v in r.items() if k != "code"}
                r_no_code["matched_in"] = "code"
                results.append(r_no_code)
                found_ids.add(t["id"])

    response = check_response_size({"results": results, "count": len(results)})
    return [TextContent(type="text", text=response)]
