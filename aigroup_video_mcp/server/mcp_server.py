"""
MCP Server implementation for video analysis.

This module implements the main MCP server that provides video analysis
tools and resources through the Model Context Protocol.
"""

import asyncio
import time
from typing import Any, Sequence
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    CallToolRequest,
    ListToolsRequest,
    ListResourcesRequest,
    ReadResourceRequest,
)
from loguru import logger

from ..settings import get_settings, get_mcp_settings
from ..tools.base import get_tool_registry, register_tool
from ..tools.analyze_video import AnalyzeVideoTool
from ..tools.summarize_video import SummarizeVideoTool
from ..tools.analyze_scenes import AnalyzeVideoScenesTool
from ..tools.analyze_custom import AnalyzeVideoCustomTool
from ..tools.validate_source import ValidateVideoSourceTool
from ..resources.base import get_resource_registry, register_resource
from ..resources.config import ConfigResource, ConfigSectionResource
from ..resources.models import ModelsResource, ModelCapabilitiesResource
from ..resources.status import StatusResource, ServiceHealthResource
from ..resources.usage_stats import (
    UsageStatsResource, 
    UsageReportResource,
    record_tool_usage,
    record_resource_usage
)


class VideoAnalysisMCPServer:
    """MCP Server for video analysis."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.settings = get_settings()
        self.mcp_settings = get_mcp_settings()
        self.server = Server(self.mcp_settings.server_name)
        
        # Initialize registries
        self.tool_registry = get_tool_registry()
        self.resource_registry = get_resource_registry()
        
        # Setup server handlers
        self._setup_handlers()
        
        # Register tools and resources
        self._register_tools()
        self._register_resources()
        
        logger.info(f"Initialized MCP server: {self.mcp_settings.server_name}")
    
    def _setup_handlers(self) -> None:
        """Setup MCP server request handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """Handle list tools request."""
            try:
                tools = self.tool_registry.get_mcp_tools()
                logger.debug(f"Listed {len(tools)} tools")
                return tools
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return []
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool call request."""
            start_time = time.time()
            
            try:
                logger.info(f"Calling tool: {name} with arguments: {arguments}")
                
                # Execute tool
                result = await self.tool_registry.execute_tool(name, arguments)
                duration = time.time() - start_time
                
                # Record usage
                record_tool_usage(
                    tool_name=name,
                    success=result.success,
                    duration=duration,
                    arguments=arguments
                )
                
                # Format response
                response_text = result.content
                if result.error:
                    response_text += f"\n\nError: {result.error}"
                
                if result.metadata:
                    response_text += f"\n\nMetadata: {result.metadata}"
                
                logger.info(f"Tool {name} completed in {duration:.2f}s (success: {result.success})")
                
                return [TextContent(type="text", text=response_text)]
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(f"Error calling tool {name}: {e}")
                
                # Record failed usage
                record_tool_usage(
                    tool_name=name,
                    success=False,
                    duration=duration,
                    arguments=arguments,
                    error=str(e)
                )
                
                return [TextContent(type="text", text=error_msg)]
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """Handle list resources request."""
            try:
                resources = self.resource_registry.get_mcp_resources()
                logger.debug(f"Listed {len(resources)} resources")
                return resources
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                return []
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle read resource request."""
            try:
                logger.info(f"Reading resource: {uri}")
                
                # Read resource
                resource_data = await self.resource_registry.read_resource(uri)
                
                # Record usage
                record_resource_usage(
                    resource_uri=uri,
                    success=True,
                    mime_type=resource_data.mime_type,
                    metadata=resource_data.metadata
                )
                
                logger.info(f"Resource {uri} read successfully")
                return resource_data.content
                
            except Exception as e:
                error_msg = f"Resource read failed: {str(e)}"
                logger.error(f"Error reading resource {uri}: {e}")
                
                # Record failed usage
                record_resource_usage(
                    resource_uri=uri,
                    success=False,
                    error=str(e)
                )
                
                return error_msg
    
    def _register_tools(self) -> None:
        """Register all video analysis tools."""
        try:
            # Register core video analysis tools
            tools = [
                AnalyzeVideoTool(),
                SummarizeVideoTool(),
                AnalyzeVideoScenesTool(),
                AnalyzeVideoCustomTool(),
                ValidateVideoSourceTool(),
            ]
            
            for tool in tools:
                register_tool(tool)
            
            logger.info(f"Registered {len(tools)} tools")
            
        except Exception as e:
            logger.error(f"Error registering tools: {e}")
            raise
    
    def _register_resources(self) -> None:
        """Register all MCP resources."""
        try:
            # Register core resources
            resources = [
                # Configuration resources
                ConfigResource(),
                ConfigSectionResource("dashscope"),
                ConfigSectionResource("video"),
                ConfigSectionResource("mcp"),
                ConfigSectionResource("log"),
                ConfigSectionResource("security"),
                
                # Model resources
                ModelsResource(),
                ModelCapabilitiesResource("qwen-vl-max"),
                ModelCapabilitiesResource("qwen-vl-plus"),
                
                # Status resources
                StatusResource(),
                ServiceHealthResource(),
                
                # Usage statistics resources
                UsageStatsResource(),
                UsageReportResource(1),   # 1 hour
                UsageReportResource(6),   # 6 hours
                UsageReportResource(24),  # 24 hours
                UsageReportResource(168), # 1 week
            ]
            
            for resource in resources:
                register_resource(resource)
            
            logger.info(f"Registered {len(resources)} resources")
            
        except Exception as e:
            logger.error(f"Error registering resources: {e}")
            raise
    
    async def run_stdio(self) -> None:
        """Run the server with stdio transport."""
        try:
            logger.info("Starting MCP server with stdio transport")
            
            # Run server
            from mcp.server.stdio import stdio_server
            
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
                
        except Exception as e:
            logger.error(f"Error running stdio server: {e}")
            raise
    
    async def run_sse(self, host: str = "localhost", port: int = 3001) -> None:
        """
        Run the server with SSE transport.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        try:
            logger.info(f"Starting MCP server with SSE transport on {host}:{port}")
            
            from mcp.server.sse import SseServerTransport
            
            async with SseServerTransport(f"http://{host}:{port}/sse") as transport:
                await self.server.run(
                    transport.read_stream,
                    transport.write_stream,
                    self.server.create_initialization_options()
                )
                
        except Exception as e:
            logger.error(f"Error running SSE server: {e}")
            raise
    
    def get_server_info(self) -> dict[str, Any]:
        """
        Get server information.
        
        Returns:
            dict[str, Any]: Server information
        """
        return {
            "name": self.mcp_settings.server_name,
            "version": self.mcp_settings.version,
            "description": self.mcp_settings.description,
            "transport": self.mcp_settings.transport,
            "tools_count": len(self.tool_registry),
            "resources_count": len(self.resource_registry),
            "environment": self.settings.environment,
            "debug_mode": self.settings.debug,
            "configuration": {
                "max_concurrent_requests": self.mcp_settings.max_concurrent_requests,
                "request_timeout": self.mcp_settings.request_timeout,
                "max_file_size": self.settings.video.max_file_size,
                "supported_formats": self.settings.video.supported_formats,
            }
        }
    
    async def health_check(self) -> dict[str, Any]:
        """
        Perform server health check.
        
        Returns:
            dict[str, Any]: Health check result
        """
        try:
            # Check basic server status
            health = {
                "status": "healthy",
                "timestamp": time.time(),
                "server_info": self.get_server_info(),
                "checks": []
            }
            
            # Check tool registry
            tools_check = {
                "name": "tools_registry",
                "status": "pass" if len(self.tool_registry) > 0 else "fail",
                "message": f"Tools registered: {len(self.tool_registry)}"
            }
            health["checks"].append(tools_check)
            
            # Check resource registry
            resources_check = {
                "name": "resources_registry", 
                "status": "pass" if len(self.resource_registry) > 0 else "fail",
                "message": f"Resources registered: {len(self.resource_registry)}"
            }
            health["checks"].append(resources_check)
            
            # Check configuration
            config_check = {
                "name": "configuration",
                "status": "pass" if self.settings.dashscope.api_key else "fail",
                "message": "Configuration loaded" if self.settings.dashscope.api_key else "DashScope API key not configured"
            }
            health["checks"].append(config_check)
            
            # Determine overall status
            failed_checks = [c for c in health["checks"] if c["status"] == "fail"]
            if failed_checks:
                health["status"] = "unhealthy"
            
            return health
            
        except Exception as e:
            return {
                "status": "error",
                "timestamp": time.time(),
                "error": str(e)
            }
    
    async def shutdown(self) -> None:
        """Shutdown the server gracefully."""
        try:
            logger.info("Shutting down MCP server")
            
            # Clear registries
            self.tool_registry.clear()
            self.resource_registry.clear()
            
            logger.info("MCP server shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during server shutdown: {e}")


# Factory functions for easy server creation
def create_server() -> VideoAnalysisMCPServer:
    """
    Create and configure a new MCP server instance.
    
    Returns:
        VideoAnalysisMCPServer: Configured server instance
    """
    return VideoAnalysisMCPServer()


async def run_stdio_server() -> None:
    """Run MCP server with stdio transport."""
    server = create_server()
    await server.run_stdio()


async def run_sse_server(host: str = "localhost", port: int = 3001) -> None:
    """
    Run MCP server with SSE transport.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    server = create_server()
    await server.run_sse(host, port)


# Context manager for server lifecycle
@asynccontextmanager
async def managed_server():
    """Context manager for server lifecycle management."""
    server = create_server()
    try:
        yield server
    finally:
        await server.shutdown()


if __name__ == "__main__":
    # Run stdio server by default
    import asyncio
    asyncio.run(run_stdio_server())