"""Tests for serialization utilities."""

import pytest
import yaml

from gims_mcp.serializers import (
    serialize_script,
    serialize_datasource_type,
    serialize_activator_type,
    serialize_property,
    serialize_parameter,
    deserialize_script,
    deserialize_datasource_type,
    deserialize_activator_type,
)


class TestSerializeScript:
    """Tests for serialize_script function."""

    def test_basic_script(self):
        """Test serialization of a basic script."""
        script_data = {
            "name": "Test Script",
            "code": 'print("hello")',
            "folder_path": "/Test",
        }
        meta_yaml, code = serialize_script(script_data, "https://gims.test")

        meta = yaml.safe_load(meta_yaml)
        assert meta["name"] == "Test Script"
        assert meta["code_file"] == "code.py"
        assert meta["gims_folder"] == "/Test"
        assert meta["exported_from"] == "https://gims.test"
        assert "exported_at" in meta
        assert code == 'print("hello")'

    def test_script_with_description(self):
        """Test serialization preserves description."""
        script_data = {
            "name": "My Script",
            "code": "pass",
            "description": "A useful script",
        }
        meta_yaml, _ = serialize_script(script_data, "https://gims.test")

        meta = yaml.safe_load(meta_yaml)
        assert meta["description"] == "A useful script"

    def test_script_with_updated_at(self):
        """Test serialization includes gims_updated_at when present."""
        script_data = {
            "name": "My Script",
            "code": "pass",
            "updated_at": "2026-01-15T10:30:00Z",
        }
        meta_yaml, _ = serialize_script(script_data, "https://gims.test")

        meta = yaml.safe_load(meta_yaml)
        assert meta["gims_updated_at"] == "2026-01-15T10:30:00Z"

    def test_script_without_code(self):
        """Test serialization of script without code returns empty string."""
        script_data = {
            "name": "Empty Script",
        }
        _, code = serialize_script(script_data, "https://gims.test")
        assert code == ""

    def test_script_default_folder(self):
        """Test default folder path is '/' when not specified."""
        script_data = {
            "name": "Test",
            "code": "",
        }
        meta_yaml, _ = serialize_script(script_data, "https://gims.test")

        meta = yaml.safe_load(meta_yaml)
        assert meta["gims_folder"] == "/"


class TestSerializeDatasourceType:
    """Tests for serialize_datasource_type function."""

    def test_basic_type(self):
        """Test serialization of a basic datasource type."""
        type_data = {
            "name": "PostgreSQL",
            "description": "PostgreSQL monitoring",
            "version": "1.0",
            "properties": [],
            "methods": [],
        }
        files = serialize_datasource_type(type_data, "https://gims.test")

        assert "meta.yaml" in files
        assert "properties.yaml" in files

        meta = yaml.safe_load(files["meta.yaml"])
        assert meta["name"] == "PostgreSQL"
        assert meta["description"] == "PostgreSQL monitoring"
        assert meta["version"] == "1.0"

    def test_type_with_properties(self):
        """Test serialization includes properties."""
        type_data = {
            "name": "PostgreSQL",
            "properties": [
                {
                    "name": "Хост",
                    "label": "host",
                    "value_type_name": "str",
                    "default_value": "localhost",
                    "section_name": "Подключение",
                    "is_required": True,
                    "is_hidden": False,
                    "is_inner": False,
                },
            ],
            "methods": [],
        }
        files = serialize_datasource_type(type_data, "https://gims.test")

        props = yaml.safe_load(files["properties.yaml"])
        assert len(props["properties"]) == 1
        assert props["properties"][0]["label"] == "host"
        assert props["properties"][0]["value_type"] == "str"
        assert props["properties"][0]["is_required"] is True

    def test_type_with_methods(self):
        """Test serialization includes methods with parameters."""
        type_data = {
            "name": "PostgreSQL",
            "properties": [],
            "methods": [
                {
                    "name": "Подключение",
                    "label": "connect",
                    "description": "Проверка подключения",
                    "code": "# connection code",
                    "parameters": [
                        {
                            "label": "timeout",
                            "input_type": True,
                            "value_type_name": "int",
                            "default_value": "30",
                        },
                    ],
                },
            ],
        }
        files = serialize_datasource_type(type_data, "https://gims.test")

        # Check method meta
        assert "methods/connect/meta.yaml" in files
        method_meta = yaml.safe_load(files["methods/connect/meta.yaml"])
        assert method_meta["name"] == "Подключение"
        assert method_meta["label"] == "connect"

        # Check method code
        assert "methods/connect/code.py" in files
        assert files["methods/connect/code.py"] == "# connection code"

        # Check method params
        assert "methods/connect/params.yaml" in files
        params = yaml.safe_load(files["methods/connect/params.yaml"])
        assert len(params["parameters"]) == 1
        assert params["parameters"][0]["label"] == "timeout"


class TestSerializeActivatorType:
    """Tests for serialize_activator_type function."""

    def test_basic_type(self):
        """Test serialization of a basic activator type."""
        type_data = {
            "name": "HTTP Poller",
            "description": "Poll HTTP endpoints",
            "version": "1.0",
            "code": "# poller code",
            "properties": [],
        }
        files = serialize_activator_type(type_data, "https://gims.test")

        assert "meta.yaml" in files
        assert "code.py" in files
        assert "properties.yaml" in files

        meta = yaml.safe_load(files["meta.yaml"])
        assert meta["name"] == "HTTP Poller"
        assert files["code.py"] == "# poller code"

    def test_type_with_properties(self):
        """Test serialization includes activator properties."""
        type_data = {
            "name": "HTTP Poller",
            "code": "pass",
            "properties": [
                {
                    "name": "Интервал",
                    "label": "interval",
                    "value_type_name": "int",
                    "default_value": "60",
                    "section_name": "Основные",
                    "is_required": True,
                },
            ],
        }
        files = serialize_activator_type(type_data, "https://gims.test")

        props = yaml.safe_load(files["properties.yaml"])
        assert len(props["properties"]) == 1
        assert props["properties"][0]["label"] == "interval"


class TestSerializeProperty:
    """Tests for serialize_property function."""

    def test_complete_property(self):
        """Test serialization of a complete property."""
        prop = {
            "name": "Хост подключения",
            "label": "host",
            "value_type_name": "str",
            "default_value": "localhost",
            "section_name": "Подключение",
            "is_required": True,
            "is_hidden": False,
            "is_inner": False,
            "description": "Hostname or IP",
        }
        result = serialize_property(prop)

        assert result["name"] == "Хост подключения"
        assert result["label"] == "host"
        assert result["value_type"] == "str"
        assert result["default_value"] == "localhost"
        assert result["section"] == "Подключение"
        assert result["is_required"] is True
        assert result["is_hidden"] is False
        assert result["is_inner"] is False
        assert result["description"] == "Hostname or IP"

    def test_property_with_updated_at(self):
        """Test that updated_at is preserved."""
        prop = {
            "name": "Test",
            "label": "test",
            "value_type_name": "str",
            "updated_at": "2026-01-15T10:00:00Z",
        }
        result = serialize_property(prop)
        assert result["gims_updated_at"] == "2026-01-15T10:00:00Z"

    def test_property_defaults(self):
        """Test default values for optional fields."""
        prop = {
            "name": "Test",
            "label": "test",
        }
        result = serialize_property(prop)

        assert result["value_type"] == ""
        assert result["default_value"] == ""
        assert result["section"] == "Основные"
        assert result["is_required"] is False
        assert result["is_hidden"] is False
        assert result["is_inner"] is False


class TestSerializeParameter:
    """Tests for serialize_parameter function."""

    def test_input_parameter(self):
        """Test serialization of an input parameter."""
        param = {
            "label": "timeout",
            "input_type": True,
            "value_type_name": "int",
            "default_value": "30",
            "description": "Timeout in seconds",
            "is_hidden": False,
        }
        result = serialize_parameter(param)

        assert result["label"] == "timeout"
        assert result["input_type"] is True
        assert result["value_type"] == "int"
        assert result["default_value"] == "30"
        assert result["description"] == "Timeout in seconds"
        assert result["is_hidden"] is False

    def test_output_parameter(self):
        """Test serialization of an output parameter."""
        param = {
            "label": "result",
            "input_type": False,
            "value_type_name": "object",
        }
        result = serialize_parameter(param)

        assert result["input_type"] is False


class TestDeserializeScript:
    """Tests for deserialize_script function."""

    def test_basic_deserialization(self):
        """Test basic script deserialization."""
        meta = {
            "name": "Test Script",
            "description": "A test script",
        }
        code = 'print("hello")'

        result = deserialize_script(meta, code)

        assert result["name"] == "Test Script"
        assert result["code"] == 'print("hello")'
        assert result["description"] == "A test script"

    def test_missing_description(self):
        """Test deserialization with missing description."""
        meta = {"name": "Test Script"}
        code = "pass"

        result = deserialize_script(meta, code)
        assert result["description"] == ""


class TestDeserializeDatasourceType:
    """Tests for deserialize_datasource_type function."""

    def test_basic_deserialization(self):
        """Test basic datasource type deserialization."""
        files = {
            "meta.yaml": yaml.dump({"name": "PostgreSQL", "description": "DB monitor"}),
            "properties.yaml": yaml.dump({"properties": []}),
        }

        result = deserialize_datasource_type(files)

        assert result["name"] == "PostgreSQL"
        assert result["description"] == "DB monitor"
        assert result["properties"] == []
        assert result["methods"] == []

    def test_with_methods(self):
        """Test deserialization with methods."""
        files = {
            "meta.yaml": yaml.dump({"name": "PostgreSQL"}),
            "properties.yaml": yaml.dump({"properties": []}),
            "methods/query/meta.yaml": yaml.dump({"name": "Query", "label": "query"}),
            "methods/query/code.py": "result = execute(sql)",
            "methods/query/params.yaml": yaml.dump({
                "parameters": [{"label": "sql", "input_type": True}]
            }),
        }

        result = deserialize_datasource_type(files)

        assert len(result["methods"]) == 1
        assert result["methods"][0]["name"] == "Query"
        assert result["methods"][0]["label"] == "query"
        assert result["methods"][0]["code"] == "result = execute(sql)"
        assert len(result["methods"][0]["parameters"]) == 1

    def test_empty_files(self):
        """Test deserialization with empty/missing files."""
        files = {}

        result = deserialize_datasource_type(files)

        assert result["name"] == ""
        assert result["methods"] == []


class TestDeserializeActivatorType:
    """Tests for deserialize_activator_type function."""

    def test_basic_deserialization(self):
        """Test basic activator type deserialization."""
        files = {
            "meta.yaml": yaml.dump({"name": "Poller", "description": "HTTP poller"}),
            "code.py": "# poller code",
            "properties.yaml": yaml.dump({"properties": []}),
        }

        result = deserialize_activator_type(files)

        assert result["name"] == "Poller"
        assert result["description"] == "HTTP poller"
        assert result["code"] == "# poller code"
        assert result["properties"] == []

    def test_missing_code(self):
        """Test deserialization with missing code file."""
        files = {
            "meta.yaml": yaml.dump({"name": "Poller"}),
            "properties.yaml": yaml.dump({"properties": []}),
        }

        result = deserialize_activator_type(files)
        assert result["code"] == "# No code"


class TestRoundTrip:
    """Tests for serialization/deserialization round-trips."""

    def test_script_round_trip(self):
        """Test that script survives serialization/deserialization."""
        original = {
            "name": "Test Script",
            "code": 'print("hello")',
            "description": "A test",
        }

        meta_yaml, code = serialize_script(original, "https://gims.test")
        meta = yaml.safe_load(meta_yaml)
        restored = deserialize_script(meta, code)

        assert restored["name"] == original["name"]
        assert restored["code"] == original["code"]
        assert restored["description"] == original["description"]

    def test_activator_type_round_trip(self):
        """Test that activator type survives serialization/deserialization."""
        original = {
            "name": "HTTP Poller",
            "description": "Poll endpoints",
            "version": "1.0",
            "code": "# poll code",
            "properties": [
                {
                    "name": "Interval",
                    "label": "interval",
                    "value_type_name": "int",
                    "default_value": "60",
                    "section_name": "Main",
                    "is_required": True,
                    "is_hidden": False,
                    "is_inner": False,
                    "description": "",
                },
            ],
        }

        files = serialize_activator_type(original, "https://gims.test")
        restored = deserialize_activator_type(files)

        assert restored["name"] == original["name"]
        assert restored["description"] == original["description"]
        assert restored["code"] == original["code"]
        assert len(restored["properties"]) == 1
