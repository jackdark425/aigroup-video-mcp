"""
Video source validation tool.

This tool provides video source validation functionality to check
if a video source is valid and accessible before analysis.
"""

from typing import Dict, Any
from pathlib import Path
from urllib.parse import urlparse
import os
from .base import VideoAnalysisTool, ToolOutput


class ValidateVideoSourceTool(VideoAnalysisTool):
    """Video source validation tool."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "validate_video_source"
    
    @property
    def description(self) -> str:
        """Tool description."""
        return "Validate video source (file or URL) to check accessibility, format, size, and other requirements"
    
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
                "check_accessibility": {
                    "type": "boolean",
                    "description": "Whether to check if the video is accessible",
                    "default": True
                },
                "check_format": {
                    "type": "boolean",
                    "description": "Whether to check video format compatibility",
                    "default": True
                },
                "check_size": {
                    "type": "boolean",
                    "description": "Whether to check video file size limits",
                    "default": True
                },
                "detailed_info": {
                    "type": "boolean",
                    "description": "Whether to return detailed video information",
                    "default": False
                }
            },
            "required": ["video_path"]
        }
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolOutput:
        """
        Execute video source validation.
        
        Args:
            inputs: Tool input parameters
            
        Returns:
            ToolOutput: Validation result
        """
        try:
            # Extract inputs
            video_path = inputs["video_path"]
            check_accessibility = inputs.get("check_accessibility", True)
            check_format = inputs.get("check_format", True)
            check_size = inputs.get("check_size", True)
            detailed_info = inputs.get("detailed_info", False)
            
            # Create video source
            video_source = self.create_video_source(video_path)
            
            # Perform validation
            validation_result = self._validate_source(
                video_source,
                check_accessibility=check_accessibility,
                check_format=check_format,
                check_size=check_size,
                detailed_info=detailed_info
            )
            
            return ToolOutput(
                success=validation_result["valid"],
                content=validation_result["message"],
                metadata={
                    "tool_name": self.name,
                    "video_path": video_path,
                    "source_type": video_source.type,
                    "validation_checks": {
                        "accessibility": check_accessibility,
                        "format": check_format,
                        "size": check_size,
                        "detailed_info": detailed_info
                    },
                    "validation_results": validation_result,
                    "analysis_type": "source_validation"
                }
            )
            
        except Exception as e:
            return ToolOutput(
                success=False,
                content=f"验证过程中发生错误：{str(e)}",
                metadata={
                    "tool_name": self.name,
                    "video_path": inputs.get("video_path", ""),
                    "analysis_type": "source_validation"
                },
                error=str(e)
            )
    
    def _validate_source(
        self, 
        video_source,
        check_accessibility: bool = True,
        check_format: bool = True,
        check_size: bool = True,
        detailed_info: bool = False
    ) -> Dict[str, Any]:
        """
        Validate video source with specified checks.
        
        Args:
            video_source: VideoSource to validate
            check_accessibility: Whether to check accessibility
            check_format: Whether to check format
            check_size: Whether to check size
            detailed_info: Whether to return detailed info
            
        Returns:
            Dict[str, Any]: Validation result
        """
        result = {
            "valid": True,
            "message": "",
            "details": {},
            "issues": [],
            "warnings": []
        }
        
        try:
            if video_source.type == "url":
                self._validate_url_source(
                    video_source, result, check_accessibility, detailed_info
                )
            elif video_source.type == "file":
                self._validate_file_source(
                    video_source, result, check_accessibility, 
                    check_format, check_size, detailed_info
                )
            
            # Generate final message
            if result["valid"]:
                if result["warnings"]:
                    result["message"] = (
                        f"视频源验证通过，但有以下警告：\n" +
                        "\n".join(f"⚠️ {warning}" for warning in result["warnings"])
                    )
                else:
                    result["message"] = "✅ 视频源验证通过，所有检查都符合要求。"
                
                if detailed_info and result["details"]:
                    result["message"] += f"\n\n详细信息：\n{self._format_details(result['details'])}"
            else:
                result["message"] = (
                    f"❌ 视频源验证失败：\n" +
                    "\n".join(f"• {issue}" for issue in result["issues"])
                )
                
                if result["warnings"]:
                    result["message"] += (
                        f"\n\n警告：\n" +
                        "\n".join(f"⚠️ {warning}" for warning in result["warnings"])
                    )
        
        except Exception as e:
            result["valid"] = False
            result["message"] = f"验证过程中发生错误：{str(e)}"
            result["issues"].append(str(e))
        
        return result
    
    def _validate_url_source(
        self, 
        video_source, 
        result: Dict[str, Any], 
        check_accessibility: bool, 
        detailed_info: bool
    ) -> None:
        """Validate URL video source."""
        try:
            parsed = urlparse(video_source.path)
            
            # Basic URL format check
            if not parsed.scheme or not parsed.netloc:
                result["valid"] = False
                result["issues"].append("URL格式无效")
                return
            
            # Check allowed/blocked domains
            domain = parsed.netloc.lower()
            
            if self.analyzer.settings.security.allowed_domains:
                if not any(allowed in domain for allowed in self.analyzer.settings.security.allowed_domains):
                    result["valid"] = False
                    result["issues"].append(f"域名不在允许列表中：{domain}")
                    return
            
            if self.analyzer.settings.security.blocked_domains:
                if any(blocked in domain for blocked in self.analyzer.settings.security.blocked_domains):
                    result["valid"] = False
                    result["issues"].append(f"域名在禁止列表中：{domain}")
                    return
            
            if detailed_info:
                result["details"]["url_info"] = {
                    "scheme": parsed.scheme,
                    "domain": domain,
                    "path": parsed.path,
                    "full_url": video_source.path
                }
            
            # Accessibility check would require actually trying to access the URL
            # For now, we'll just mark it as passed if format is valid
            if check_accessibility:
                result["warnings"].append("URL可访问性检查需要实际网络请求，请确保URL有效")
            
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"URL验证失败：{str(e)}")
    
    def _validate_file_source(
        self, 
        video_source, 
        result: Dict[str, Any], 
        check_accessibility: bool,
        check_format: bool,
        check_size: bool,
        detailed_info: bool
    ) -> None:
        """Validate file video source."""
        try:
            path = Path(video_source.path)
            
            # Check if file exists
            if check_accessibility:
                if not path.exists():
                    result["valid"] = False
                    result["issues"].append(f"文件不存在：{video_source.path}")
                    return
                
                if not path.is_file():
                    result["valid"] = False
                    result["issues"].append(f"路径不是文件：{video_source.path}")
                    return
            
            # Check file format
            if check_format:
                file_ext = path.suffix.lower().lstrip('.')
                if file_ext not in self.analyzer.video_settings.supported_formats:
                    result["valid"] = False
                    result["issues"].append(
                        f"不支持的视频格式：{file_ext}（支持的格式：{', '.join(self.analyzer.video_settings.supported_formats)}）"
                    )
                    return
            
            # Check file size
            if check_size and path.exists():
                file_size = path.stat().st_size
                max_size = self.analyzer.video_settings.max_file_size
                
                if file_size > max_size:
                    result["valid"] = False
                    result["issues"].append(
                        f"文件过大：{self._format_size(file_size)}（最大允许：{self._format_size(max_size)}）"
                    )
                    return
                elif file_size > max_size * 0.8:  # Warning at 80% of limit
                    result["warnings"].append(
                        f"文件较大：{self._format_size(file_size)}，接近大小限制"
                    )
            
            if detailed_info and path.exists():
                stat = path.stat()
                result["details"]["file_info"] = {
                    "path": str(path.absolute()),
                    "size": stat.st_size,
                    "size_formatted": self._format_size(stat.st_size),
                    "extension": path.suffix.lower(),
                    "modified_time": stat.st_mtime,
                    "is_readable": os.access(path, os.R_OK)
                }
        
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"文件验证失败：{str(e)}")
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"
    
    def _format_details(self, details: Dict[str, Any]) -> str:
        """Format details dictionary as readable text."""
        formatted = []
        for section, data in details.items():
            formatted.append(f"{section}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    formatted.append(f"  {key}: {value}")
            else:
                formatted.append(f"  {data}")
        return "\n".join(formatted)