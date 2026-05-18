"""
AI Provider 抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """统一消息格式"""
    role: str  # system, user, assistant
    content: str


@dataclass
class ChatCompletionRequest:
    """统一请求参数"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


@dataclass
class Usage:
    """Token使用统计"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatCompletionResponse:
    """统一响应格式"""
    id: str
    content: str
    model: str
    usage: Usage
    finish_reason: str  # stop, length, error


class BaseAIProvider(ABC):
    """AI Provider 抽象基类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider名称"""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """支持的模型列表"""
        pass

    @abstractmethod
    async def chat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """非流式对话"""
        pass

    @abstractmethod
    async def chat_stream(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        """流式对话"""
        pass

    async def validate_config(self) -> bool:
        """验证配置是否有效"""
        import logging
        _log = logging.getLogger(__name__)
        try:
            test_request = ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="test")],
                max_tokens=1
            )
            await self.chat(test_request)
            return True
        except Exception as exc:
            _log.warning("Provider %s config validation failed: %s", self.name, exc)
            return False
