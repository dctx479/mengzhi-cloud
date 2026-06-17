"""
平台发布器注册表

负责根据 platform 字符串找到对应的 PublisherBase 子类实例。
支持环境变量驱动的 Mock/Real 模式切换。

版本: 1.0
创建日期: 2026-06-17
"""

from typing import Dict, Type, Optional
import logging
import os

from .base import PublisherBase
from .adapters import (
    DouyinPublisher,
    XiaohongshuPublisher,
    WechatPublisher,
    WeiboPublisher,
)

logger = logging.getLogger(__name__)


class PublisherRegistry:
    """发布器注册表 (单例)

    根据 platform key 返回对应平台的 PublisherBase 实例。
    支持 Mock/Real 模式切换 (环境变量 PUBLISHER_MODE)。
    """

    _instance: Optional["PublisherRegistry"] = None
    _adapters: Dict[str, Type[PublisherBase]] = {
        "douyin": DouyinPublisher,
        "xiaohongshu": XiaohongshuPublisher,
        "wechat": WechatPublisher,
        "weibo": WeiboPublisher,
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, platform: str) -> Optional[PublisherBase]:
        """获取指定平台的发布器实例

        Args:
            platform: 平台 key (douyin/xiaohongshu/wechat/weibo)

        Returns:
            PublisherBase 实例, 不支持时返回 None
        """
        adapter_cls = self._adapters.get(platform)
        if not adapter_cls:
            logger.warning(f"⚠️ WARNING: Unsupported platform: {platform}")
            return None

        mode = os.getenv("PUBLISHER_MODE", "mock").lower()
        config = {
            "mode": mode,
            "platform": platform,
        }

        # 真实模式: 从环境变量读取凭证 (当前未使用, 仅占位)
        if mode == "real":
            config["app_key"] = os.getenv(f"PUBLISHER_{platform.upper()}_APP_KEY", "")
            config["app_secret"] = os.getenv(f"PUBLISHER_{platform.upper()}_APP_SECRET", "")
            config["access_token"] = os.getenv(f"PUBLISHER_{platform.upper()}_ACCESS_TOKEN", "")

        return adapter_cls(config)

    def list_platforms(self) -> list:
        """列出所有支持的平台"""
        return list(self._adapters.keys())

    def is_supported(self, platform: str) -> bool:
        """检查平台是否支持"""
        return platform in self._adapters
