"""MCP Tools for DataSource Types."""

import json
from mcp.server import Server
from mcp.types import Tool, TextContent

from ..client import GimsClient, GimsApiError
from ..utils import build_folder_paths, build_item_paths, search_in_code, format_error


def register_datasource_type_tools(server: Server, client: GimsClient) -> None:
    """Register all datasource type-related tools with the MCP server."""
    # Tools are registered via get_datasource_type_tools() and handled in server.py
    pass


async def handle_datasource_type_tool(name: str, arguments: dict, client: GimsClient) -> list[TextContent] | None:
    """Handle datasource type tool calls. Returns None if tool not handled."""
    try:
        handlers = {
            "list_datasource_type_folders": _list_datasource_type_folders,
            "create_datasource_type_folder": _create_datasource_type_folder,
            "update_datasource_type_folder": _update_datasource_type_folder,
            "delete_datasource_type_folder": _delete_datasource_type_folder,
            "list_datasource_types": _list_datasource_types,
            "get_datasource_type": _get_datasource_type,
            "create_datasource_type": _create_datasource_type,
            "update_datasource_type": _update_datasource_type,
            "delete_datasource_type": _delete_datasource_type,
            "list_datasource_type_properties": _list_datasource_type_properties,
            "create_datasource_type_property": _create_datasource_type_property,
            "update_datasource_type_property": _update_datasource_type_property,
            "delete_datasource_type_property": _delete_datasource_type_property,
            "list_datasource_type_methods": _list_datasource_type_methods,
            "create_datasource_type_method": _create_datasource_type_method,
            "update_datasource_type_method": _update_datasource_type_method,
            "delete_datasource_type_method": _delete_datasource_type_method,
            "list_method_parameters": _list_method_parameters,
            "create_method_parameter": _create_method_parameter,
            "update_method_parameter": _update_method_parameter,
            "delete_method_parameter": _delete_method_parameter,
            "search_datasource_type_code": _search_datasource_type_code,
        }
        if name in handlers:
            return await handlers[name](client, arguments)
    except GimsApiError as e:
        return [TextContent(type="text", text=f"Error: {e.message}\nDetail: {e.detail}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {format_error(e)}")]
    return None


def get_datasource_type_tools() -> list[Tool]:
    """Get the list of datasource type tools."""
    return [
        # Folders
        Tool(
            name="list_datasource_type_folders",
            description="List all datasource type folders with their hierarchy paths",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="create_datasource_type_folder",
            description="Create a new datasource type folder",
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
            name="update_datasource_type_folder",
            description="Update a datasource type folder",
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
            name="delete_datasource_type_folder",
            description="Delete a datasource type folder",
            inputSchema={
                "type": "object",
                "properties": {"folder_id": {"type": "integer", "description": "Folder ID"}},
                "required": ["folder_id"],
            },
        ),
        # Types
        Tool(
            name="list_datasource_types",
            description="List all datasource types",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_datasource_type",
            description="Get a datasource type with its properties and methods",
            inputSchema={
                "type": "object",
                "properties": {"type_id": {"type": "integer", "description": "Type ID"}},
                "required": ["type_id"],
            },
        ),
        Tool(
            name="create_datasource_type",
            description="Create a new datasource type",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Type name"},
                    "description": {"type": "string", "description": "Description"},
                    "version": {"type": "string", "description": "Version (default: 1.0)"},
                    "folder_id": {"type": "integer", "description": "Folder ID (optional)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="update_datasource_type",
            description="Update a datasource type",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_id": {"type": "integer", "description": "Type ID"},
                    "name": {"type": "string", "description": "New name"},
                    "description": {"type": "string", "description": "New description"},
                    "version": {"type": "string", "description": "New version"},
                    "folder_id": {"type": "integer", "description": "New folder ID"},
                },
                "required": ["type_id"],
            },
        ),
        Tool(
            name="delete_datasource_type",
            description="Delete a datasource type",
            inputSchema={
                "type": "object",
                "properties": {"type_id": {"type": "integer", "description": "Type ID"}},
                "required": ["type_id"],
            },
        ),
        # Properties
        Tool(
            name="list_datasource_type_properties",
            description="List all properties of a datasource type",
            inputSchema={
                "type": "object",
                "properties": {"mds_type_id": {"type": "integer", "description": "Datasource type ID"}},
                "required": ["mds_type_id"],
            },
        ),
        Tool(
            name="create_datasource_type_property",
            description="Create a new property for a datasource type",
            inputSchema={
                "type": "object",
                "properties": {
                    "mds_type_id": {"type": "integer", "description": "Datasource type ID"},
                    "name": {"type": "string", "description": "Property name"},
                    "label": {"type": "string", "description": "Property label (code identifier, English only)"},
                    "value_type_id": {"type": "integer", "description": "Value type ID (use list_value_types to get IDs)"},
                    "section_name_id": {"type": "integer", "description": "Section ID (use list_property_sections to get IDs)"},
                    "description": {"type": "string", "description": "Description"},
                    "default_value": {"type": "string", "description": "Default value"},
                    "is_required": {"type": "boolean", "description": "Is required (default: false)"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden (default: false)"},
                },
                "required": ["mds_type_id", "name", "label", "value_type_id", "section_name_id"],
            },
        ),
        Tool(
            name="update_datasource_type_property",
            description="Update a datasource type property",
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
            name="delete_datasource_type_property",
            description="Delete a datasource type property",
            inputSchema={
                "type": "object",
                "properties": {"property_id": {"type": "integer", "description": "Property ID"}},
                "required": ["property_id"],
            },
        ),
        # Methods
        Tool(
            name="list_datasource_type_methods",
            description="List all methods of a datasource type",
            inputSchema={
                "type": "object",
                "properties": {"mds_type_id": {"type": "integer", "description": "Datasource type ID"}},
                "required": ["mds_type_id"],
            },
        ),
        Tool(
            name="create_datasource_type_method",
            description="Create a new method for a datasource type",
            inputSchema={
                "type": "object",
                "properties": {
                    "mds_type_id": {"type": "integer", "description": "Datasource type ID"},
                    "name": {"type": "string", "description": "Method name"},
                    "label": {"type": "string", "description": "Method label (code identifier, English only)"},
                    "code": {"type": "string", "description": "Python code for the method"},
                    "description": {"type": "string", "description": "Description"},
                },
                "required": ["mds_type_id", "name", "label"],
            },
        ),
        Tool(
            name="update_datasource_type_method",
            description="Update a datasource type method (including its code)",
            inputSchema={
                "type": "object",
                "properties": {
                    "method_id": {"type": "integer", "description": "Method ID"},
                    "name": {"type": "string", "description": "New name"},
                    "label": {"type": "string", "description": "New label"},
                    "code": {"type": "string", "description": "New Python code"},
                    "description": {"type": "string", "description": "New description"},
                },
                "required": ["method_id"],
            },
        ),
        Tool(
            name="delete_datasource_type_method",
            description="Delete a datasource type method",
            inputSchema={
                "type": "object",
                "properties": {"method_id": {"type": "integer", "description": "Method ID"}},
                "required": ["method_id"],
            },
        ),
        # Method Parameters
        Tool(
            name="list_method_parameters",
            description="List all parameters of a method",
            inputSchema={
                "type": "object",
                "properties": {"method_id": {"type": "integer", "description": "Method ID"}},
                "required": ["method_id"],
            },
        ),
        Tool(
            name="create_method_parameter",
            description="Create a new parameter for a method",
            inputSchema={
                "type": "object",
                "properties": {
                    "method_id": {"type": "integer", "description": "Method ID"},
                    "label": {"type": "string", "description": "Parameter label (code identifier)"},
                    "value_type_id": {"type": "integer", "description": "Value type ID"},
                    "input_type": {"type": "boolean", "description": "Is input parameter (true) or output (false)"},
                    "default_value": {"type": "string", "description": "Default value"},
                    "description": {"type": "string", "description": "Description"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden"},
                },
                "required": ["method_id", "label", "value_type_id"],
            },
        ),
        Tool(
            name="update_method_parameter",
            description="Update a method parameter",
            inputSchema={
                "type": "object",
                "properties": {
                    "parameter_id": {"type": "integer", "description": "Parameter ID"},
                    "label": {"type": "string", "description": "New label"},
                    "default_value": {"type": "string", "description": "New default value"},
                    "description": {"type": "string", "description": "New description"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden"},
                },
                "required": ["parameter_id"],
            },
        ),
        Tool(
            name="delete_method_parameter",
            description="Delete a method parameter",
            inputSchema={
                "type": "object",
                "properties": {"parameter_id": {"type": "integer", "description": "Parameter ID"}},
                "required": ["parameter_id"],
            },
        ),
        # Search
        Tool(
            name="search_datasource_type_code",
            description="Search for code in datasource type methods",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "case_sensitive": {"type": "boolean", "description": "Case-sensitive (default: false)"},
                },
                "required": ["query"],
            },
        ),
    ]


# Handler implementations

async def _list_datasource_type_folders(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_datasource_type_folders()
    folders_with_paths = build_folder_paths(folders)
    return [TextContent(type="text", text=json.dumps({"folders": folders_with_paths}, indent=2, ensure_ascii=False))]


async def _create_datasource_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type_folder(
        name=arguments["name"],
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_datasource_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.update_datasource_type_folder(
        folder_id=arguments["folder_id"],
        name=arguments.get("name"),
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_datasource_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type_folder(folder_id=arguments["folder_id"])
    return [TextContent(type="text", text="Folder deleted successfully")]


async def _list_datasource_types(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_datasource_type_folders()
    folders_with_paths = build_folder_paths(folders)
    types = await client.list_datasource_types()
    types_with_paths = build_item_paths(types, folders_with_paths, folder_id_field="folder")
    return [TextContent(type="text", text=json.dumps({"types": types_with_paths}, indent=2, ensure_ascii=False))]


async def _get_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    type_id = arguments["type_id"]
    ds_type = await client.get_datasource_type(type_id)
    properties = await client.list_datasource_type_properties(type_id)
    methods = await client.list_datasource_type_methods(type_id)

    # Get parameters for each method
    for method in methods:
        method["parameters"] = await client.list_method_parameters(method["id"])

    result = {
        "type": ds_type,
        "properties": properties,
        "methods": methods,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _create_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type(
        name=arguments["name"],
        description=arguments.get("description", ""),
        version=arguments.get("version", "1.0"),
        folder_id=arguments.get("folder_id"),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    type_id = arguments.pop("type_id")
    result = await client.update_datasource_type(type_id, **arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type(type_id=arguments["type_id"])
    return [TextContent(type="text", text="Datasource type deleted successfully")]


async def _list_datasource_type_properties(client: GimsClient, arguments: dict) -> list[TextContent]:
    properties = await client.list_datasource_type_properties(mds_type_id=arguments["mds_type_id"])
    return [TextContent(type="text", text=json.dumps({"properties": properties}, indent=2, ensure_ascii=False))]


async def _create_datasource_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type_property(**arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_datasource_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    property_id = arguments.pop("property_id")
    result = await client.update_datasource_type_property(property_id, **arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_datasource_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type_property(property_id=arguments["property_id"])
    return [TextContent(type="text", text="Property deleted successfully")]


async def _list_datasource_type_methods(client: GimsClient, arguments: dict) -> list[TextContent]:
    methods = await client.list_datasource_type_methods(mds_type_id=arguments["mds_type_id"])
    return [TextContent(type="text", text=json.dumps({"methods": methods}, indent=2, ensure_ascii=False))]


async def _create_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type_method(
        mds_type_id=arguments["mds_type_id"],
        name=arguments["name"],
        label=arguments["label"],
        code=arguments.get("code", "# Method code\npass"),
        description=arguments.get("description", ""),
    )
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    method_id = arguments.pop("method_id")
    result = await client.update_datasource_type_method(method_id, **arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type_method(method_id=arguments["method_id"])
    return [TextContent(type="text", text="Method deleted successfully")]


async def _list_method_parameters(client: GimsClient, arguments: dict) -> list[TextContent]:
    parameters = await client.list_method_parameters(method_id=arguments["method_id"])
    return [TextContent(type="text", text=json.dumps({"parameters": parameters}, indent=2, ensure_ascii=False))]


async def _create_method_parameter(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_method_parameter(**arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _update_method_parameter(client: GimsClient, arguments: dict) -> list[TextContent]:
    parameter_id = arguments.pop("parameter_id")
    result = await client.update_method_parameter(parameter_id, **arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


async def _delete_method_parameter(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_method_parameter(parameter_id=arguments["parameter_id"])
    return [TextContent(type="text", text="Parameter deleted successfully")]


async def _search_datasource_type_code(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Search in method code - done locally."""
    types = await client.list_datasource_types()
    all_methods = []
    for ds_type in types:
        methods = await client.list_datasource_type_methods(ds_type["id"])
        for method in methods:
            method["type_id"] = ds_type["id"]
            method["type_name"] = ds_type["name"]
        all_methods.extend(methods)

    results = search_in_code(
        all_methods,
        arguments["query"],
        code_field="code",
        case_sensitive=arguments.get("case_sensitive", False),
    )
    return [TextContent(type="text", text=json.dumps({"results": results}, indent=2, ensure_ascii=False))]
