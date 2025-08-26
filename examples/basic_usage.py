#!/usr/bin/env python3
"""
Aigroup Video MCP 基础使用示例

这个脚本演示了如何使用 Aigroup Video MCP 进行视频分析。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from aigroup_video_mcp.core.analyzer import get_analyzer, create_video_source
from aigroup_video_mcp.settings import get_settings


async def basic_video_analysis():
    """基础视频分析示例"""
    print("=== 基础视频分析示例 ===")
    
    try:
        # 检查 API Key
        if not os.getenv("DASHSCOPE_API_KEY"):
            print("错误：请设置 DASHSCOPE_API_KEY 环境变量")
            return
        
        # 创建分析器
        analyzer = get_analyzer(async_mode=True)
        
        # 示例视频路径（请替换为实际的视频文件）
        video_path = "path/to/your/video.mp4"
        
        # 检查视频文件是否存在
        if not Path(video_path).exists():
            print(f"注意：示例视频文件不存在: {video_path}")
            print("请将 video_path 变量替换为实际的视频文件路径")
            return
        
        # 创建视频源
        video_source = create_video_source(video_path)
        
        # 分析视频
        print(f"正在分析视频: {video_path}")
        result = await analyzer.analyze(
            video_source, 
            "请详细描述这个视频的内容，包括主要场景、人物和事件。"
        )
        
        if result.success:
            print("分析成功！")
            print("-" * 50)
            print(result.content)
            print("-" * 50)
            print(f"分析耗时: {result.duration:.2f} 秒")
        else:
            print(f"分析失败: {result.error}")
            
    except Exception as e:
        print(f"发生错误: {e}")


async def video_summarization():
    """视频摘要示例"""
    print("\n=== 视频摘要示例 ===")
    
    try:
        analyzer = get_analyzer(async_mode=True)
        video_path = "path/to/your/video.mp4"
        
        if not Path(video_path).exists():
            print(f"注意：示例视频文件不存在: {video_path}")
            return
        
        video_source = create_video_source(video_path)
        
        # 生成不同类型的摘要
        summary_types = ["brief", "general", "detailed"]
        
        for summary_type in summary_types:
            print(f"\n--- {summary_type.upper()} 摘要 ---")
            result = await analyzer.summarize(video_source, summary_type)
            
            if result.success:
                print(result.content)
            else:
                print(f"摘要生成失败: {result.error}")
                
    except Exception as e:
        print(f"发生错误: {e}")


async def scene_analysis():
    """场景分析示例"""
    print("\n=== 场景分析示例 ===")
    
    try:
        analyzer = get_analyzer(async_mode=True)
        video_path = "path/to/your/video.mp4"
        
        if not Path(video_path).exists():
            print(f"注意：示例视频文件不存在: {video_path}")
            return
        
        video_source = create_video_source(video_path)
        
        # 场景分析
        result = await analyzer.analyze_scenes(
            video_source, 
            scene_detection=True
        )
        
        if result.success:
            print("场景分析结果：")
            print("-" * 50)
            print(result.content)
        else:
            print(f"场景分析失败: {result.error}")
            
    except Exception as e:
        print(f"发生错误: {e}")


async def custom_analysis():
    """自定义分析示例"""
    print("\n=== 自定义分析示例 ===")
    
    try:
        analyzer = get_analyzer(async_mode=True)
        video_path = "path/to/your/video.mp4"
        
        if not Path(video_path).exists():
            print(f"注意：示例视频文件不存在: {video_path}")
            return
        
        video_source = create_video_source(video_path)
        
        # 自定义分析提示词
        custom_prompts = [
            "这个视频中有多少个人？他们在做什么？",
            "请识别视频中出现的所有文字和标志。",
            "分析视频的情感色调和氛围。",
            "描述视频的拍摄技巧和视觉风格。"
        ]
        
        for i, prompt in enumerate(custom_prompts, 1):
            print(f"\n--- 自定义分析 {i} ---")
            print(f"提示词: {prompt}")
            
            result = await analyzer.analyze_custom(video_source, prompt)
            
            if result.success:
                print("分析结果:")
                print(result.content)
            else:
                print(f"分析失败: {result.error}")
                
    except Exception as e:
        print(f"发生错误: {e}")


def check_configuration():
    """检查配置"""
    print("=== 配置检查 ===")
    
    try:
        settings = get_settings()
        
        print(f"环境: {settings.environment}")
        print(f"调试模式: {settings.debug}")
        print(f"DashScope API Key: {'已配置' if settings.dashscope.api_key else '未配置'}")
        print(f"支持的视频格式: {', '.join(settings.video.supported_formats)}")
        print(f"最大文件大小: {settings.video.max_file_size // (1024*1024)}MB")
        print(f"最大视频时长: {settings.video.max_duration}秒")
        
    except Exception as e:
        print(f"配置检查失败: {e}")


async def main():
    """主函数"""
    print("Aigroup Video MCP 使用示例")
    print("=" * 50)
    
    # 配置检查
    check_configuration()
    
    # 检查是否有 API Key
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n请设置 DASHSCOPE_API_KEY 环境变量后再运行示例。")
        print("例如: export DASHSCOPE_API_KEY=your_api_key_here")
        return
    
    print("\n注意：请将示例中的视频路径替换为实际的视频文件路径")
    print("支持的格式: MP4, AVI, MOV, MKV, WebM, FLV")
    
    # 运行各种示例
    await basic_video_analysis()
    await video_summarization()
    await scene_analysis()
    await custom_analysis()
    
    print("\n=== 示例运行完成 ===")


if __name__ == "__main__":
    # 设置事件循环策略（Windows 兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行示例
    asyncio.run(main())