"""
Base resource class and resource registry for MCP resources.

This module provides the foundation for all resources that can be accessed
through the MCP protocol.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from loguru import logger

from mcp.types import Resource as MCPResource
from ..settings import get_settings


class ResourceData(BaseModel):
    """Base data model for resources."""
    
    content: str
    metadata: Dict[str, Any] = {}
    mime_type: str = "text/plain"


class MCPResourceBase(ABC):
    """Base class for all MCP resources."""
    
    def __init__(self):
        """Initialize the resource."""
        self.settings = get_settings()
    
    @property
    @abstractmethod
    def uri(self) -> str:
        """Resource URI."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Resource name."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Resource description."""
        pass
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "text/plain"
    
    @abstractmethod
    async def read(self) -> ResourceData:
        """
        Read resource data.
        
        Returns:
            ResourceData: Resource content and metadata
        """
        pass
    
    def to_mcp_resource(self) -> MCPResource:
        """
        Convert to MCP resource format.
        
        Returns:
            MCPResource: MCP resource definition
        """
        return MCPResource(
            uri=self.uri,
            name=self.name,
            description=self.description,
            mimeType=self.mime_type
        )


class ResourceRegistry:
    """Registry for managing MCP resources."""
    
    def __init__(self):
        """Initialize resource registry."""
        self._resources: Dict[str, MCPResourceBase] = {}
    
    def register(self, resource: MCPResourceBase) -> None:
        """
        Register a resource.
        
        Args:
            resource: Resource to register
        """
        if resource.uri in self._resources:
            logger.warning(f"Resource {resource.uri} is already registered, overriding")
        
        self._resources[resource.uri] = resource
        logger.info(f"Registered resource: {resource.uri}")
    
    def unregister(self, resource_uri: str) -> None:
        """
        Unregister a resource.
        
        Args:
            resource_uri: URI of resource to unregister
        """
        if resource_uri in self._resources:
            del self._resources[resource_uri]
            logger.info(f"Unregistered resource: {resource_uri}")
        else:
            logger.warning(f"Resource {resource_uri} not found in registry")
    
    def get_resource(self, resource_uri: str) -> Optional[MCPResourceBase]:
        """
        Get a resource by URI.
        
        Args:
            resource_uri: URI of resource to get
            
        Returns:
            Optional[MCPResourceBase]: Resource instance or None if not found
        """
        return self._resources.get(resource_uri)
    
    def list_resources(self) -> List[str]:
        """
        List all registered resource URIs.
        
        Returns:
            List[str]: List of resource URIs
        """
        return list(self._resources.keys())
    
    def get_mcp_resources(self) -> List[MCPResource]:
        """
        Get all resources in MCP format.
        
        Returns:
            List[MCPResource]: List of MCP resources
        """
        return [resource.to_mcp_resource() for resource in self._resources.values()]
    
    async def read_resource(self, resource_uri: str) -> ResourceData:
        """
        Read a resource by URI.
        
        Args:
            resource_uri: URI of resource to read
            
        Returns:
            ResourceData: Resource data
            
        Raises:
            ValueError: If resource not found
        """
        resource = self.get_resource(resource_uri)
        if not resource:
            raise ValueError(f"Resource not found: {resource_uri}")
        
        try:
            data = await resource.read()
            logger.info(f"Resource {resource_uri} read successfully")
            return data
            
        except Exception as e:
            error_msg = f"Resource {resource_uri} read failed: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def clear(self) -> None:
        """Clear all registered resources."""
        self._resources.clear()
        logger.info("Cleared all resources from registry")
    
    def __len__(self) -> int:
        """Get number of registered resources."""
        return len(self._resources)
    
    def __contains__(self, resource_uri: str) -> bool:
        """Check if resource is registered."""
        return resource_uri in self._resources
    
    def __iter__(self):
        """Iterate over resource URIs."""
        return iter(self._resources.keys())


# Global resource registry instance
_resource_registry = ResourceRegistry()


def get_resource_registry() -> ResourceRegistry:
    """
    Get the global resource registry instance.
    
    Returns:
        ResourceRegistry: Global resource registry
    """
    return _resource_registry


def register_resource(resource: MCPResourceBase) -> None:
    """
    Register a resource in the global registry.
    
    Args:
        resource: Resource to register
    """
    _resource_registry.register(resource)


def get_resource(resource_uri: str) -> Optional[MCPResourceBase]:
    """
    Get a resource from the global registry.
    
    Args:
        resource_uri: URI of resource to get
        
    Returns:
        Optional[MCPResourceBase]: Resource instance or None if not found
    """
    return _resource_registry.get_resource(resource_uri)


def list_resources() -> List[str]:
    """
    List all resources in the global registry.
    
    Returns:
        List[str]: List of resource URIs
    """
    return _resource_registry.list_resources()


# Utility functions for common resource operations
def format_json_content(data: Dict[str, Any], pretty: bool = True) -> str:
    """
    Format dictionary as JSON string.
    
    Args:
        data: Data to format
        pretty: Whether to use pretty formatting
        
    Returns:
        str: JSON formatted string
    """
    import json
    
    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        return json.dumps(data, ensure_ascii=False)


def format_yaml_content(data: Dict[str, Any]) -> str:
    """
    Format dictionary as YAML string.
    
    Args:
        data: Data to format
        
    Returns:
        str: YAML formatted string
    """
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except ImportError:
        # Fallback to JSON if YAML is not available
        return format_json_content(data, pretty=True)


def format_table_content(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
    """
    Format list of dictionaries as table string.
    
    Args:
        data: Data to format as table
        headers: Optional custom headers
        
    Returns:
        str: Table formatted string
    """
    if not data:
        return "No data available"
    
    # Get headers
    if headers is None:
        headers = list(data[0].keys()) if data else []
    
    # Calculate column widths
    col_widths = {}
    for header in headers:
        col_widths[header] = len(str(header))
        for row in data:
            value = str(row.get(header, ""))
            col_widths[header] = max(col_widths[header], len(value))
    
    # Format table
    lines = []
    
    # Header row
    header_row = " | ".join(str(header).ljust(col_widths[header]) for header in headers)
    lines.append(header_row)
    
    # Separator row
    separator_row = " | ".join("-" * col_widths[header] for header in headers)
    lines.append(separator_row)
    
    # Data rows
    for row in data:
        data_row = " | ".join(str(row.get(header, "")).ljust(col_widths[header]) for header in headers)
        lines.append(data_row)
    
    return "\n".join(lines)