"""
Tools module for MCP video analysis tools.

This module contains all the video analysis tools that can be called
through the MCP protocol.
"""

from .base import VideoAnalysisTool, ToolRegistry
from .analyze_video import AnalyzeVideoTool
from .summarize_video import SummarizeVideoTool
from .analyze_scenes import AnalyzeVideoScenesTool
from .analyze_custom import AnalyzeVideoCustomTool
from .validate_source import ValidateVideoSourceTool

__all__ = [
    "VideoAnalysisTool",
    "ToolRegistry", 
    "AnalyzeVideoTool",
    "SummarizeVideoTool",
    "AnalyzeVideoScenesTool",
    "AnalyzeVideoCustomTool",
    "ValidateVideoSourceTool",
]