"""MCP Server for GIMS Automation."""

import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .client import GimsClient, GimsApiError
from .config import Config
from .tools.scripts import get_script_tools, handle_script_tool
from .tools.datasource_types import get_datasource_type_tools, handle_datasource_type_tool
from .tools.activator_types import get_activator_type_tools, handle_activator_type_tool
from .tools.references import get_reference_tools, handle_reference_tool
from .tools.logs import get_log_tools, handle_log_tool
from .tools.sync import get_sync_tools, handle_sync_tool
from .utils import format_error, set_max_response_size

logger = logging.getLogger(__name__)


class GimsMcpServer:
    """MCP Server for GIMS Automation."""

    def __init__(self, config: Config):
        self.config = config
        self.client = GimsClient(config)
        self.server = Server("gims-automation")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def list_tools():
            """Return list of available tools."""
            tools = []
            tools.extend(get_script_tools())
            tools.extend(get_datasource_type_tools())
            tools.extend(get_activator_type_tools())
            tools.extend(get_reference_tools())
            tools.extend(get_log_tools())
            tools.extend(get_sync_tools())
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                # Try script tools
                result = await handle_script_tool(name, arguments, self.client)
                if result is not None:
                    return result

                # Try datasource type tools
                result = await handle_datasource_type_tool(name, arguments, self.client)
                if result is not None:
                    return result

                # Try activator type tools
                result = await handle_activator_type_tool(name, arguments, self.client)
                if result is not None:
                    return result

                # Try reference tools
                result = await handle_reference_tool(name, arguments, self.client)
                if result is not None:
                    return result

                # Try log tools
                result = await handle_log_tool(name, arguments, self.client)
                if result is not None:
                    return result

                # Try sync tools
                result = await handle_sync_tool(name, arguments, self.client)
                if result is not None:
                    return result

                return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except GimsApiError as e:
                return [TextContent(type="text", text=f"GIMS API Error ({e.status_code}): {e.message}\nDetail: {e.detail}")]
            except Exception as e:
                logger.exception(f"Error calling tool {name}")
                return [TextContent(type="text", text=f"Error: {format_error(e)}")]

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

    async def close(self):
        """Close server resources."""
        await self.client.close()


async def run_server(config: Config):
    """Run the MCP server with the given configuration."""
    # Configure response size limit
    set_max_response_size(config.max_response_size_kb)

    server = GimsMcpServer(config)
    try:
        await server.run()
    finally:
        await server.close()
