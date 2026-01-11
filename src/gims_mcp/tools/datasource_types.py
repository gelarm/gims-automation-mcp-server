"""MCP Tools for DataSource Types."""

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
            "get_datasource_type_method": _get_datasource_type_method,
            "create_datasource_type_method": _create_datasource_type_method,
            "update_datasource_type_method": _update_datasource_type_method,
            "delete_datasource_type_method": _delete_datasource_type_method,
            "list_method_parameters": _list_method_parameters,
            "create_method_parameter": _create_method_parameter,
            "update_method_parameter": _update_method_parameter,
            "delete_method_parameter": _delete_method_parameter,
            "search_datasource_types": _search_datasource_types,
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
            description="Get a datasource type. Use include_properties=false and include_methods=false to get only basic type info (useful when full response is too large)",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_id": {"type": "integer", "description": "Type ID"},
                    "include_properties": {"type": "boolean", "description": "Include properties (default: true)"},
                    "include_methods": {"type": "boolean", "description": "Include methods with code (default: true)"},
                },
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
            description="Create a new property for a datasource type. Property is accessed in method code via self.property_label",
            inputSchema={
                "type": "object",
                "properties": {
                    "mds_type_id": {"type": "integer", "description": "Datasource type ID"},
                    "name": {"type": "string", "description": "Property display name"},
                    "label": {"type": "string", "description": "Property label - variable name in code (snake_case, English). Access via self.label"},
                    "value_type_id": {"type": "integer", "description": "Value type ID (use list_value_types). IMPORTANT: Do NOT use 'Список' or 'Справочник' types - use 'Объект' instead"},
                    "section_name_id": {"type": "integer", "description": "Section ID (use list_property_sections)"},
                    "description": {"type": "string", "description": "Description"},
                    "default_value": {"type": "string", "description": "Default value"},
                    "is_required": {"type": "boolean", "description": "Is required (default: false)"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden (default: false)"},
                    "default_dict_value_id": {"type": ["integer", "null"], "description": "Default dictionary value ID (for dictionary properties)"},
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
            description="List all methods of a datasource type (without code, use get_datasource_type_method for full code)",
            inputSchema={
                "type": "object",
                "properties": {"mds_type_id": {"type": "integer", "description": "Datasource type ID"}},
                "required": ["mds_type_id"],
            },
        ),
        Tool(
            name="get_datasource_type_method",
            description="Get a single method with its full code and parameters",
            inputSchema={
                "type": "object",
                "properties": {"method_id": {"type": "integer", "description": "Method ID"}},
                "required": ["method_id"],
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
            description="Create input or output parameter for a datasource type method. Input parameters (input_type=true) are passed when calling the method. Output parameters (input_type=false) are returned as dict from the method.",
            inputSchema={
                "type": "object",
                "properties": {
                    "method_id": {"type": "integer", "description": "Method ID"},
                    "label": {"type": "string", "description": "Parameter label - variable name in method code (snake_case, English)"},
                    "value_type_id": {"type": "integer", "description": "Value type ID (use list_value_types). IMPORTANT: Do NOT use 'Список' or 'Справочник' types - use 'Объект' instead"},
                    "input_type": {"type": "boolean", "description": "true = INPUT parameter (passed to method), false = OUTPUT parameter (returned from method as dict key)"},
                    "default_value": {"type": "string", "description": "Default value"},
                    "description": {"type": "string", "description": "Description"},
                    "is_hidden": {"type": "boolean", "description": "Is hidden"},
                    "default_dict_value_id": {"type": ["integer", "null"], "description": "Default dictionary value ID (for dictionary properties)"},
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
            name="search_datasource_types",
            description="Search datasource types by name and/or method code. Default searches by name only.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (substring or regex)"},
                    "search_in": {
                        "type": "string",
                        "description": "Where to search: 'name' (default), 'code' (method code), or 'both'",
                        "enum": ["name", "code", "both"],
                    },
                    "case_sensitive": {"type": "boolean", "description": "Case-sensitive search (default: false)"},
                },
                "required": ["query"],
            },
        ),
    ]


# Handler implementations

async def _list_datasource_type_folders(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_datasource_type_folders()
    folders_with_paths = build_folder_paths(folders)
    response = check_response_size({"folders": folders_with_paths})
    return [TextContent(type="text", text=response)]


async def _create_datasource_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type_folder(
        name=arguments["name"],
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_datasource_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.update_datasource_type_folder(
        folder_id=arguments["folder_id"],
        name=arguments.get("name"),
        parent_folder_id=arguments.get("parent_folder_id"),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_datasource_type_folder(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type_folder(folder_id=arguments["folder_id"])
    return [TextContent(type="text", text="Folder deleted successfully")]


async def _list_datasource_types(client: GimsClient, arguments: dict) -> list[TextContent]:
    folders = await client.list_datasource_type_folders()
    folders_with_paths = build_folder_paths(folders)
    types = await client.list_datasource_types()
    types_with_paths = build_item_paths(types, folders_with_paths, folder_id_field="folder")
    response = check_response_size({"types": types_with_paths})
    return [TextContent(type="text", text=response)]


async def _get_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    type_id = arguments["type_id"]
    include_properties = arguments.get("include_properties", True)
    include_methods = arguments.get("include_methods", True)

    ds_type = await client.get_datasource_type(type_id)
    result = {"type": ds_type}

    if include_properties:
        properties = await client.list_datasource_type_properties(type_id)
        result["properties"] = properties

    if include_methods:
        methods = await client.list_datasource_type_methods(type_id)
        # Get parameters for each method
        for method in methods:
            method["parameters"] = await client.list_method_parameters(method["id"])
        result["methods"] = methods

    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _create_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type(
        name=arguments["name"],
        description=arguments.get("description", ""),
        version=arguments.get("version", "1.0"),
        folder_id=arguments.get("folder_id"),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    type_id = arguments.pop("type_id")
    result = await client.update_datasource_type(type_id, **arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type(type_id=arguments["type_id"])
    return [TextContent(type="text", text="Datasource type deleted successfully")]


async def _list_datasource_type_properties(client: GimsClient, arguments: dict) -> list[TextContent]:
    properties = await client.list_datasource_type_properties(mds_type_id=arguments["mds_type_id"])
    response = check_response_size({"properties": properties})
    return [TextContent(type="text", text=response)]


async def _create_datasource_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type_property(**arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_datasource_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    property_id = arguments.pop("property_id")
    result = await client.update_datasource_type_property(property_id, **arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_datasource_type_property(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type_property(property_id=arguments["property_id"])
    return [TextContent(type="text", text="Property deleted successfully")]


async def _list_datasource_type_methods(client: GimsClient, arguments: dict) -> list[TextContent]:
    methods = await client.list_datasource_type_methods(mds_type_id=arguments["mds_type_id"])
    # Remove code from list to reduce size
    methods_no_code = [{k: v for k, v in m.items() if k != "code"} for m in methods]
    response = check_response_size({"methods": methods_no_code})
    return [TextContent(type="text", text=response)]


async def _get_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    method_id = arguments["method_id"]
    method = await client.get_datasource_type_method(method_id)
    parameters = await client.list_method_parameters(method_id)
    result = {
        "method": method,
        "parameters": parameters,
    }
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _create_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_datasource_type_method(
        mds_type_id=arguments["mds_type_id"],
        name=arguments["name"],
        label=arguments["label"],
        code=arguments.get("code", "# Method code\npass"),
        description=arguments.get("description", ""),
    )
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    method_id = arguments.pop("method_id")
    result = await client.update_datasource_type_method(method_id, **arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_datasource_type_method(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_datasource_type_method(method_id=arguments["method_id"])
    return [TextContent(type="text", text="Method deleted successfully")]


async def _list_method_parameters(client: GimsClient, arguments: dict) -> list[TextContent]:
    parameters = await client.list_method_parameters(method_id=arguments["method_id"])
    response = check_response_size({"parameters": parameters})
    return [TextContent(type="text", text=response)]


async def _create_method_parameter(client: GimsClient, arguments: dict) -> list[TextContent]:
    result = await client.create_method_parameter(**arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _update_method_parameter(client: GimsClient, arguments: dict) -> list[TextContent]:
    parameter_id = arguments.pop("parameter_id")
    result = await client.update_method_parameter(parameter_id, **arguments)
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


async def _delete_method_parameter(client: GimsClient, arguments: dict) -> list[TextContent]:
    await client.delete_method_parameter(parameter_id=arguments["parameter_id"])
    return [TextContent(type="text", text="Parameter deleted successfully")]


async def _search_datasource_types(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Search datasource types by name and/or method code."""
    query = arguments["query"]
    search_in = arguments.get("search_in", "name")  # Default to name search
    case_sensitive = arguments.get("case_sensitive", False)

    results = []
    found_ids = set()

    # Search by name (default)
    if search_in in ("name", "both"):
        types = await client.list_datasource_types()
        name_results = search_in_code(
            types,
            query,
            code_field="name",
            case_sensitive=case_sensitive,
        )
        for r in name_results:
            if r.get("id") not in found_ids:
                results.append(r)
                found_ids.add(r.get("id"))

    # Search by method code
    if search_in in ("code", "both"):
        types = await client.list_datasource_types()
        for ds_type in types:
            if ds_type["id"] in found_ids:
                continue
            methods = await client.list_datasource_type_methods(ds_type["id"])
            method_results = search_in_code(
                methods,
                query,
                code_field="code",
                case_sensitive=case_sensitive,
            )
            if method_results:
                # Return type info with matched methods (without full code)
                result = {
                    "id": ds_type["id"],
                    "name": ds_type["name"],
                    "description": ds_type.get("description", ""),
                    "matched_in": "code",
                    "matched_methods": [
                        {"id": m["id"], "name": m["name"], "match_count": m["match_count"]}
                        for m in method_results
                    ],
                }
                results.append(result)
                found_ids.add(ds_type["id"])

    response = check_response_size({"results": results, "count": len(results)})
    return [TextContent(type="text", text=response)]
