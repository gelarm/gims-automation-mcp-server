"""Tests for validation utilities."""

import pytest

from gims_mcp.validators import (
    validate_python_syntax,
    validate_script_meta,
    validate_datasource_type_meta,
    validate_activator_type_meta,
)


class TestValidatePythonSyntax:
    """Tests for validate_python_syntax function."""

    def test_valid_simple_code(self):
        """Test validation of simple valid Python code."""
        code = "def hello():\n    print('Hello')"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_complex_code(self):
        """Test validation of complex valid Python code."""
        code = """
import os
from datetime import datetime

class MyClass:
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"

def main():
    obj = MyClass("World")
    print(obj.greet())

if __name__ == "__main__":
    main()
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None

    def test_valid_empty_code(self):
        """Test that empty code is valid."""
        is_valid, error = validate_python_syntax("")
        assert is_valid is True
        assert error is None

    def test_valid_whitespace_only(self):
        """Test that whitespace-only code is valid."""
        is_valid, error = validate_python_syntax("   \n\t\n   ")
        assert is_valid is True
        assert error is None

    def test_valid_comment_only(self):
        """Test that comment-only code is valid."""
        is_valid, error = validate_python_syntax("# This is a comment")
        assert is_valid is True
        assert error is None

    def test_invalid_syntax_missing_colon(self):
        """Test detection of missing colon in function definition."""
        code = "def hello()\n    print('Hello')"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "Синтаксическая ошибка" in error

    def test_invalid_syntax_unclosed_parenthesis(self):
        """Test detection of unclosed parenthesis."""
        code = "print('hello'"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "Синтаксическая ошибка" in error

    def test_invalid_syntax_bad_indentation(self):
        """Test detection of bad indentation."""
        code = "def hello():\nprint('Hello')"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "Синтаксическая ошибка" in error

    def test_invalid_syntax_reports_line_number(self):
        """Test that error message includes line number."""
        code = "x = 1\ny = 2\ndef broken(\nz = 3"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert error is not None
        assert "строке" in error  # Should mention line number

    def test_valid_unicode_code(self):
        """Test validation of code with Unicode characters."""
        code = """
# Привет мир
def приветствие():
    return "Привет, мир!"
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error is None


class TestValidateScriptMeta:
    """Tests for validate_script_meta function."""

    def test_valid_minimal_meta(self):
        """Test validation of minimal valid meta."""
        meta = {"name": "Test Script", "code_file": "code.py"}
        is_valid, error = validate_script_meta(meta)
        assert is_valid is True
        assert error is None

    def test_valid_complete_meta(self):
        """Test validation of complete meta with all fields."""
        meta = {
            "name": "Test Script",
            "code_file": "code.py",
            "description": "A test script",
            "version": "1.0",
            "gims_folder": "/Test",
            "exported_at": "2026-01-20T10:00:00Z",
            "exported_from": "https://gims.example.com",
        }
        is_valid, error = validate_script_meta(meta)
        assert is_valid is True
        assert error is None

    def test_invalid_missing_name(self):
        """Test detection of missing name field."""
        meta = {"code_file": "code.py"}
        is_valid, error = validate_script_meta(meta)
        assert is_valid is False
        assert error is not None
        assert "name" in error

    def test_invalid_missing_code_file(self):
        """Test detection of missing code_file field."""
        meta = {"name": "Test Script"}
        is_valid, error = validate_script_meta(meta)
        assert is_valid is False
        assert error is not None
        assert "code_file" in error

    def test_invalid_empty_meta(self):
        """Test detection of empty meta."""
        meta = {}
        is_valid, error = validate_script_meta(meta)
        assert is_valid is False
        assert error is not None


class TestValidateDatasourceTypeMeta:
    """Tests for validate_datasource_type_meta function."""

    def test_valid_minimal_meta(self):
        """Test validation of minimal valid meta."""
        meta = {"name": "PostgreSQL Monitor"}
        is_valid, error = validate_datasource_type_meta(meta)
        assert is_valid is True
        assert error is None

    def test_valid_complete_meta(self):
        """Test validation of complete meta with all fields."""
        meta = {
            "name": "PostgreSQL Monitor",
            "description": "Мониторинг PostgreSQL",
            "version": "2.0",
            "gims_folder": "/Database/PostgreSQL",
            "exported_at": "2026-01-20T10:00:00Z",
            "exported_from": "https://gims.example.com",
        }
        is_valid, error = validate_datasource_type_meta(meta)
        assert is_valid is True
        assert error is None

    def test_invalid_missing_name(self):
        """Test detection of missing name field."""
        meta = {"description": "Some description"}
        is_valid, error = validate_datasource_type_meta(meta)
        assert is_valid is False
        assert error is not None
        assert "name" in error

    def test_invalid_empty_meta(self):
        """Test detection of empty meta."""
        meta = {}
        is_valid, error = validate_datasource_type_meta(meta)
        assert is_valid is False
        assert error is not None


class TestValidateActivatorTypeMeta:
    """Tests for validate_activator_type_meta function."""

    def test_valid_minimal_meta(self):
        """Test validation of minimal valid meta."""
        meta = {"name": "HTTP Poller"}
        is_valid, error = validate_activator_type_meta(meta)
        assert is_valid is True
        assert error is None

    def test_valid_complete_meta(self):
        """Test validation of complete meta with all fields."""
        meta = {
            "name": "HTTP Poller",
            "description": "Опрос HTTP endpoints",
            "version": "1.5",
            "is_all_nodes_run": False,
            "gims_folder": "/Polling/HTTP",
            "code_file": "code.py",
            "exported_at": "2026-01-20T10:00:00Z",
            "exported_from": "https://gims.example.com",
        }
        is_valid, error = validate_activator_type_meta(meta)
        assert is_valid is True
        assert error is None

    def test_invalid_missing_name(self):
        """Test detection of missing name field."""
        meta = {"code_file": "code.py"}
        is_valid, error = validate_activator_type_meta(meta)
        assert is_valid is False
        assert error is not None
        assert "name" in error

    def test_invalid_empty_meta(self):
        """Test detection of empty meta."""
        meta = {}
        is_valid, error = validate_activator_type_meta(meta)
        assert is_valid is False
        assert error is not None
