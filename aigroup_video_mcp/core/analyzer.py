"""
Core video analysis module using Alibaba Cloud DashScope.

This module provides asynchronous video analysis functionality including
basic analysis, summarization, scene analysis, and custom prompt analysis.
"""

import asyncio
import os
import re
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse
from pathlib import Path

import dashscope
from dashscope import MultiModalConversation
from pydantic import BaseModel, Field, field_validator
from loguru import logger

from ..settings import get_settings, get_dashscope_settings, get_video_settings


class VideoSource(BaseModel):
    """Video source information."""
    
    type: str = Field(description="Source type: 'url' or 'file'")
    path: str = Field(description="Video path or URL")
    size: Optional[int] = Field(default=None, description="File size in bytes")
    duration: Optional[float] = Field(default=None, description="Duration in seconds")
    format: Optional[str] = Field(default=None, description="Video format")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate source type."""
        if v not in ['url', 'file']:
            raise ValueError("Source type must be 'url' or 'file'")
        return v
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Validate video path."""
        if not v.strip():
            raise ValueError("Video path cannot be empty")
        return v.strip()


class AnalysisResult(BaseModel):
    """Analysis result model."""
    
    success: bool = Field(description="Whether analysis was successful")
    content: str = Field(description="Analysis content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: float = Field(default_factory=time.time, description="Analysis timestamp")
    duration: Optional[float] = Field(default=None, description="Analysis duration")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class BaseVideoAnalyzer(ABC):
    """Base class for video analyzers."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.settings = get_settings()
        self.dashscope_settings = get_dashscope_settings()
        self.video_settings = get_video_settings()
        
        # Initialize DashScope
        dashscope.api_key = self.dashscope_settings.api_key
        dashscope.base_http_api_url = self.dashscope_settings.base_url
    
    @abstractmethod
    async def analyze(self, source: VideoSource, **kwargs) -> AnalysisResult:
        """Analyze video content."""
        pass
    
    def validate_video_source(self, source: VideoSource) -> bool:
        """
        Validate video source.
        
        Args:
            source: Video source to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValueError: If source is invalid
        """
        try:
            if source.type == "url":
                return self._validate_url(source.path)
            elif source.type == "file":
                return self._validate_file(source.path)
            else:
                raise ValueError(f"Unsupported source type: {source.type}")
        except Exception as e:
            logger.error(f"Video source validation failed: {e}")
            raise
    
    def _validate_url(self, url: str) -> bool:
        """Validate video URL."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            
            # Check allowed/blocked domains
            domain = parsed.netloc.lower()
            
            if self.settings.security.allowed_domains:
                if not any(allowed in domain for allowed in self.settings.security.allowed_domains):
                    raise ValueError(f"Domain not allowed: {domain}")
            
            if self.settings.security.blocked_domains:
                if any(blocked in domain for blocked in self.settings.security.blocked_domains):
                    raise ValueError(f"Domain blocked: {domain}")
            
            return True
        except Exception as e:
            logger.error(f"URL validation failed: {e}")
            raise
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate local video file."""
        try:
            path = Path(file_path)
            
            # Check if file exists
            if not path.exists():
                raise ValueError(f"File does not exist: {file_path}")
            
            # Check if it's a file
            if not path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.video_settings.max_file_size:
                raise ValueError(
                    f"File too large: {file_size} bytes "
                    f"(max: {self.video_settings.max_file_size} bytes)"
                )
            
            # Check file extension
            file_ext = path.suffix.lower().lstrip('.')
            if file_ext not in self.video_settings.supported_formats:
                raise ValueError(
                    f"Unsupported format: {file_ext} "
                    f"(supported: {', '.join(self.video_settings.supported_formats)})"
                )
            
            return True
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            raise
    
    def _prepare_dashscope_request(
        self, 
        source: VideoSource, 
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare DashScope API request."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"video": source.path},
                    {"text": prompt}
                ]
            }
        ]
        
        request_params = {
            "model": kwargs.get("model", self.dashscope_settings.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
        }
        
        return request_params


class AsyncVideoAnalyzer(BaseVideoAnalyzer):
    """Asynchronous video analyzer."""
    
    async def analyze(
        self, 
        source: VideoSource, 
        prompt: str = "请分析这个视频的内容。",
        **kwargs
    ) -> AnalysisResult:
        """
        Analyze video content with custom prompt.
        
        Args:
            source: Video source
            prompt: Analysis prompt
            **kwargs: Additional parameters
            
        Returns:
            AnalysisResult: Analysis result
        """
        start_time = time.time()
        
        try:
            # Validate source
            self.validate_video_source(source)
            
            # Prepare request
            request_params = self._prepare_dashscope_request(source, prompt, **kwargs)
            
            # Make API call with retry logic
            result = await self._call_dashscope_with_retry(request_params)
            
            duration = time.time() - start_time
            
            return AnalysisResult(
                success=True,
                content=result.get("content", ""),
                metadata={
                    "model": request_params["model"],
                    "source_type": source.type,
                    "source_path": source.path,
                    "prompt": prompt,
                    "request_params": request_params,
                    "raw_response": result
                },
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Video analysis failed: {error_msg}")
            
            return AnalysisResult(
                success=False,
                content="",
                metadata={
                    "source_type": source.type,
                    "source_path": source.path,
                    "prompt": prompt
                },
                duration=duration,
                error=error_msg
            )
    
    async def summarize(
        self, 
        source: VideoSource, 
        summary_type: str = "general",
        **kwargs
    ) -> AnalysisResult:
        """
        Generate video summary.
        
        Args:
            source: Video source
            summary_type: Type of summary ('general', 'detailed', 'brief')
            **kwargs: Additional parameters
            
        Returns:
            AnalysisResult: Summary result
        """
        prompts = {
            "general": "请为这个视频生成一个简洁明了的摘要，包括主要内容、关键场景和重要信息。",
            "detailed": "请为这个视频生成一个详细的摘要，包括：1) 视频概述 2) 主要场景描述 3) 关键人物或对象 4) 重要对话或文字信息 5) 总结。",
            "brief": "请用2-3句话简要概括这个视频的主要内容。"
        }
        
        prompt = prompts.get(summary_type, prompts["general"])
        return await self.analyze(source, prompt, **kwargs)
    
    async def analyze_scenes(
        self, 
        source: VideoSource, 
        scene_detection: bool = True,
        **kwargs
    ) -> AnalysisResult:
        """
        Analyze video scenes.
        
        Args:
            source: Video source
            scene_detection: Whether to detect scene transitions
            **kwargs: Additional parameters
            
        Returns:
            AnalysisResult: Scene analysis result
        """
        if scene_detection:
            prompt = (
                "请分析这个视频的场景结构，包括：\n"
                "1. 识别主要场景和场景转换\n"
                "2. 描述每个场景的内容和特点\n"
                "3. 分析场景之间的关系和逻辑\n"
                "4. 标注重要的时间点（如果可见）"
            )
        else:
            prompt = (
                "请描述这个视频中的主要场景，包括：\n"
                "1. 场景环境和背景\n"
                "2. 主要物体和人物\n"
                "3. 动作和事件\n"
                "4. 视觉特点和风格"
            )
        
        return await self.analyze(source, prompt, **kwargs)
    
    async def analyze_custom(
        self, 
        source: VideoSource, 
        custom_prompt: str,
        **kwargs
    ) -> AnalysisResult:
        """
        Analyze video with custom prompt.
        
        Args:
            source: Video source
            custom_prompt: Custom analysis prompt
            **kwargs: Additional parameters
            
        Returns:
            AnalysisResult: Analysis result
        """
        # Validate prompt length
        if len(custom_prompt) > self.settings.security.max_prompt_length:
            raise ValueError(
                f"Prompt too long: {len(custom_prompt)} characters "
                f"(max: {self.settings.security.max_prompt_length})"
            )
        
        return await self.analyze(source, custom_prompt, **kwargs)
    
    async def _call_dashscope_with_retry(self, request_params: Dict[str, Any]) -> Dict[str, Any]:
        """Call DashScope API with retry logic."""
        max_retries = self.dashscope_settings.max_retries
        retry_delay = self.dashscope_settings.retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Calling DashScope API (attempt {attempt + 1}/{max_retries + 1})")
                
                # Call DashScope API
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: MultiModalConversation.call(**request_params)
                )
                
                if response.status_code == 200:
                    output = response.output
                    if output and "choices" in output and output["choices"]:
                        content = output["choices"][0]["message"]["content"]
                        
                        # Handle both string and list format responses
                        if isinstance(content, list):
                            if content and isinstance(content[0], dict) and "text" in content[0]:
                                content = content[0]["text"]
                            else:
                                content = str(content)
                        elif not isinstance(content, str):
                            content = str(content)
                        return {
                            "content": content,
                            "usage": output.get("usage", {}),
                            "request_id": response.request_id
                        }
                    else:
                        raise ValueError("Empty response from DashScope API")
                else:
                    error_msg = f"DashScope API error: {response.status_code} - {response.message}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                    
            except Exception as e:
                logger.warning(f"DashScope API call failed (attempt {attempt + 1}): {e}")
                
                if attempt == max_retries:
                    raise e
                
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (attempt + 1))


class VideoAnalyzer:
    """Synchronous video analyzer (compatibility wrapper)."""
    
    def __init__(self):
        """Initialize synchronous analyzer."""
        self.async_analyzer = AsyncVideoAnalyzer()
    
    def analyze(self, source: VideoSource, prompt: str = "请分析这个视频的内容。", **kwargs) -> AnalysisResult:
        """Analyze video content (synchronous)."""
        return asyncio.run(self.async_analyzer.analyze(source, prompt, **kwargs))
    
    def summarize(self, source: VideoSource, summary_type: str = "general", **kwargs) -> AnalysisResult:
        """Generate video summary (synchronous)."""
        return asyncio.run(self.async_analyzer.summarize(source, summary_type, **kwargs))
    
    def analyze_scenes(self, source: VideoSource, scene_detection: bool = True, **kwargs) -> AnalysisResult:
        """Analyze video scenes (synchronous)."""
        return asyncio.run(self.async_analyzer.analyze_scenes(source, scene_detection, **kwargs))
    
    def analyze_custom(self, source: VideoSource, custom_prompt: str, **kwargs) -> AnalysisResult:
        """Analyze video with custom prompt (synchronous)."""
        return asyncio.run(self.async_analyzer.analyze_custom(source, custom_prompt, **kwargs))
    
    def validate_video_source(self, source: VideoSource) -> bool:
        """Validate video source (synchronous)."""
        return self.async_analyzer.validate_video_source(source)


# Utility functions
def create_video_source(path_or_url: str) -> VideoSource:
    """
    Create VideoSource from path or URL.
    
    Args:
        path_or_url: Video file path or URL
        
    Returns:
        VideoSource: Created video source
    """
    # Determine if it's a URL or file path
    if path_or_url.startswith(('http://', 'https://')):
        return VideoSource(type="url", path=path_or_url)
    else:
        path = Path(path_or_url)
        file_info = {}
        
        if path.exists():
            file_info["size"] = path.stat().st_size
            file_info["format"] = path.suffix.lower().lstrip('.')
        
        return VideoSource(type="file", path=str(path), **file_info)


def get_analyzer(async_mode: bool = True) -> Union[AsyncVideoAnalyzer, VideoAnalyzer]:
    """
    Get video analyzer instance.
    
    Args:
        async_mode: Whether to return async analyzer
        
    Returns:
        Union[AsyncVideoAnalyzer, VideoAnalyzer]: Analyzer instance
    """
    if async_mode:
        return AsyncVideoAnalyzer()
    else:
        return VideoAnalyzer()