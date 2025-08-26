"""
Configuration management module.

This module provides configuration management based on Pydantic v2,
supporting environment variables and configuration files.
"""

import os
from functools import lru_cache
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DashScopeSettings(BaseModel):
    """DashScope API configuration."""
    
    api_key: str = Field(
        description="DashScope API key",
        min_length=1
    )
    base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1",
        description="DashScope API base URL"
    )
    model: str = Field(
        default="qwen-vl-max",
        description="Default model for video analysis"
    )
    timeout: int = Field(
        default=300,
        ge=1,
        le=1800,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries"
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between retries in seconds"
    )


class VideoSettings(BaseModel):
    """Video processing configuration."""
    
    max_file_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        ge=1024,
        description="Maximum video file size in bytes"
    )
    supported_formats: List[str] = Field(
        default=["mp4", "avi", "mov", "mkv", "webm", "flv"],
        description="Supported video formats"
    )
    max_duration: int = Field(
        default=3600,  # 1 hour
        ge=1,
        description="Maximum video duration in seconds"
    )
    frame_sampling_rate: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Frame sampling rate for analysis"
    )
    quality_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Video quality threshold"
    )


class MCPSettings(BaseModel):
    """MCP service configuration."""
    
    server_name: str = Field(
        default="aigroup-video-mcp",
        description="MCP server name"
    )
    version: str = Field(
        default="0.1.0",
        description="MCP server version"
    )
    description: str = Field(
        default="A MCP server for video multimodal understanding",
        description="MCP server description"
    )
    transport: str = Field(
        default="stdio",
        description="MCP transport method"
    )
    max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent requests"
    )
    request_timeout: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="Request timeout in seconds"
    )


class LogSettings(BaseModel):
    """Logging configuration."""
    
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Log level"
    )
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="Log format"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Log file path (optional)"
    )
    max_file_size: str = Field(
        default="10 MB",
        description="Maximum log file size"
    )
    rotation: str = Field(
        default="1 week",
        description="Log rotation period"
    )
    retention: str = Field(
        default="1 month",
        description="Log retention period"
    )
    enable_console: bool = Field(
        default=True,
        description="Enable console logging"
    )


class SecuritySettings(BaseModel):
    """Security configuration."""
    
    enable_rate_limiting: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        ge=1,
        description="Number of requests per time window"
    )
    rate_limit_window: int = Field(
        default=3600,  # 1 hour
        ge=1,
        description="Rate limit time window in seconds"
    )
    enable_input_validation: bool = Field(
        default=True,
        description="Enable input validation"
    )
    max_prompt_length: int = Field(
        default=10000,
        ge=1,
        description="Maximum prompt length"
    )
    allowed_domains: List[str] = Field(
        default=[],
        description="Allowed domains for video URLs"
    )
    blocked_domains: List[str] = Field(
        default=[],
        description="Blocked domains for video URLs"
    )

    @field_validator('allowed_domains', 'blocked_domains')
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        """Validate domain lists."""
        return [domain.lower().strip() for domain in v if domain.strip()]


class Settings(BaseSettings):
    """Main settings class combining all configuration sections."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Sub-configurations
    dashscope: DashScopeSettings = Field(
        default_factory=lambda: DashScopeSettings(
            api_key=os.getenv("DASHSCOPE_API_KEY", "")
        )
    )
    video: VideoSettings = Field(default_factory=VideoSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)
    log: LogSettings = Field(default_factory=LogSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    # Environment
    environment: str = Field(
        default="production",
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing."""
        # Validate DashScope API key
        if not self.dashscope.api_key:
            raise ValueError(
                "DashScope API key is required. "
                "Please set DASHSCOPE_API_KEY environment variable."
            )
        
        # Adjust log level for debug mode
        if self.debug and self.log.level == LogLevel.INFO:
            self.log.level = LogLevel.DEBUG
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.model_dump()
    
    def get_dashscope_config(self) -> Dict[str, Any]:
        """Get DashScope configuration."""
        return {
            "api_key": self.dashscope.api_key,
            "base_url": self.dashscope.base_url,
            "timeout": self.dashscope.timeout,
            "max_retries": self.dashscope.max_retries,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (Singleton pattern).
    
    Returns:
        Settings: Cached settings instance
    """
    return Settings()


# Export commonly used settings getters
def get_dashscope_settings() -> DashScopeSettings:
    """Get DashScope settings."""
    return get_settings().dashscope


def get_video_settings() -> VideoSettings:
    """Get video settings."""
    return get_settings().video


def get_mcp_settings() -> MCPSettings:
    """Get MCP settings."""
    return get_settings().mcp


def get_log_settings() -> LogSettings:
    """Get log settings."""
    return get_settings().log


def get_security_settings() -> SecuritySettings:
    """Get security settings."""
    return get_settings().security