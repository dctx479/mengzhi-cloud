"""
AI服务初始化文件

版本: 2.0 - 多Provider支持
更新日期: 2026-01-22
"""

from .deepseek_client import DeepSeekClient, get_deepseek_client
from .prompt_templates import PromptTemplates
from .base_provider import (
    BaseAIProvider,
    ChatMessage,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Usage,
)
from .factory import AIProviderFactory
from .providers.deepseek_provider import DeepSeekProvider
from .providers.openai_provider import OpenAIProvider

__all__ = [
    # 旧版兼容
    "DeepSeekClient",
    "get_deepseek_client",
    "PromptTemplates",
    # 新版多Provider
    "BaseAIProvider",
    "ChatMessage",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "Usage",
    "AIProviderFactory",
    "DeepSeekProvider",
    "OpenAIProvider",
]
