"""MCP Tools for synchronization with Git."""

from datetime import datetime

import yaml
from mcp.types import Tool, TextContent

from ..client import GimsClient, GimsApiError
from ..serializers import (
    serialize_script,
    serialize_datasource_type,
    serialize_activator_type,
    deserialize_datasource_type,
    deserialize_activator_type,
)
from ..validators import validate_python_syntax
from ..utils import check_response_size, format_error, ResponseTooLargeError


def get_sync_tools() -> list[Tool]:
    """Get the list of sync tools for Git integration."""
    return [
        Tool(
            name="export_script",
            description="Export a script from GIMS to Git format (meta.yaml + code.py)",
            inputSchema={
                "type": "object",
                "properties": {
                    "script_id": {"type": "integer", "description": "Script ID"},
                    "script_name": {"type": "string", "description": "Script name (alternative to ID)"},
                },
            },
        ),
        Tool(
            name="import_script",
            description="Import a script to GIMS from Git format. Validates Python syntax before import.",
            inputSchema={
                "type": "object",
                "properties": {
                    "meta_yaml": {"type": "string", "description": "Content of meta.yaml"},
                    "code": {"type": "string", "description": "Python code of the script"},
                    "target_name": {"type": "string", "description": "Name to use if different from meta"},
                    "target_folder_id": {"type": "integer", "description": "Folder ID to save to"},
                    "update_existing": {"type": "boolean", "description": "Update existing script", "default": False},
                },
                "required": ["meta_yaml", "code"],
            },
        ),
        Tool(
            name="export_datasource_type",
            description="Export a datasource type with all properties and methods",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_id": {"type": "integer", "description": "Datasource type ID"},
                    "type_name": {"type": "string", "description": "Datasource type name (alternative to ID)"},
                },
            },
        ),
        Tool(
            name="import_datasource_type",
            description="Import a datasource type from Git format",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "object",
                        "description": "Dictionary of files: {'meta.yaml': ..., 'properties.yaml': ..., 'methods/X/...': ...}",
                    },
                    "target_name": {"type": "string", "description": "Name to use if different from meta"},
                    "update_existing": {"type": "boolean", "description": "Update existing type", "default": False},
                },
                "required": ["files"],
            },
        ),
        Tool(
            name="export_activator_type",
            description="Export an activator type with properties and code",
            inputSchema={
                "type": "object",
                "properties": {
                    "type_id": {"type": "integer", "description": "Activator type ID"},
                    "type_name": {"type": "string", "description": "Activator type name (alternative to ID)"},
                },
            },
        ),
        Tool(
            name="import_activator_type",
            description="Import an activator type from Git format",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "object",
                        "description": "Dictionary of files: {'meta.yaml': ..., 'code.py': ..., 'properties.yaml': ...}",
                    },
                    "target_name": {"type": "string", "description": "Name to use if different from meta"},
                    "update_existing": {"type": "boolean", "description": "Update existing type", "default": False},
                },
                "required": ["files"],
            },
        ),
        Tool(
            name="validate_python_code",
            description="Validate Python code syntax using ast.parse()",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to validate"},
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="compare_with_git",
            description="Compare a GIMS component with its Git version (by updated_at)",
            inputSchema={
                "type": "object",
                "properties": {
                    "component_type": {
                        "type": "string",
                        "enum": ["script", "datasource_type", "activator_type"],
                        "description": "Component type",
                    },
                    "gims_name": {"type": "string", "description": "Component name in GIMS"},
                    "git_exported_at": {"type": "string", "description": "Export date from Git meta.yaml"},
                },
                "required": ["component_type", "gims_name", "git_exported_at"],
            },
        ),
    ]


async def handle_sync_tool(name: str, arguments: dict, client: GimsClient) -> list[TextContent] | None:
    """Handle sync tool calls. Returns None if tool not handled."""
    try:
        handlers = {
            "export_script": _export_script,
            "import_script": _import_script,
            "export_datasource_type": _export_datasource_type,
            "import_datasource_type": _import_datasource_type,
            "export_activator_type": _export_activator_type,
            "import_activator_type": _import_activator_type,
            "validate_python_code": _validate_python_code,
            "compare_with_git": _compare_with_git,
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


# ==================== Export Script ====================


async def _export_script(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Export a script to Git format."""
    script_id = arguments.get("script_id")
    script_name = arguments.get("script_name")

    if script_id:
        script = await client.get_script(script_id)
    elif script_name:
        scripts = await client.list_scripts()
        script = next((s for s in scripts if s["name"] == script_name), None)
        if not script:
            return [TextContent(type="text", text=f"Error: Скрипт '{script_name}' не найден")]
        script = await client.get_script(script["id"])
    else:
        return [TextContent(type="text", text="Error: Укажите script_id или script_name")]

    meta_yaml, code = serialize_script(script, client.config.url)
    result = {
        "files": {
            "meta.yaml": meta_yaml,
            "code.py": code,
        },
        "suggested_folder": script["name"].lower().replace(" ", "_"),
    }
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Import Script ====================


async def _import_script(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Import a script from Git format."""
    meta_yaml = arguments["meta_yaml"]
    code = arguments["code"]
    target_name = arguments.get("target_name")
    target_folder_id = arguments.get("target_folder_id")
    update_existing = arguments.get("update_existing", False)

    # Validate Python syntax
    is_valid, error = validate_python_syntax(code)
    if not is_valid:
        return [TextContent(type="text", text=f"Error: Ошибка синтаксиса Python: {error}")]

    # Parse metadata
    meta = yaml.safe_load(meta_yaml)
    name = target_name or meta.get("name", "Unnamed Script")

    # Check if exists
    scripts = await client.list_scripts()
    existing = next((s for s in scripts if s["name"] == name), None)

    if existing and not update_existing:
        result = {
            "error": f"Скрипт '{name}' уже существует",
            "existing_id": existing["id"],
            "suggestion": "Используйте target_name для создания с другим именем или update_existing=true",
        }
        response = check_response_size(result)
        return [TextContent(type="text", text=response)]

    if existing and update_existing:
        await client.update_script(existing["id"], code=code)
        result = {"action": "updated", "script_id": existing["id"], "name": name}
    else:
        created = await client.create_script(name=name, code=code, folder_id=target_folder_id)
        result = {"action": "created", "script_id": created["id"], "name": name}

    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Export Datasource Type ====================


async def _export_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Export a datasource type to Git format."""
    type_id = arguments.get("type_id")
    type_name = arguments.get("type_name")

    if type_id:
        ds_type = await client.get_datasource_type(type_id)
    elif type_name:
        ds_types = await client.list_datasource_types()
        ds_type = next((t for t in ds_types if t["name"] == type_name), None)
        if not ds_type:
            return [TextContent(type="text", text=f"Error: Тип ИД '{type_name}' не найден")]
        ds_type = await client.get_datasource_type(ds_type["id"])
    else:
        return [TextContent(type="text", text="Error: Укажите type_id или type_name")]

    # Get properties
    properties = await client.list_datasource_type_properties(ds_type["id"])
    ds_type["properties"] = properties

    # Get methods with parameters
    methods = await client.list_datasource_type_methods(ds_type["id"])
    for method in methods:
        params = await client.list_method_parameters(method["id"])
        method["parameters"] = params
    ds_type["methods"] = methods

    files = serialize_datasource_type(ds_type, client.config.url)
    result = {
        "files": files,
        "suggested_folder": ds_type["name"].lower().replace(" ", "_"),
    }
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Import Helpers ====================


async def _resolve_reference_ids(client: GimsClient) -> tuple[dict[str, int], dict[str, int]]:
    """Get name -> id mappings for value_types and sections."""
    value_types = await client.list_value_types()
    sections = await client.list_property_sections()

    vt_map = {vt["name"]: vt["id"] for vt in value_types}
    sec_map = {s["name"]: s["id"] for s in sections}

    return vt_map, sec_map


async def _import_properties(
    client: GimsClient,
    type_id: int,
    properties: list[dict],
    is_datasource: bool,
    vt_map: dict[str, int],
    sec_map: dict[str, int],
) -> dict:
    """Import properties for a datasource or activator type.

    Args:
        client: GIMS API client.
        type_id: ID of the datasource or activator type.
        properties: List of property data from deserialized Git files.
        is_datasource: True for datasource type, False for activator type.
        vt_map: value_type name -> id mapping.
        sec_map: section name -> id mapping.

    Returns:
        Import result dict with created/skipped counts and errors.
    """
    result = {"created": 0, "skipped": 0, "errors": []}

    for prop in properties:
        name = prop.get("name", "")
        label = prop.get("label", name)
        value_type_name = prop.get("value_type", "")
        section_name = prop.get("section", "Основные")

        # Resolve value_type_id
        value_type_id = vt_map.get(value_type_name)
        if value_type_id is None:
            result["skipped"] += 1
            result["errors"].append(f"Property '{name}': unknown value_type '{value_type_name}'")
            continue

        # Resolve section_id
        section_id = sec_map.get(section_name)
        if section_id is None:
            result["skipped"] += 1
            result["errors"].append(f"Property '{name}': unknown section '{section_name}'")
            continue

        try:
            if is_datasource:
                await client.create_datasource_type_property(
                    mds_type_id=type_id,
                    name=name,
                    label=label,
                    value_type_id=value_type_id,
                    section_name_id=section_id,
                    description=prop.get("description", ""),
                    default_value=prop.get("default_value", ""),
                    is_required=prop.get("is_required", False),
                    is_hidden=prop.get("is_hidden", False),
                )
            else:
                await client.create_activator_type_property(
                    activator_type_id=type_id,
                    name=name,
                    label=label,
                    value_type_id=value_type_id,
                    section_name_id=section_id,
                    description=prop.get("description", ""),
                    default_value=prop.get("default_value", ""),
                    is_required=prop.get("is_required", False),
                    is_hidden=prop.get("is_hidden", False),
                )
            result["created"] += 1
        except GimsApiError as e:
            result["skipped"] += 1
            result["errors"].append(f"Property '{name}': {e.message}")

    return result


async def _import_methods(
    client: GimsClient,
    type_id: int,
    methods: list[dict],
    vt_map: dict[str, int],
) -> dict:
    """Import methods and their parameters for a datasource type.

    Args:
        client: GIMS API client.
        type_id: ID of the datasource type.
        methods: List of method data from deserialized Git files.
        vt_map: value_type name -> id mapping.

    Returns:
        Import result dict with created counts and errors.
    """
    result = {"created": 0, "parameters_created": 0, "errors": []}

    for method in methods:
        name = method.get("name", "")
        label = method.get("label", name)
        code = method.get("code", "# No code")
        description = method.get("description", "")

        try:
            created_method = await client.create_datasource_type_method(
                mds_type_id=type_id,
                name=name,
                label=label,
                code=code,
                description=description,
            )
            result["created"] += 1

            # Import parameters for this method
            method_id = created_method["id"]
            for param in method.get("parameters", []):
                param_label = param.get("label", "")
                value_type_name = param.get("value_type", "")

                # Resolve value_type_id
                value_type_id = vt_map.get(value_type_name)
                if value_type_id is None:
                    result["errors"].append(
                        f"Method '{label}' param '{param_label}': unknown value_type '{value_type_name}'"
                    )
                    continue

                try:
                    await client.create_method_parameter(
                        method_id=method_id,
                        label=param_label,
                        value_type_id=value_type_id,
                        input_type=param.get("input_type", True),
                        default_value=param.get("default_value", ""),
                        description=param.get("description", ""),
                        is_hidden=param.get("is_hidden", False),
                    )
                    result["parameters_created"] += 1
                except GimsApiError as e:
                    result["errors"].append(f"Method '{label}' param '{param_label}': {e.message}")

        except GimsApiError as e:
            result["errors"].append(f"Method '{label}': {e.message}")

    return result


# ==================== Import Datasource Type ====================


async def _import_datasource_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Import a datasource type from Git format."""
    files = arguments["files"]
    target_name = arguments.get("target_name")
    update_existing = arguments.get("update_existing", False)

    # Deserialize
    data = deserialize_datasource_type(files)
    name = target_name or data.get("name", "Unnamed Type")

    # Validate method codes
    for method in data.get("methods", []):
        is_valid, error = validate_python_syntax(method.get("code", ""))
        if not is_valid:
            return [TextContent(
                type="text",
                text=f"Error: Ошибка синтаксиса в методе '{method.get('label', 'unknown')}': {error}",
            )]

    # Check if exists
    ds_types = await client.list_datasource_types()
    existing = next((t for t in ds_types if t["name"] == name), None)

    if existing and not update_existing:
        result = {
            "error": f"Тип ИД '{name}' уже существует",
            "existing_id": existing["id"],
            "suggestion": "Используйте target_name для создания с другим именем или update_existing=true",
        }
        response = check_response_size(result)
        return [TextContent(type="text", text=response)]

    # Create or update base type
    if existing and update_existing:
        await client.update_datasource_type(
            existing["id"],
            description=data.get("description"),
            version=data.get("version"),
        )
        type_id = existing["id"]
        action = "updated"
    else:
        created = await client.create_datasource_type(
            name=name,
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
        )
        type_id = created["id"]
        action = "created"

    # Resolve reference IDs for properties and methods
    vt_map, sec_map = await _resolve_reference_ids(client)

    # Import properties
    properties_result = await _import_properties(
        client=client,
        type_id=type_id,
        properties=data.get("properties", []),
        is_datasource=True,
        vt_map=vt_map,
        sec_map=sec_map,
    )

    # Import methods (only for new types or if update_existing)
    methods_result = await _import_methods(
        client=client,
        type_id=type_id,
        methods=data.get("methods", []),
        vt_map=vt_map,
    )

    result = {
        "action": action,
        "type_id": type_id,
        "name": name,
        "properties": properties_result,
        "methods": methods_result,
    }

    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Export Activator Type ====================


async def _export_activator_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Export an activator type to Git format."""
    type_id = arguments.get("type_id")
    type_name = arguments.get("type_name")

    if type_id:
        act_type = await client.get_activator_type(type_id)
    elif type_name:
        act_types = await client.list_activator_types()
        act_type = next((t for t in act_types if t["name"] == type_name), None)
        if not act_type:
            return [TextContent(type="text", text=f"Error: Тип активатора '{type_name}' не найден")]
        act_type = await client.get_activator_type(act_type["id"])
    else:
        return [TextContent(type="text", text="Error: Укажите type_id или type_name")]

    # Get properties
    properties = await client.list_activator_type_properties(act_type["id"])
    act_type["properties"] = properties

    files = serialize_activator_type(act_type, client.config.url)
    result = {
        "files": files,
        "suggested_folder": act_type["name"].lower().replace(" ", "_"),
    }
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Import Activator Type ====================


async def _import_activator_type(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Import an activator type from Git format."""
    files = arguments["files"]
    target_name = arguments.get("target_name")
    update_existing = arguments.get("update_existing", False)

    # Deserialize
    data = deserialize_activator_type(files)
    name = target_name or data.get("name", "Unnamed Type")
    code = data.get("code", "# No code")

    # Validate code
    is_valid, error = validate_python_syntax(code)
    if not is_valid:
        return [TextContent(type="text", text=f"Error: Ошибка синтаксиса Python: {error}")]

    # Check if exists
    act_types = await client.list_activator_types()
    existing = next((t for t in act_types if t["name"] == name), None)

    if existing and not update_existing:
        result = {
            "error": f"Тип активатора '{name}' уже существует",
            "existing_id": existing["id"],
            "suggestion": "Используйте target_name для создания с другим именем или update_existing=true",
        }
        response = check_response_size(result)
        return [TextContent(type="text", text=response)]

    # Create or update base type
    if existing and update_existing:
        await client.update_activator_type(
            existing["id"],
            code=code,
            description=data.get("description"),
            version=data.get("version"),
        )
        type_id = existing["id"]
        action = "updated"
    else:
        created = await client.create_activator_type(
            name=name,
            code=code,
            description=data.get("description", ""),
            version=data.get("version", "1.0"),
        )
        type_id = created["id"]
        action = "created"

    # Resolve reference IDs for properties
    vt_map, sec_map = await _resolve_reference_ids(client)

    # Import properties
    properties_result = await _import_properties(
        client=client,
        type_id=type_id,
        properties=data.get("properties", []),
        is_datasource=False,
        vt_map=vt_map,
        sec_map=sec_map,
    )

    result = {
        "action": action,
        "type_id": type_id,
        "name": name,
        "properties": properties_result,
    }

    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Validate Python Code ====================


async def _validate_python_code(_client: GimsClient, arguments: dict) -> list[TextContent]:
    """Validate Python code syntax."""
    code = arguments["code"]
    is_valid, error = validate_python_syntax(code)
    result = {
        "valid": is_valid,
        "error": error,
    }
    response = check_response_size(result)
    return [TextContent(type="text", text=response)]


# ==================== Compare With Git ====================


async def _compare_with_git(client: GimsClient, arguments: dict) -> list[TextContent]:
    """Compare GIMS component with Git version."""
    component_type = arguments["component_type"]
    gims_name = arguments["gims_name"]
    git_exported_at = arguments["git_exported_at"]

    # Parse git date
    try:
        git_date = datetime.fromisoformat(git_exported_at.replace("Z", "+00:00"))
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: Неверный формат даты: {e}")]

    # Get component from GIMS
    if component_type == "script":
        components = await client.list_scripts()
        component = next((c for c in components if c["name"] == gims_name), None)
    elif component_type == "datasource_type":
        components = await client.list_datasource_types()
        component = next((c for c in components if c["name"] == gims_name), None)
    elif component_type == "activator_type":
        components = await client.list_activator_types()
        component = next((c for c in components if c["name"] == gims_name), None)
    else:
        return [TextContent(type="text", text=f"Error: Неизвестный тип компонента: {component_type}")]

    if not component:
        result = {
            "status": "not_found_in_gims",
            "recommendation": "import",
            "message": f"Компонент '{gims_name}' не найден в GIMS. Рекомендуется импорт.",
        }
        response = check_response_size(result)
        return [TextContent(type="text", text=response)]

    # Compare dates
    gims_updated_at = component.get("updated_at")
    if not gims_updated_at:
        result = {
            "status": "no_updated_at",
            "message": "Компонент в GIMS не имеет поля updated_at. Невозможно сравнить.",
            "recommendation": "manual_check",
        }
        response = check_response_size(result)
        return [TextContent(type="text", text=response)]

    try:
        gims_date = datetime.fromisoformat(gims_updated_at.replace("Z", "+00:00"))
    except ValueError:
        result = {
            "status": "invalid_gims_date",
            "message": f"Некорректный формат даты в GIMS: {gims_updated_at}",
            "recommendation": "manual_check",
        }
        response = check_response_size(result)
        return [TextContent(type="text", text=response)]

    if gims_date > git_date:
        result = {
            "status": "gims_newer",
            "gims_updated_at": gims_updated_at,
            "git_exported_at": git_exported_at,
            "recommendation": "export",
            "message": "Версия в GIMS новее. Рекомендуется экспорт в Git.",
        }
    elif gims_date < git_date:
        result = {
            "status": "git_newer",
            "gims_updated_at": gims_updated_at,
            "git_exported_at": git_exported_at,
            "recommendation": "import",
            "message": "Версия в Git новее. Рекомендуется импорт в GIMS.",
        }
    else:
        result = {
            "status": "in_sync",
            "gims_updated_at": gims_updated_at,
            "git_exported_at": git_exported_at,
            "message": "Версии синхронизированы.",
        }

    response = check_response_size(result)
    return [TextContent(type="text", text=response)]
