"""Validation utilities for Python code and YAML structures."""

import ast
from typing import Optional


def validate_python_syntax(code: str) -> tuple[bool, Optional[str]]:
    """
    Validate Python code syntax using ast.parse().

    Args:
        code: Python code string to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Синтаксическая ошибка в строке {e.lineno}: {e.msg}"


def validate_script_meta(meta: dict) -> tuple[bool, Optional[str]]:
    """
    Validate script meta.yaml structure.

    Args:
        meta: Parsed meta.yaml dictionary.

    Returns:
        Tuple of (is_valid, error_message).
    """
    required = ["name", "code_file"]
    for field in required:
        if field not in meta:
            return False, f"Отсутствует обязательное поле: {field}"
    return True, None


def validate_datasource_type_meta(meta: dict) -> tuple[bool, Optional[str]]:
    """
    Validate datasource type meta.yaml structure.

    Args:
        meta: Parsed meta.yaml dictionary.

    Returns:
        Tuple of (is_valid, error_message).
    """
    required = ["name"]
    for field in required:
        if field not in meta:
            return False, f"Отсутствует обязательное поле: {field}"
    return True, None


def validate_activator_type_meta(meta: dict) -> tuple[bool, Optional[str]]:
    """
    Validate activator type meta.yaml structure.

    Args:
        meta: Parsed meta.yaml dictionary.

    Returns:
        Tuple of (is_valid, error_message).
    """
    required = ["name"]
    for field in required:
        if field not in meta:
            return False, f"Отсутствует обязательное поле: {field}"
    return True, None
