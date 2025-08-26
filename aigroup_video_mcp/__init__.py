"""
Aigroup Video MCP - A MCP server for video multimodal understanding

This package provides a Model Context Protocol (MCP) server that integrates
with Alibaba Cloud DashScope for video content analysis and understanding.

Features:
- Video content analysis
- Intelligent summarization
- Scene recognition
- Custom prompt analysis
- MCP protocol support
"""

__version__ = "1.1.0"
__author__ = "Aigroup Team"
__email__ = "team@aigroup.com"

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings", "__version__"]