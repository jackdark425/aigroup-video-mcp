"""
Main entry point for Aigroup Video MCP server.

This module provides the command-line interface and main entry points
for running the video analysis MCP server.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import argparse
import json

from loguru import logger

from .server.mcp_server import (
    create_server,
    run_stdio_server,
    run_sse_server,
    managed_server
)
from .settings import get_settings
from .core.analyzer import get_analyzer, create_video_source
from . import __version__


class CLIError(Exception):
    """CLI specific error."""
    pass


async def cmd_server_stdio() -> None:
    """Run MCP server with stdio transport."""
    try:
        logger.info("Starting Aigroup Video MCP server (stdio mode)")
        await run_stdio_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


async def cmd_server_sse(host: str = "localhost", port: int = 3001) -> None:
    """Run MCP server with SSE transport."""
    try:
        logger.info(f"Starting Aigroup Video MCP server (SSE mode) on {host}:{port}")
        await run_sse_server(host, port)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


async def cmd_health_check() -> None:
    """Perform server health check."""
    try:
        async with managed_server() as server:
            health = await server.health_check()
            
            print(json.dumps(health, indent=2, ensure_ascii=False))
            
            if health["status"] != "healthy":
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        sys.exit(1)


async def cmd_server_info() -> None:
    """Show server information."""
    try:
        async with managed_server() as server:
            info = server.get_server_info()
            print(json.dumps(info, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        sys.exit(1)


def cmd_config_check() -> None:
    """Validate configuration."""
    try:
        settings = get_settings()
        print("Configuration validation successful ✅")
        print(f"Environment: {settings.environment}")
        print(f"Debug mode: {settings.debug}")
        print(f"DashScope API key: {'configured' if settings.dashscope.api_key else 'missing'}")
        print(f"Supported video formats: {', '.join(settings.video.supported_formats)}")
        print(f"Max file size: {settings.video.max_file_size // (1024*1024)}MB")
        
    except Exception as e:
        print(f"Configuration validation failed ❌: {e}")
        sys.exit(1)


async def cmd_analyze_video(
    video_path: str,
    prompt: Optional[str] = None,
    output_format: str = "text",
    save_to: Optional[str] = None
) -> None:
    """Analyze video using the core analyzer (for testing)."""
    try:
        # Create analyzer
        analyzer = get_analyzer(async_mode=True)
        
        # Create video source
        video_source = create_video_source(video_path)
        
        # Set default prompt
        if not prompt:
            prompt = "请分析这个视频的内容，包括主要场景、人物、动作和事件。"
        
        print(f"Analyzing video: {video_path}")
        print(f"Prompt: {prompt}")
        print("Processing...")
        
        # Analyze video
        result = await analyzer.analyze(video_source, prompt)
        
        # Format output
        if output_format == "json":
            output = {
                "success": result.success,
                "content": result.content,
                "metadata": result.metadata,
                "error": result.error
            }
            output_text = json.dumps(output, indent=2, ensure_ascii=False)
        else:  # text format
            output_text = f"Analysis Result:\n{'='*50}\n"
            if result.success:
                output_text += result.content
                if result.metadata:
                    output_text += f"\n\nMetadata:\n{json.dumps(result.metadata, indent=2, ensure_ascii=False)}"
            else:
                output_text += f"Analysis failed: {result.error}"
        
        # Output result
        if save_to:
            Path(save_to).write_text(output_text, encoding='utf-8')
            print(f"Result saved to: {save_to}")
        else:
            print(output_text)
        
        if not result.success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        sys.exit(1)


def cmd_version() -> None:
    """Show version information."""
    print(f"Aigroup Video MCP v{__version__}")
    print("A MCP server for video multimodal understanding")
    print("Based on Alibaba Cloud DashScope")


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Setup logging configuration."""
    try:
        settings = get_settings()
        log_settings = settings.log
        
        # Remove default logger
        logger.remove()
        
        # Configure log level
        if debug:
            log_level = "DEBUG"
        else:
            log_level = log_settings.level.value
        
        # Console logging
        if log_settings.enable_console:
            logger.add(
                sys.stderr,
                level=log_level,
                format=log_settings.format,
                colorize=True
            )
        
        # File logging
        if log_file or log_settings.file_path:
            file_path = log_file or log_settings.file_path
            logger.add(
                file_path,
                level=log_level,
                format=log_settings.format,
                rotation=log_settings.rotation,
                retention=log_settings.retention,
                compression="gz"
            )
        
    except Exception as e:
        # Fallback to basic logging
        logger.remove()
        logger.add(sys.stderr, level="INFO", colorize=True)
        logger.warning(f"Failed to setup logging: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="aigroup-video-mcp",
        description="Aigroup Video MCP - A MCP server for video multimodal understanding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start MCP server (stdio mode)
  aigroup-video-mcp serve

  # Start SSE server
  aigroup-video-mcp serve --transport sse --host 0.0.0.0 --port 3001

  # Check server health
  aigroup-video-mcp health

  # Validate configuration
  aigroup-video-mcp config

  # Analyze a video file
  aigroup-video-mcp analyze video.mp4 --prompt "描述视频内容"

  # Show version
  aigroup-video-mcp version
        """
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"aigroup-video-mcp {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Server command
    serve_parser = subparsers.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport method (default: stdio)"
    )
    serve_parser.add_argument(
        "--host",
        default="localhost",
        help="Host for SSE server (default: localhost)"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=3001,
        help="Port for SSE server (default: 3001)"
    )
    
    # Health check command
    subparsers.add_parser("health", help="Perform server health check")
    
    # Server info command
    subparsers.add_parser("info", help="Show server information")
    
    # Config check command
    subparsers.add_parser("config", help="Validate configuration")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze video (for testing)")
    analyze_parser.add_argument("video_path", help="Path to video file or URL")
    analyze_parser.add_argument(
        "--prompt",
        help="Analysis prompt"
    )
    analyze_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    analyze_parser.add_argument(
        "--save-to",
        help="Save result to file"
    )
    
    # Version command
    subparsers.add_parser("version", help="Show version information")
    
    return parser


async def async_main() -> None:
    """Async main function."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(debug=args.debug, log_file=args.log_file)
    
    # Handle commands
    try:
        if args.command == "serve":
            if args.transport == "stdio":
                await cmd_server_stdio()
            elif args.transport == "sse":
                await cmd_server_sse(args.host, args.port)
        
        elif args.command == "health":
            await cmd_health_check()
        
        elif args.command == "info":
            await cmd_server_info()
        
        elif args.command == "config":
            cmd_config_check()
        
        elif args.command == "analyze":
            await cmd_analyze_video(
                args.video_path,
                args.prompt,
                args.format,
                args.save_to
            )
        
        elif args.command == "version":
            cmd_version()
        
        else:
            # No command specified, default to serve stdio
            await cmd_server_stdio()
    
    except CLIError as e:
        logger.error(f"CLI error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.debug:
            raise
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("Error: Python 3.8 or higher is required")
            sys.exit(1)
        
        # Check if DASHSCOPE_API_KEY is set
        if not os.getenv("DASHSCOPE_API_KEY"):
            print("Warning: DASHSCOPE_API_KEY environment variable is not set")
            print("Please set it before running the server:")
            print("export DASHSCOPE_API_KEY=your_api_key")
        
        # Run async main
        asyncio.run(async_main())
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()