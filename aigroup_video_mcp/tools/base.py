"""
Base tool class and tool registry for MCP video analysis tools.

This module provides the foundation for all video analysis tools
that can be called through the MCP protocol.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, Field
from loguru import logger

from mcp.types import Tool as MCPTool, TextContent
from ..core.analyzer import AsyncVideoAnalyzer, VideoSource, AnalysisResult


class ToolInput(BaseModel):
    """Base input model for tools."""
    pass


class ToolOutput(BaseModel):
    """Base output model for tools."""
    
    success: bool = Field(description="Whether the operation was successful")
    content: str = Field(description="Tool output content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class VideoAnalysisTool(ABC):
    """Base class for all video analysis tools."""
    
    def __init__(self):
        """Initialize the tool."""
        self.analyzer = AsyncVideoAnalyzer()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """Input schema for the tool."""
        pass
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute the tool with given inputs.
        
        Args:
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Tool execution result
        """
        pass
    
    def to_mcp_tool(self) -> MCPTool:
        """
        Convert to MCP tool format.
        
        Returns:
            MCPTool: MCP tool definition
        """
        return MCPTool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema
        )
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate tool inputs.
        
        Args:
            inputs: Input parameters to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If inputs are invalid
        """
        try:
            # Basic validation - can be overridden in subclasses
            schema = self.input_schema
            
            if "required" in schema:
                for field in schema["required"]:
                    if field not in inputs:
                        raise ValueError(f"Required field missing: {field}")
            
            if "properties" in schema:
                for field, field_schema in schema["properties"].items():
                    if field in inputs:
                        value = inputs[field]
                        self._validate_field(field, value, field_schema)
            
            return True
            
        except Exception as e:
            logger.error(f"Input validation failed for {self.name}: {e}")
            raise
    
    def _validate_field(self, field_name: str, value: Any, field_schema: Dict[str, Any]) -> None:
        """Validate a single field."""
        field_type = field_schema.get("type")
        
        if field_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"Field {field_name} must be a string")
            
            min_length = field_schema.get("minLength")
            if min_length and len(value) < min_length:
                raise ValueError(f"Field {field_name} must be at least {min_length} characters")
            
            max_length = field_schema.get("maxLength")
            if max_length and len(value) > max_length:
                raise ValueError(f"Field {field_name} must be at most {max_length} characters")
        
        elif field_type == "integer":
            if not isinstance(value, int):
                raise ValueError(f"Field {field_name} must be an integer")
            
            minimum = field_schema.get("minimum")
            if minimum is not None and value < minimum:
                raise ValueError(f"Field {field_name} must be at least {minimum}")
            
            maximum = field_schema.get("maximum")
            if maximum is not None and value > maximum:
                raise ValueError(f"Field {field_name} must be at most {maximum}")
        
        elif field_type == "number":
            if not isinstance(value, (int, float)):
                raise ValueError(f"Field {field_name} must be a number")
        
        elif field_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"Field {field_name} must be a boolean")
        
        elif field_type == "array":
            if not isinstance(value, list):
                raise ValueError(f"Field {field_name} must be an array")
    
    def create_video_source(self, path_or_url: str) -> VideoSource:
        """
        Create VideoSource from path or URL.
        
        Args:
            path_or_url: Video file path or URL
            
        Returns:
            VideoSource: Created video source
        """
        if path_or_url.startswith(('http://', 'https://')):
            return VideoSource(type="url", path=path_or_url)
        else:
            return VideoSource(type="file", path=path_or_url)
    
    def analysis_result_to_tool_output(self, result: AnalysisResult) -> ToolOutput:
        """
        Convert AnalysisResult to ToolOutput.
        
        Args:
            result: Analysis result
            
        Returns:
            ToolOutput: Tool output
        """
        return ToolOutput(
            success=result.success,
            content=result.content,
            metadata=result.metadata,
            error=result.error
        )


class ToolRegistry:
    """Registry for managing video analysis tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, VideoAnalysisTool] = {}
    
    def register(self, tool: VideoAnalysisTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} is already registered, overriding")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
        else:
            logger.warning(f"Tool {tool_name} not found in registry")
    
    def get_tool(self, tool_name: str) -> Optional[VideoAnalysisTool]:
        """
        Get a tool by name.
        
        Args:
            tool_name: Name of tool to get
            
        Returns:
            Optional[VideoAnalysisTool]: Tool instance or None if not found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List[str]: List of tool names
        """
        return list(self._tools.keys())
    
    def get_mcp_tools(self) -> List[MCPTool]:
        """
        Get all tools in MCP format.
        
        Returns:
            List[MCPTool]: List of MCP tools
        """
        return [tool.to_mcp_tool() for tool in self._tools.values()]
    
    async def execute_tool(self, tool_name: str, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Tool execution result
            
        Raises:
            ValueError: If tool not found or inputs invalid
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        try:
            # Validate inputs
            tool.validate_inputs(inputs)
            
            # Execute tool
            result = await tool.execute(inputs)
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Tool {tool_name} execution failed: {e}"
            logger.error(error_msg)
            
            return ToolOutput(
                success=False,
                content="",
                metadata={"tool_name": tool_name, "inputs": inputs},
                error=error_msg
            )
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        logger.info("Cleared all tools from registry")
    
    def __len__(self) -> int:
        """Get number of registered tools."""
        return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered."""
        return tool_name in self._tools
    
    def __iter__(self):
        """Iterate over tool names."""
        return iter(self._tools.keys())


# Global tool registry instance
_tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    
    Returns:
        ToolRegistry: Global tool registry
    """
    return _tool_registry


def register_tool(tool: VideoAnalysisTool) -> None:
    """
    Register a tool in the global registry.
    
    Args:
        tool: Tool to register
    """
    _tool_registry.register(tool)


def get_tool(tool_name: str) -> Optional[VideoAnalysisTool]:
    """
    Get a tool from the global registry.
    
    Args:
        tool_name: Name of tool to get
        
    Returns:
        Optional[VideoAnalysisTool]: Tool instance or None if not found
    """
    return _tool_registry.get_tool(tool_name)


def list_tools() -> List[str]:
    """
    List all tools in the global registry.
    
    Returns:
        List[str]: List of tool names
    """
    return _tool_registry.list_tools()