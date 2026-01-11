"""Pytest configuration and fixtures."""

import pytest
import respx
from httpx import Response

from gims_mcp.config import Config
from gims_mcp.client import GimsClient


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        url="https://gims.test.local",
        access_token="test-access-token",
        refresh_token="test-refresh-token",
    )


@pytest.fixture
def client(config):
    """Create a test client."""
    return GimsClient(config)


@pytest.fixture
def mock_api():
    """Create a mock API context."""
    with respx.mock(base_url="https://gims.test.local/automation") as respx_mock:
        yield respx_mock


# Sample data fixtures

@pytest.fixture
def sample_folders():
    """Sample folder data."""
    return [
        {"id": 1, "name": "root", "parent_folder_id": None},
        {"id": 2, "name": "monitoring", "parent_folder_id": 1},
        {"id": 3, "name": "prometheus", "parent_folder_id": 2},
    ]


@pytest.fixture
def sample_scripts():
    """Sample script data."""
    return [
        {"id": 1, "name": "test_script", "code": "print('hello')", "folder_id": 2},
        {"id": 2, "name": "check_health", "code": "# check health\npass", "folder_id": 3},
    ]


@pytest.fixture
def sample_datasource_types():
    """Sample datasource type data."""
    return [
        {"id": 1, "name": "PostgreSQL", "description": "PostgreSQL database", "version": "1.0", "folder": None},
        {"id": 2, "name": "Prometheus", "description": "Prometheus monitoring", "version": "1.0", "folder": 1},
    ]


@pytest.fixture
def sample_activator_types():
    """Sample activator type data."""
    return [
        {"id": 1, "name": "ScheduleActivator", "code": "# schedule\npass", "version": "1.0", "folder": None},
        {"id": 2, "name": "TriggerActivator", "code": "# trigger\npass", "version": "1.0", "folder": 1},
    ]


@pytest.fixture
def sample_value_types():
    """Sample value type data."""
    return [
        {"id": 1, "name": "str", "description": "Строка"},
        {"id": 2, "name": "int", "description": "Целое число"},
        {"id": 3, "name": "bool", "description": "Логическое значение"},
    ]


@pytest.fixture
def sample_property_sections():
    """Sample property section data."""
    return [
        {"id": 1, "name": "Основные", "order_id": 1},
        {"id": 2, "name": "Подключение", "order_id": 2},
        {"id": 3, "name": "Дополнительно", "order_id": 3},
    ]
