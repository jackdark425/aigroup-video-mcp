"""视频分析器
封装 DashScope API 调用功能，提供视频内容分析、摘要、场景识别等功能。
"""

import os
import dashscope
from typing import Dict, List, Optional, Any
from loguru import logger
from urllib.parse import urlparse
import argparse
from dataclasses import dataclass


@dataclass
class Settings:
    dashscope_api_key: str
    dashscope_model: str = "qwen-vl-max-latest"
    dashscope_max_tokens: int = 1500
    dashscope_temperature: float = 0.1
    video_default_fps: float = 1.0

    @property
    def dashscope(self):
        return self


def get_settings() -> Settings:
    """从环境变量获取设置"""
    api_key = os.environ.get('DASHSCOPE_API_KEY')
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 环境变量未设置")

    model = os.environ.get('DASHSCOPE_MODEL', 'qwen-vl-max-latest')
    max_tokens = int(os.environ.get('DASHSCOPE_MAX_TOKENS', '1500'))
    temperature = float(os.environ.get('DASHSCOPE_TEMPERATURE', '0.1'))
    fps = float(os.environ.get('VIDEO_DEFAULT_FPS', '1.0'))

    return Settings(
        dashscope_api_key=api_key,
        dashscope_model=model,
        dashscope_max_tokens=max_tokens,
        dashscope_temperature=temperature,
        video_default_fps=fps
    )


class VideoAnalyzer:
    """视频分析器类"""

    def __init__(self):
        """初始化视频分析器"""
        self.settings = get_settings()
        self._setup_dashscope()

    def _setup_dashscope(self):
        """配置 DashScope 客户端"""
        try:
            api_key = self.settings.dashscope_api_key
            if not api_key:
                raise ValueError("DashScope API Key 未配置")

            # 设置 DashScope API Key
            dashscope.api_key = api_key
            os.environ['DASHSCOPE_API_KEY'] = api_key
            logger.info("DashScope 客户端配置成功")

        except Exception as e:
            logger.error(f"DashScope 客户端配置失败: {e}")
            raise

    def _validate_video_url(self, video_url: str) -> bool:
        """验证视频路径/URL格式 - 支持本地路径和互联网URL"""
        try:
            if not video_url or not isinstance(video_url, str):
                logger.debug("视频路径为空或类型无效")
                return False

            # 检查是否为有效的HTTP/HTTPS URL
            parsed = urlparse(video_url)
            if parsed.scheme in ['http', 'https']:
                if parsed.netloc:
                    logger.debug(f"识别为互联网URL: {video_url}")
                    return True
                else:
                    logger.debug(f"无效的URL格式: {video_url}")
                    return False

            # 检查本地文件路径
            # 1. 直接检查绝对路径是否存在
            if os.path.isabs(video_url):
                if os.path.exists(video_url):
                    logger.debug(f"识别为本地绝对路径: {video_url}")
                    return True
                else:
                    logger.debug(f"本地绝对路径不存在: {video_url}")
                    return False

            # 2. 检查相对路径
            relative_path = os.path.join(os.getcwd(), video_url)
            if os.path.exists(relative_path):
                logger.debug(f"识别为本地相对路径: {video_url}")
                return True
            else:
                logger.debug(f"本地相对路径不存在: {video_url}")
                return False

        except Exception as e:
            logger.debug(f"视频路径验证异常: {e}")
            return False

    def _create_base_message(self, video_url: str, text_prompt: str, fps: float = None) -> List[Dict]:
        """创建基础消息结构"""
        if not self._validate_video_url(video_url):
            raise ValueError(f"无效的视频URL: {video_url}")

        fps_value = fps or self.settings.video_default_fps

        messages = [
            {
                "role": "system",
                "content": [{"text": "You are a helpful video analysis assistant."}]
            },
            {
                "role": "user",
                "content": [
                    {
                        "video": video_url,
                        "fps": fps_value
                    },
                    {
                        "text": text_prompt
                    }
                ]
            }
        ]

        return messages

    def analyze_video_basic(self, video_url: str, question: str, fps: float = None) -> str:
        """基础视频分析 - 基于原始 1.py 的逻辑

        Args:
            video_url: 视频文件路径或URL（支持本地路径和互联网URL）
            question: 分析问题
            fps: 抽帧频率，默认使用配置值

        Returns:
            分析结果文本
        """
        try:
            logger.info(f"开始分析视频: {video_url}")
            logger.debug(f"问题: {question}")

            messages = self._create_base_message(video_url, question, fps)

            response = dashscope.MultiModalConversation.call(
                model=self.settings.dashscope_model,
                messages=messages,
                max_tokens=self.settings.dashscope_max_tokens,
                temperature=self.settings.dashscope_temperature
            )

            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code} - {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.output.choices[0].message.content[0]["text"]
            logger.info("视频分析完成")
            return result

        except Exception as e:
            logger.error(f"视频分析失败: {e}")
            raise

    def analyze_video_with_prompt(self, video_url: str, prompt_template: str, **kwargs) -> str:
        """使用提示词模板分析视频

        Args:
            video_url: 视频文件路径或URL（支持本地路径和互联网URL）
            prompt_template: 提示词模板
            **kwargs: 模板参数

        Returns:
            分析结果文本
        """
        try:
            # 格式化提示词
            question = prompt_template.format(**kwargs) if kwargs else prompt_template

            logger.info(f"使用提示词模板分析视频: {prompt_template[:50]}...")
            return self.analyze_video_basic(video_url, question)

        except Exception as e:
            logger.error(f"提示词分析失败: {e}")
            raise

    def analyze_video_summary(self, video_url: str) -> str:
        """视频摘要分析

        Args:
            video_url: 视频文件路径或URL（支持本地路径和互联网URL）

        Returns:
            视频摘要分析结果
        """
        prompt = "请提供这个视频的详细摘要，包括主要内容、场景、人物和关键事件。"
        return self.analyze_video_with_prompt(video_url, prompt)

    def analyze_video_scenes(self, video_url: str) -> str:
        """视频场景分析

        Args:
            video_url: 视频文件路径或URL（支持本地路径和互联网URL）

        Returns:
            视频场景分析结果
        """
        prompt = "请分析这个视频中的主要场景和场景转换，并描述每个场景的内容。"
        return self.analyze_video_with_prompt(video_url, prompt)

    def analyze_video_content(self, video_url: str, custom_question: str) -> str:
        """自定义问题分析视频

        Args:
            video_url: 视频文件路径或URL（支持本地路径和互联网URL）
            custom_question: 自定义分析问题

        Returns:
            自定义问题分析结果
        """
        return self.analyze_video_basic(video_url, custom_question)


def main():
    parser = argparse.ArgumentParser(description='视频分析工具 - 支持本地路径和互联网URL')
    parser.add_argument('--video_path', default=os.environ.get('VIDEO_PATH'), help='视频文件路径或URL（支持本地路径和互联网URL，如 https://example.com/video.mp4）')
    parser.add_argument('--question', default=os.environ.get('VIDEO_QUESTION', '请描述这个视频的主要内容'), help='分析问题')

    args = parser.parse_args()

    if not args.video_path:
        parser.error("视频路径未指定，请设置 --video_path 参数或 VIDEO_PATH 环境变量")

    # 创建分析器实例（API Key 从环境变量读取）
    analyzer = VideoAnalyzer()

    # 执行分析
    try:
        result = analyzer.analyze_video_basic(args.video_path, args.question)
        print("分析结果:")
        print(result)
    except Exception as e:
        print(f"分析失败: {e}")


if __name__ == '__main__':
    main()