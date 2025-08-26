"""
Configuration resource.

This resource provides access to system configuration information.
"""

from typing import Dict, Any
from .base import MCPResourceBase, ResourceData, format_json_content


class ConfigResource(MCPResourceBase):
    """Configuration resource."""
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return "config://system"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return "System Configuration"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return "Access to system configuration settings and parameters"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read configuration data.
        
        Returns:
            ResourceData: Configuration information
        """
        try:
            # Get sanitized configuration (without sensitive data)
            config_data = self._get_sanitized_config()
            
            content = format_json_content(config_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "configuration",
                    "last_updated": self.settings.model_dump().get("timestamp"),
                    "environment": self.settings.environment,
                    "debug_mode": self.settings.debug
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error reading configuration: {str(e)}",
                metadata={"error": str(e)},
                mime_type="text/plain"
            )
    
    def _get_sanitized_config(self) -> Dict[str, Any]:
        """
        Get sanitized configuration without sensitive information.
        
        Returns:
            Dict[str, Any]: Sanitized configuration
        """
        config = self.settings.model_dump()
        
        # Remove sensitive information
        if "dashscope" in config:
            if "api_key" in config["dashscope"]:
                # Mask API key
                api_key = config["dashscope"]["api_key"]
                if len(api_key) > 8:
                    config["dashscope"]["api_key"] = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                else:
                    config["dashscope"]["api_key"] = "*" * len(api_key)
        
        # Add additional metadata
        config["_metadata"] = {
            "config_version": "1.0",
            "generated_at": "runtime",
            "sanitized": True,
            "description": "Aigroup Video MCP Configuration"
        }
        
        return config


class ConfigSectionResource(MCPResourceBase):
    """Configuration section resource for specific config sections."""
    
    def __init__(self, section: str):
        """
        Initialize configuration section resource.
        
        Args:
            section: Configuration section name
        """
        super().__init__()
        self.section = section
        
        # Validate section
        valid_sections = ["dashscope", "video", "mcp", "log", "security"]
        if section not in valid_sections:
            raise ValueError(f"Invalid config section: {section}. Valid sections: {valid_sections}")
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return f"config://system/{self.section}"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return f"{self.section.title()} Configuration"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return f"Access to {self.section} configuration settings"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read configuration section data.
        
        Returns:
            ResourceData: Configuration section information
        """
        try:
            # Get specific configuration section
            config_section = getattr(self.settings, self.section, None)
            if config_section is None:
                raise ValueError(f"Configuration section '{self.section}' not found")
            
            # Convert to dict and sanitize if needed
            section_data = config_section.model_dump()
            
            if self.section == "dashscope" and "api_key" in section_data:
                # Mask API key
                api_key = section_data["api_key"]
                if len(api_key) > 8:
                    section_data["api_key"] = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
                else:
                    section_data["api_key"] = "*" * len(api_key)
            
            content = format_json_content(section_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "configuration_section",
                    "section": self.section,
                    "environment": self.settings.environment,
                    "debug_mode": self.settings.debug
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error reading {self.section} configuration: {str(e)}",
                metadata={"error": str(e), "section": self.section},
                mime_type="text/plain"
            )