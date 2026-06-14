"""
多媒体生成 Provider 抽象基类

与 BaseAIProvider (LLM chat/embedding) 平行的一套抽象, 用于统一管理
图像/视频/音频生成类 Provider (如即梦AI)。两套体系不混用:
 - BaseAIProvider: chat / chat_stream / embedding 语义
 - MultimediaProvider: generate_image / generate_video / generate_audio 语义

能力声明式设计: Provider 通过 `capabilities` 声明支持哪些媒体类型,
调用未声明的能力会抛 UnsupportedCapabilityError (而非 AttributeError)。
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class MediaCapability(str, Enum):
    """多媒体生成能力类型"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class UnsupportedCapabilityError(NotImplementedError):
    """Provider 不支持所请求的媒体生成能力"""


class MultimediaProvider(ABC):
    """多媒体 (图像/视频/音频) 生成 Provider 抽象基类"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider 名称"""
        raise NotImplementedError

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """支持的模型列表"""
        raise NotImplementedError

    @property
    @abstractmethod
    def capabilities(self) -> Set[MediaCapability]:
        """该 Provider 支持的媒体能力集合"""
        raise NotImplementedError

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """连通性测试"""
        raise NotImplementedError

    async def generate_image(self, prompt: str, **opts) -> Dict[str, Any]:
        """文生图。不支持时抛 UnsupportedCapabilityError。"""
        raise UnsupportedCapabilityError(f"{self.name} does not support image generation")

    async def generate_video(self, prompt: str, **opts) -> Dict[str, Any]:
        """视频生成。不支持时抛 UnsupportedCapabilityError。"""
        raise UnsupportedCapabilityError(f"{self.name} does not support video generation")

    async def generate_audio(self, text: str, **opts) -> Dict[str, Any]:
        """音频生成 (TTS)。不支持时抛 UnsupportedCapabilityError。"""
        raise UnsupportedCapabilityError(f"{self.name} does not support audio generation")

    def supports(self, capability: MediaCapability) -> bool:
        """是否支持指定媒体能力"""
        return capability in self.capabilities
