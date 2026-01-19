"""Serialization of GIMS components to YAML format for Git storage."""

from datetime import datetime, timezone

import yaml


def serialize_script(script_data: dict, gims_url: str) -> tuple[str, str]:
    """
    Serialize a script to meta.yaml and code.py format.

    Args:
        script_data: Script data from GIMS API.
        gims_url: GIMS instance URL for tracking export source.

    Returns:
        Tuple of (meta_yaml_content, code_content).
    """
    meta = {
        "name": script_data["name"],
        "description": script_data.get("description", ""),
        "version": "1.0",
        "gims_folder": script_data.get("folder_path", "/"),
        "code_file": "code.py",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_from": gims_url,
    }

    # Include updated_at if available for comparison
    if script_data.get("updated_at"):
        meta["gims_updated_at"] = script_data["updated_at"]

    return yaml.dump(meta, allow_unicode=True, default_flow_style=False), script_data.get("code", "")


def serialize_datasource_type(type_data: dict, gims_url: str) -> dict[str, str]:
    """
    Serialize a datasource type with all properties and methods.

    Args:
        type_data: Datasource type data from GIMS API (with properties and methods).
        gims_url: GIMS instance URL for tracking export source.

    Returns:
        Dictionary mapping file paths to their content:
        {
            'meta.yaml': ...,
            'properties.yaml': ...,
            'methods/<label>/meta.yaml': ...,
            'methods/<label>/code.py': ...,
            'methods/<label>/params.yaml': ...
        }
    """
    files = {}

    # meta.yaml
    meta = {
        "name": type_data["name"],
        "description": type_data.get("description", ""),
        "version": type_data.get("version", "1.0"),
        "gims_folder": type_data.get("folder_path", "/"),
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_from": gims_url,
    }
    if type_data.get("updated_at"):
        meta["gims_updated_at"] = type_data["updated_at"]
    files["meta.yaml"] = yaml.dump(meta, allow_unicode=True, default_flow_style=False)

    # properties.yaml
    props = {"properties": [serialize_property(p) for p in type_data.get("properties", [])]}
    files["properties.yaml"] = yaml.dump(props, allow_unicode=True, default_flow_style=False)

    # methods/
    for method in type_data.get("methods", []):
        method_folder = f"methods/{method['label']}"
        method_meta = {
            "name": method["name"],
            "label": method["label"],
            "description": method.get("description", ""),
            "code_file": "code.py",
            "params_file": "params.yaml",
        }
        if method.get("updated_at"):
            method_meta["gims_updated_at"] = method["updated_at"]
        files[f"{method_folder}/meta.yaml"] = yaml.dump(method_meta, allow_unicode=True, default_flow_style=False)
        files[f"{method_folder}/code.py"] = method.get("code", "# No code")

        params = {"parameters": [serialize_parameter(p) for p in method.get("parameters", [])]}
        files[f"{method_folder}/params.yaml"] = yaml.dump(params, allow_unicode=True, default_flow_style=False)

    return files


def serialize_activator_type(type_data: dict, gims_url: str) -> dict[str, str]:
    """
    Serialize an activator type with all properties and code.

    Args:
        type_data: Activator type data from GIMS API (with properties).
        gims_url: GIMS instance URL for tracking export source.

    Returns:
        Dictionary mapping file paths to their content:
        {
            'meta.yaml': ...,
            'code.py': ...,
            'properties.yaml': ...
        }
    """
    files = {}

    # meta.yaml
    meta = {
        "name": type_data["name"],
        "description": type_data.get("description", ""),
        "version": type_data.get("version", "1.0"),
        "gims_folder": type_data.get("folder_path", "/"),
        "code_file": "code.py",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_from": gims_url,
    }
    if type_data.get("updated_at"):
        meta["gims_updated_at"] = type_data["updated_at"]
    files["meta.yaml"] = yaml.dump(meta, allow_unicode=True, default_flow_style=False)

    # code.py
    files["code.py"] = type_data.get("code", "# No code")

    # properties.yaml
    props = {"properties": [serialize_property(p) for p in type_data.get("properties", [])]}
    files["properties.yaml"] = yaml.dump(props, allow_unicode=True, default_flow_style=False)

    return files


def serialize_property(prop: dict) -> dict:
    """
    Serialize a property for YAML export.

    Args:
        prop: Property data from GIMS API.

    Returns:
        Serialized property dictionary.
    """
    result = {
        "name": prop["name"],
        "label": prop["label"],
        "value_type": prop.get("value_type_name", prop.get("value_type", "")),
        "default_value": prop.get("default_value", ""),
        "section": prop.get("section_name", prop.get("section", "Основные")),
        "is_required": prop.get("is_required", False),
        "is_hidden": prop.get("is_hidden", False),
        "is_inner": prop.get("is_inner", False),
        "description": prop.get("description", ""),
    }
    if prop.get("updated_at"):
        result["gims_updated_at"] = prop["updated_at"]
    return result


def serialize_parameter(param: dict) -> dict:
    """
    Serialize a method parameter for YAML export.

    Args:
        param: Parameter data from GIMS API.

    Returns:
        Serialized parameter dictionary.
    """
    result = {
        "label": param["label"],
        "input_type": param.get("input_type", True),
        "value_type": param.get("value_type_name", param.get("value_type", "")),
        "default_value": param.get("default_value", ""),
        "description": param.get("description", ""),
        "is_hidden": param.get("is_hidden", False),
    }
    if param.get("updated_at"):
        result["gims_updated_at"] = param["updated_at"]
    return result


def deserialize_script(meta: dict, code: str) -> dict:
    """
    Deserialize script from Git format to GIMS API format.

    Args:
        meta: Parsed meta.yaml dictionary.
        code: Python code content.

    Returns:
        Dictionary suitable for GIMS API create/update.
    """
    return {
        "name": meta["name"],
        "code": code,
        "description": meta.get("description", ""),
    }


def deserialize_datasource_type(files: dict[str, str]) -> dict:
    """
    Deserialize datasource type from Git format to GIMS API format.

    Args:
        files: Dictionary mapping file paths to content.

    Returns:
        Dictionary suitable for GIMS API create/update.
    """
    meta = yaml.safe_load(files.get("meta.yaml", "{}"))
    props_data = yaml.safe_load(files.get("properties.yaml", "properties: []"))

    result = {
        "name": meta.get("name", ""),
        "description": meta.get("description", ""),
        "version": meta.get("version", "1.0"),
        "properties": props_data.get("properties", []),
        "methods": [],
    }

    # Parse methods from methods/<label>/ folders
    method_folders = set()
    for path in files.keys():
        if path.startswith("methods/") and "/" in path[8:]:
            label = path.split("/")[1]
            method_folders.add(label)

    for label in method_folders:
        method_meta_path = f"methods/{label}/meta.yaml"
        method_code_path = f"methods/{label}/code.py"
        method_params_path = f"methods/{label}/params.yaml"

        if method_meta_path in files:
            method_meta = yaml.safe_load(files[method_meta_path])
            method = {
                "name": method_meta.get("name", label),
                "label": method_meta.get("label", label),
                "description": method_meta.get("description", ""),
                "code": files.get(method_code_path, "# No code"),
                "parameters": [],
            }

            if method_params_path in files:
                params_data = yaml.safe_load(files[method_params_path])
                method["parameters"] = params_data.get("parameters", [])

            result["methods"].append(method)

    return result


def deserialize_activator_type(files: dict[str, str]) -> dict:
    """
    Deserialize activator type from Git format to GIMS API format.

    Args:
        files: Dictionary mapping file paths to content.

    Returns:
        Dictionary suitable for GIMS API create/update.
    """
    meta = yaml.safe_load(files.get("meta.yaml", "{}"))
    props_data = yaml.safe_load(files.get("properties.yaml", "properties: []"))

    return {
        "name": meta.get("name", ""),
        "description": meta.get("description", ""),
        "version": meta.get("version", "1.0"),
        "code": files.get("code.py", "# No code"),
        "properties": props_data.get("properties", []),
    }
