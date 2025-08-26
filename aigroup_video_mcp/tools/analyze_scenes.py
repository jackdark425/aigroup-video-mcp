"""
Video scene analysis tool.

This tool provides video scene analysis and scene transition detection functionality.
"""

from typing import Dict, Any
from .base import VideoAnalysisTool, ToolOutput


class AnalyzeVideoScenesTool(VideoAnalysisTool):
    """Video scene analysis tool."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "analyze_video_scenes"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return "Analyze video scenes, detect scene transitions, and describe scene content and structure"
    
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
                "scene_detection": {
                    "type": "boolean",
                    "description": "Whether to detect scene transitions",
                    "default": True
                },
                "detailed_analysis": {
                    "type": "boolean",
                    "description": "Whether to provide detailed scene analysis",
                    "default": False
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
                    "default": 2500
                }
            },
            "required": ["video_path"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute video scene analysis.
        
        Args:
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Scene analysis result
        """
        try:
            # Extract inputs
            video_path = inputs["video_path"]
            scene_detection = inputs.get("scene_detection", True)
            detailed_analysis = inputs.get("detailed_analysis", False)
            
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
            
            # Analyze scenes
            result = await self.analyzer.analyze_scenes(
                video_source, 
                scene_detection=scene_detection, 
                **kwargs
            )
            
            # If detailed analysis is requested and the initial analysis succeeded,
            # we can enhance the result with additional analysis
            if detailed_analysis and result.success:
                # Create an enhanced prompt for detailed analysis
                enhanced_prompt = (
                    "基于之前的场景分析，请提供更详细的分析，包括：\n"
                    "1. 每个场景的具体时长估计\n"
                    "2. 场景中的视觉元素详细描述\n"
                    "3. 场景间的逻辑关系和叙事结构\n"
                    "4. 摄影技巧和视觉风格分析\n"
                    "5. 场景的情感色调和氛围\n"
                    f"原始分析结果：{result.content}"
                )
                
                enhanced_result = await self.analyzer.analyze(
                    video_source, 
                    enhanced_prompt, 
                    **kwargs
                )
                
                if enhanced_result.success:
                    result = enhanced_result
                    result.metadata["enhanced_analysis"] = True
            
            # Convert to tool output
            tool_output = self.analysis_result_to_tool_output(result)
            
            # Add tool-specific metadata
            tool_output.metadata.update({
                "tool_name": self.name,
                "video_path": video_path,
                "scene_detection": scene_detection,
                "detailed_analysis": detailed_analysis,
                "analysis_type": "scene_analysis"
            })
            
            return tool_output
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                metadata={
                    "tool_name": self.name,
                    "video_path": inputs.get("video_path", ""),
                    "scene_detection": inputs.get("scene_detection", True),
                    "detailed_analysis": inputs.get("detailed_analysis", False),
                    "analysis_type": "scene_analysis"
                },
                error=str(e)
            )