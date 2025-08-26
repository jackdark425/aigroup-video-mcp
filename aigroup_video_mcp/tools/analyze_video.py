"""
Basic video analysis tool.

This tool provides basic video content analysis functionality.
"""

from typing import Dict, Any
from .base import VideoAnalysisTool, ToolOutput


class AnalyzeVideoTool(VideoAnalysisTool):
    """Basic video analysis tool."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "analyze_video"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return "Analyze video content and provide a comprehensive description of what's happening in the video"
    
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
                "prompt": {
                    "type": "string",
                    "description": "Custom analysis prompt (optional)",
                    "default": "请分析这个视频的内容，包括主要场景、人物、动作和事件。"
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
                    "default": 2000
                }
            },
            "required": ["video_path"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute video analysis.
        
        Args:
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Analysis result
        """
        try:
            # Extract inputs
            video_path = inputs["video_path"]
            prompt = inputs.get("prompt", "请分析这个视频的内容，包括主要场景、人物、动作和事件。")
            
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
            
            # Analyze video
            result = await self.analyzer.analyze(video_source, prompt, **kwargs)
            
            # Convert to tool output
            tool_output = self.analysis_result_to_tool_output(result)
            
            # Add tool-specific metadata
            tool_output.metadata.update({
                "tool_name": self.name,
                "video_path": video_path,
                "prompt": prompt,
                "analysis_type": "basic_analysis"
            })
            
            return tool_output
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                metadata={
                    "tool_name": self.name,
                    "video_path": inputs.get("video_path", ""),
                    "analysis_type": "basic_analysis"
                },
                error=str(e)
            )