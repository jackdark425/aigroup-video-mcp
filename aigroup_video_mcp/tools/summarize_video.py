"""
Video summarization tool.

This tool provides video summarization functionality with different summary types.
"""

from typing import Dict, Any
from .base import VideoAnalysisTool, ToolOutput


class SummarizeVideoTool(VideoAnalysisTool):
    """Video summarization tool."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "summarize_video"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return "Generate intelligent summaries of video content with different detail levels"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Input schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "video_path": {
                    "type": "string",
                    "description": "Path to the video file or video URL",
                    "minLength": 1
                },
                "summary_type": {
                    "type": "string",
                    "description": "Type of summary to generate",
                    "enum": ["general", "detailed", "brief"],
                    "default": "general"
                },
                "model": {
                    "type": "string",
                    "description": "Model to use for analysis (optional)",
                    "default": "qwen-vl-max"
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature for text generation (optional, 0.0-2.0)",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.7
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens for response (optional)",
                    "minimum": 100,
                    "maximum": 4000,
                    "default": 1500
                }
            },
            "required": ["video_path"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute video summarization.
        
        Args:
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Summarization result
        """
        try:
            # Extract inputs
            video_path = inputs["video_path"]
            summary_type = inputs.get("summary_type", "general")
            
            # Optional parameters
            kwargs = {}
            if "model" in inputs:
                kwargs["model"] = inputs["model"]
            if "temperature" in inputs:
                kwargs["temperature"] = inputs["temperature"]
            if "max_tokens" in inputs:
                kwargs["max_tokens"] = inputs["max_tokens"]
            
            # Create video source
            video_source = self.create_video_source(video_path)
            
            # Generate summary
            result = await self.analyzer.summarize(video_source, summary_type, **kwargs)
            
            # Convert to tool output
            tool_output = self.analysis_result_to_tool_output(result)
            
            # Add tool-specific metadata
            tool_output.metadata.update({
                "tool_name": self.name,
                "video_path": video_path,
                "summary_type": summary_type,
                "analysis_type": "summarization"
            })
            
            return tool_output
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                metadata={
                    "tool_name": self.name,
                    "video_path": inputs.get("video_path", ""),
                    "summary_type": inputs.get("summary_type", "general"),
                    "analysis_type": "summarization"
                },
                error=str(e)
            )