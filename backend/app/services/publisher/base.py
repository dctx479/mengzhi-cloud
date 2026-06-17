"""
平台发布器抽象基类

定义多平台分发的统一接口和共享数据结构:
- PublishRequest: 发布请求 (内容/标题/媒体/标签)
- PublishResult: 发布结果 (成功/平台URL/错误)
- PublisherBase: 抽象类, 子类实现 adapt() + publish()

版本: 1.0
创建日期: 2026-06-17
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class PublishRequest:
    """发布请求

    包含一个内容帖子所需的所有字段, 由适配器根据平台规则裁剪/格式化。
    """

    content: str
    title: Optional[str] = None
    images: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishResult:
    """发布结果"""

    success: bool
    platform: str
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class PublisherBase(ABC):
    """平台发布器抽象基类

    子类需要定义:
    - `platform` 类属性: 平台标识 (与 models.Platform 枚举值一致)
    - `adapt()`: 平台特定的内容适配 (字数/标签/格式)
    - `publish()`: 实际执行发布 (Mock 返回假数据, Real 调 HTTP)
    """

    platform: str = ""  # 子类必须定义

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def validate(self, request: PublishRequest) -> Optional[str]:
        """参数校验, 失败返回错误信息, 成功返回 None

        默认实现检查: 标题/内容长度, 至少 1 张图或纯文本
        """
        if not request.content and not request.title:
            return "内容和标题不能同时为空"
        if request.content and len(request.content) > 50000:
            return f"内容长度 {len(request.content)} 超过最大限制 50000 字符"
        return None

    @abstractmethod
    def adapt(self, request: PublishRequest) -> PublishRequest:
        """平台特定的内容适配 (字数/标签/格式)

        返回适配后的 PublishRequest, 由 publish() 使用。
        """
        ...

    @abstractmethod
    async def publish(self, request: PublishRequest) -> PublishResult:
        """执行发布 (Mock 或 Real)

        Real 模式: 调真实开放 API
        Mock 模式: 模拟延迟 + 返回假 URL
        """
        ...

    def format_tags(self, tags: List[str], prefix: str = "#") -> List[str]:
        """统一的标签格式化辅助方法

        - 去重
        - 去除空白
        - 添加 # 前缀 (如未带)
        - 限制最大 30 字符
        """
        seen = set()
        result = []
        for tag in tags:
            if not tag:
                continue
            tag = str(tag).strip()
            if not tag:
                continue
            if not tag.startswith(prefix):
                tag = f"{prefix}{tag}"
            tag = tag[:30]
            if tag in seen:
                continue
            seen.add(tag)
            result.append(tag)
        return result
