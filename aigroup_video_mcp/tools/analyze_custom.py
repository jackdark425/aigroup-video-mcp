"""
Custom video analysis tool.

This tool provides flexible video analysis with custom prompts.
"""

from typing import Dict, Any
from .base import VideoAnalysisTool, ToolOutput


class AnalyzeVideoCustomTool(VideoAnalysisTool):
    """Custom video analysis tool."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "analyze_video_custom"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return "Analyze video content with fully customizable prompts for specific analysis needs"
    
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
                "custom_prompt": {
                    "type": "string",
                    "description": "Custom analysis prompt describing what you want to analyze",
                    "minLength": 5,
                    "maxLength": 10000
                },
                "analysis_focus": {
                    "type": "string",
                    "description": "Focus area for analysis (optional)",
                    "enum": [
                        "content", "technical", "emotional", "educational", 
                        "commercial", "artistic", "narrative", "characters",
                        "objects", "text", "audio", "movement", "colors",
                        "lighting", "composition", "quality", "accessibility"
                    ]
                },
                "output_format": {
                    "type": "string",
                    "description": "Desired output format (optional)",
                    "enum": ["paragraph", "bullet_points", "structured", "json", "table"],
                    "default": "paragraph"
                },
                "language": {
                    "type": "string",
                    "description": "Output language (optional)",
                    "enum": ["zh-CN", "en", "auto"],
                    "default": "zh-CN"
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
            "required": ["video_path", "custom_prompt"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute custom video analysis.
        
        Args:
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Custom analysis result
        """
        try:
            # Extract inputs
            video_path = inputs["video_path"]
            custom_prompt = inputs["custom_prompt"]
            analysis_focus = inputs.get("analysis_focus")
            output_format = inputs.get("output_format", "paragraph")
            language = inputs.get("language", "zh-CN")
            
            # Enhance the prompt based on additional parameters
            enhanced_prompt = self._enhance_prompt(
                custom_prompt, 
                analysis_focus, 
                output_format, 
                language
            )
            
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
            
            # Analyze with custom prompt
            result = await self.analyzer.analyze_custom(
                video_source, 
                enhanced_prompt, 
                **kwargs
            )
            
            # Convert to tool output
            tool_output = self.analysis_result_to_tool_output(result)
            
            # Add tool-specific metadata
            tool_output.metadata.update({
                "tool_name": self.name,
                "video_path": video_path,
                "custom_prompt": custom_prompt,
                "analysis_focus": analysis_focus,
                "output_format": output_format,
                "language": language,
                "enhanced_prompt": enhanced_prompt,
                "analysis_type": "custom_analysis"
            })
            
            return tool_output
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content="",
                metadata={
                    "tool_name": self.name,
                    "video_path": inputs.get("video_path", ""),
                    "custom_prompt": inputs.get("custom_prompt", ""),
                    "analysis_focus": inputs.get("analysis_focus"),
                    "output_format": inputs.get("output_format", "paragraph"),
                    "language": inputs.get("language", "zh-CN"),
                    "analysis_type": "custom_analysis"
                },
                error=str(e)
            )
    
    def _enhance_prompt(
        self, 
        custom_prompt: str, 
        analysis_focus: str = None,
        output_format: str = "paragraph",
        language: str = "zh-CN"
    ) -> str:
        """
        Enhance the custom prompt with additional instructions.
        
        Args:
            custom_prompt: Original custom prompt
            analysis_focus: Analysis focus area
            output_format: Desired output format
            language: Output language
            
        Returns:
            str: Enhanced prompt
        """
        enhanced_parts = []
        
        # Language instruction
        if language == "zh-CN":
            enhanced_parts.append("请用中文回答。")
        elif language == "en":
            enhanced_parts.append("Please respond in English.")
        elif language == "auto":
            enhanced_parts.append("请根据视频内容选择合适的语言回答。")
        
        # Focus instruction
        if analysis_focus:
            focus_instructions = {
                "content": "重点关注视频的内容信息，包括主题、情节、信息等。",
                "technical": "重点关注视频的技术方面，包括画质、音质、编码、格式等。",
                "emotional": "重点关注视频的情感表达，包括情感色调、氛围、感受等。",
                "educational": "重点关注视频的教育价值，包括学习要点、知识传递等。",
                "commercial": "重点关注视频的商业元素，包括品牌、产品、营销信息等。",
                "artistic": "重点关注视频的艺术价值，包括美学、创意、视觉风格等。",
                "narrative": "重点关注视频的叙事结构，包括故事线、情节发展等。",
                "characters": "重点关注视频中的人物，包括外观、行为、角色等。",
                "objects": "重点关注视频中的物体，包括道具、场景元素等。",
                "text": "重点关注视频中的文字信息，包括字幕、标题、文字内容等。",
                "audio": "重点关注视频的音频内容，包括对话、音乐、音效等。",
                "movement": "重点关注视频中的动作和运动，包括人物动作、镜头运动等。",
                "colors": "重点关注视频的色彩，包括色调、配色、色彩效果等。",
                "lighting": "重点关注视频的光照，包括光线效果、明暗对比等。",
                "composition": "重点关注视频的构图，包括画面布局、视觉构成等。",
                "quality": "重点关注视频质量，包括清晰度、稳定性、压缩效果等。",
                "accessibility": "重点关注视频的可访问性，包括字幕、音频描述等。"
            }
            
            if analysis_focus in focus_instructions:
                enhanced_parts.append(focus_instructions[analysis_focus])
        
        # Output format instruction
        format_instructions = {
            "paragraph": "请以段落形式组织回答。",
            "bullet_points": "请以要点列表的形式组织回答。",
            "structured": "请以结构化的方式组织回答，使用标题和子标题。",
            "json": "请以JSON格式组织回答。",
            "table": "请以表格形式组织回答（如果适用）。"
        }
        
        if output_format in format_instructions:
            enhanced_parts.append(format_instructions[output_format])
        
        # Combine all parts
        enhanced_parts.append(custom_prompt)
        
        return " ".join(enhanced_parts)