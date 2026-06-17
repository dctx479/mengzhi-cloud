"""
多平台内容分发 - 抽象层包

导出:
- PublisherBase / PublishRequest / PublishResult
- PublisherRegistry
- 4 个平台适配器 (Douyin/Xiaohongshu/Wechat/Weibo)
- ContentPublisherService (统一入口)

版本: 1.0
创建日期: 2026-06-17
"""

from .base import PublisherBase, PublishRequest, PublishResult
from .registry import PublisherRegistry
from .adapters import (
    DouyinPublisher,
    XiaohongshuPublisher,
    WechatPublisher,
    WeiboPublisher,
)
from .publisher_service import ContentPublisherService

__all__ = [
    "PublisherBase",
    "PublishRequest",
    "PublishResult",
    "PublisherRegistry",
    "DouyinPublisher",
    "XiaohongshuPublisher",
    "WechatPublisher",
    "WeiboPublisher",
    "ContentPublisherService",
]
