"""
Models resource.

This resource provides information about available models and their capabilities.
"""

from typing import Dict, Any, List
import time
from .base import MCPResourceBase, ResourceData, format_json_content


class ModelsResource(MCPResourceBase):
    """Models resource."""
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return "models://available"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return "Available Models"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return "Information about available AI models and their capabilities"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read models information.
        
        Returns:
            ResourceData: Models information
        """
        try:
            models_data = self._get_models_info()
            
            content = format_json_content(models_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "models_info",
                    "total_models": len(models_data.get("models", [])),
                    "default_model": models_data.get("default_model"),
                    "generated_at": time.time()
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error reading models information: {str(e)}",
                metadata={"error": str(e)},
                mime_type="text/plain"
            )
    
    def _get_models_info(self) -> Dict[str, Any]:
        """
        Get information about available models.
        
        Returns:
            Dict[str, Any]: Models information
        """
        models_info = {
            "default_model": self.settings.dashscope.model,
            "provider": "DashScope (Alibaba Cloud)",
            "models": [
                {
                    "name": "qwen-vl-max",
                    "type": "multimodal",
                    "capabilities": [
                        "video_understanding",
                        "image_understanding", 
                        "text_generation",
                        "scene_analysis",
                        "object_detection",
                        "text_recognition"
                    ],
                    "max_video_duration": "10 minutes",
                    "supported_formats": self.settings.video.supported_formats,
                    "max_tokens": 4000,
                    "description": "Qwen-VL Max is a large-scale multimodal model with powerful video and image understanding capabilities",
                    "recommended_for": [
                        "general_video_analysis",
                        "detailed_scene_analysis", 
                        "content_summarization",
                        "educational_content_analysis"
                    ],
                    "is_default": True
                },
                {
                    "name": "qwen-vl-plus",
                    "type": "multimodal",
                    "capabilities": [
                        "video_understanding",
                        "image_understanding",
                        "text_generation",
                        "basic_scene_analysis"
                    ],
                    "max_video_duration": "5 minutes",
                    "supported_formats": self.settings.video.supported_formats,
                    "max_tokens": 2000,
                    "description": "Qwen-VL Plus offers balanced performance and cost for video understanding tasks",
                    "recommended_for": [
                        "basic_video_analysis",
                        "quick_summarization",
                        "content_classification"
                    ],
                    "is_default": False
                }
            ],
            "usage_guidelines": {
                "video_preprocessing": [
                    "Ensure video format is supported",
                    "Check video file size limits",
                    "Verify video duration limits",
                    "Consider video quality for better results"
                ],
                "prompt_optimization": [
                    "Use specific and clear prompts",
                    "Provide context when needed",
                    "Ask focused questions",
                    "Use structured prompts for complex analysis"
                ],
                "performance_tips": [
                    "Use appropriate temperature settings",
                    "Set reasonable token limits",
                    "Consider chunking for long videos",
                    "Use caching for repeated analysis"
                ]
            },
            "limitations": {
                "video_length": f"Maximum {self.settings.video.max_duration} seconds",
                "file_size": f"Maximum {self.settings.video.max_file_size // (1024*1024)}MB",
                "concurrent_requests": f"Maximum {self.settings.mcp.max_concurrent_requests} requests",
                "api_rate_limits": "Subject to DashScope API rate limits"
            },
            "metadata": {
                "last_updated": time.time(),
                "version": "1.0",
                "source": "aigroup-video-mcp"
            }
        }
        
        return models_info


class ModelCapabilitiesResource(MCPResourceBase):
    """Model capabilities resource for specific model."""
    
    def __init__(self, model_name: str):
        """
        Initialize model capabilities resource.
        
        Args:
            model_name: Name of the model
        """
        super().__init__()
        self.model_name = model_name
    
    @property
    def uri(self) -> str:
        """Resource URI."""
        return f"models://{self.model_name}/capabilities"
    
    @property
    def name(self) -> str:
        """Resource name."""
        return f"{self.model_name} Capabilities"
    
    @property
    def description(self) -> str:
        """Resource description."""
        return f"Detailed capabilities and specifications for {self.model_name} model"
    
    @property
    def mime_type(self) -> str:
        """Resource MIME type."""
        return "application/json"
    
    async def read(self) -> ResourceData:
        """
        Read model capabilities.
        
        Returns:
            ResourceData: Model capabilities information
        """
        try:
            capabilities_data = self._get_model_capabilities()
            
            if not capabilities_data:
                return ResourceData(
                    content=f"Model '{self.model_name}' not found",
                    metadata={"error": "model_not_found", "model_name": self.model_name},
                    mime_type="text/plain"
                )
            
            content = format_json_content(capabilities_data, pretty=True)
            
            return ResourceData(
                content=content,
                metadata={
                    "resource_type": "model_capabilities",
                    "model_name": self.model_name,
                    "generated_at": time.time()
                },
                mime_type=self.mime_type
            )
            
        except Exception as e:
            return ResourceData(
                content=f"Error reading capabilities for {self.model_name}: {str(e)}",
                metadata={"error": str(e), "model_name": self.model_name},
                mime_type="text/plain"
            )
    
    def _get_model_capabilities(self) -> Dict[str, Any]:
        """
        Get detailed capabilities for specific model.
        
        Returns:
            Dict[str, Any]: Model capabilities or None if not found
        """
        # Get all models info
        models_info = ModelsResource()._get_models_info()
        
        # Find the specific model
        for model in models_info.get("models", []):
            if model["name"] == self.model_name:
                # Return detailed capabilities
                return {
                    "model_name": self.model_name,
                    "basic_info": {
                        "type": model["type"],
                        "description": model["description"],
                        "is_default": model["is_default"]
                    },
                    "capabilities": model["capabilities"],
                    "technical_specs": {
                        "max_video_duration": model["max_video_duration"],
                        "supported_formats": model["supported_formats"],
                        "max_tokens": model["max_tokens"]
                    },
                    "recommended_use_cases": model["recommended_for"],
                    "parameters": {
                        "temperature_range": "0.0 - 2.0",
                        "default_temperature": 0.7,
                        "top_p_range": "0.0 - 1.0", 
                        "default_top_p": 0.9,
                        "supports_streaming": False
                    },
                    "performance_characteristics": {
                        "typical_response_time": "5-30 seconds",
                        "accuracy_level": "high" if self.model_name == "qwen-vl-max" else "medium",
                        "cost_efficiency": "medium" if self.model_name == "qwen-vl-max" else "high"
                    },
                    "metadata": {
                        "last_updated": time.time(),
                        "source": "aigroup-video-mcp"
                    }
                }
        
        return None