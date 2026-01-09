"""MCP Tools for Reference data (ValueTypes, PropertySections)."""

import json
from mcp.types import Tool, TextContent

from ..client import GimsClient, GimsApiError
from ..utils import format_error


def register_reference_tools(server, client: GimsClient) -> None:
    """Register all reference tools with the MCP server."""
    # Tools are registered via get_reference_tools() and handled in server.py
    pass


async def handle_reference_tool(name: str, arguments: dict, client: GimsClient) -> list[TextContent] | None:
    """Handle reference tool calls. Returns None if tool not handled."""
    try:
        if name == "list_value_types":
            return await _list_value_types(client)
        elif name == "list_property_sections":
            return await _list_property_sections(client)
    except GimsApiError as e:
        return [TextContent(type="text", text=f"Error: {e.message}\nDetail: {e.detail}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {format_error(e)}")]
    return None


def get_reference_tools() -> list[Tool]:
    """Get the list of reference tools."""
    return [
        Tool(
            name="list_value_types",
            description="List all available value types for properties and parameters. Use this to get value_type_id when creating properties.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_property_sections",
            description="List all available property sections. Use this to get section_name_id when creating properties.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


async def _list_value_types(client: GimsClient) -> list[TextContent]:
    """List all value types."""
    types = await client.list_value_types()
    return [TextContent(type="text", text=json.dumps({"value_types": types}, indent=2, ensure_ascii=False))]


async def _list_property_sections(client: GimsClient) -> list[TextContent]:
    """List all property sections."""
    sections = await client.list_property_sections()
    return [TextContent(type="text", text=json.dumps({"property_sections": sections}, indent=2, ensure_ascii=False))]
