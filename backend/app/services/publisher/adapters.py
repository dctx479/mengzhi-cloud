"""
4 大平台适配器实现 (Mock 模式)

- DouyinPublisher: 抖音
- XiaohongshuPublisher: 小红书
- WechatPublisher: 微信公众号
- WeiboPublisher: 微博

每个适配器:
1. adapt() 执行平台特定的内容预处理 (字数截断/标签规范化)
2. publish() 模拟 50-300ms 延迟 + 5% 概率失败 + 返回 mock URL

Mock 模式特征: 所有 URL 以 `mock.{platform}.com` 开头,
                platform_post_id 以 `mock_` 前缀, 便于识别.

真实模式 (PUBLISHER_MODE=real) 占位, 仅 logger.warning "would call API".

版本: 1.0
创建日期: 2026-06-17
"""

import asyncio
import logging
import random
import uuid
from typing import Optional

from .base import PublisherBase, PublishRequest, PublishResult

logger = logging.getLogger(__name__)


# 平台特定字数/标签限制
ADAPTER_RULES = {
    "douyin": {
        "title_max": 30,
        "content_max": 1500,
        "require_media": True,
        "media_min": 1,
        "tag_prefix": "#",
    },
    "xiaohongshu": {
        "title_max": 20,
        "content_max": 1000,
        "require_media": True,
        "media_min": 1,
        "tag_prefix": "#",
    },
    "wechat": {
        "title_max": 64,
        "content_max": 20000,
        "require_media": False,
        "media_min": 0,
        "tag_prefix": "",
    },
    "weibo": {
        "title_max": 30,
        "content_max": 2000,
        "require_media": False,
        "media_min": 0,
        "tag_prefix": "#",
    },
}


def _truncate(text: str, max_len: int) -> str:
    """安全截断文本 (中文按字符算)"""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


class DouyinPublisher(PublisherBase):
    """抖音发布器 (Mock)"""

    platform = "douyin"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.rules = ADAPTER_RULES["douyin"]

    def adapt(self, request: PublishRequest) -> PublishRequest:
        adapted_title = _truncate(request.title or "", self.rules["title_max"])
        adapted_content = _truncate(request.content, self.rules["content_max"])
        adapted_tags = self.format_tags(request.tags, self.rules["tag_prefix"])
        return PublishRequest(
            content=adapted_content,
            title=adapted_title or None,
            images=list(request.images),
            tags=adapted_tags,
            extra=request.extra,
        )

    def validate(self, request: PublishRequest) -> Optional[str]:
        err = super().validate(request)
        if err:
            return err
        # 抖音要求至少 1 个媒体 (视频/图片)
        if self.rules["require_media"] and len(request.images) < self.rules["media_min"]:
            return "抖音发布需要至少 1 个媒体 (图片/视频)"
        return None

    async def publish(self, request: PublishRequest) -> PublishResult:
        if self.config.get("mode") == "real":
            logger.warning(
                f"⚠️ WARNING: real Douyin API not implemented, "
                f"would call /share/item/create with title={request.title}"
            )
        # 模拟 50-300ms 延迟
        await asyncio.sleep(random.uniform(0.05, 0.3))
        # 5% 概率失败
        if random.random() < 0.05:
            return PublishResult(
                success=False,
                platform=self.platform,
                error_message="抖音平台限流 (mock failure)",
            )
        post_id = f"mock_dy_{uuid.uuid4().hex[:16]}"
        return PublishResult(
            success=True,
            platform=self.platform,
            platform_post_id=post_id,
            platform_url=f"https://mock.douyin.com/video/{post_id}",
            raw_response={"mock": True, "platform": "douyin"},
        )


class XiaohongshuPublisher(PublisherBase):
    """小红书发布器 (Mock)"""

    platform = "xiaohongshu"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.rules = ADAPTER_RULES["xiaohongshu"]

    def adapt(self, request: PublishRequest) -> PublishRequest:
        adapted_title = _truncate(request.title or "", self.rules["title_max"])
        adapted_content = _truncate(request.content, self.rules["content_max"])
        adapted_tags = self.format_tags(request.tags, self.rules["tag_prefix"])
        return PublishRequest(
            content=adapted_content,
            title=adapted_title or None,
            images=list(request.images),
            tags=adapted_tags,
            extra=request.extra,
        )

    def validate(self, request: PublishRequest) -> Optional[str]:
        err = super().validate(request)
        if err:
            return err
        if self.rules["require_media"] and len(request.images) < self.rules["media_min"]:
            return "小红书发布需要至少 1 张图片"
        return None

    async def publish(self, request: PublishRequest) -> PublishResult:
        if self.config.get("mode") == "real":
            logger.warning(
                f"⚠️ WARNING: real Xiaohongshu API not implemented, "
                f"would call /api/sns/v1/note/post with title={request.title}"
            )
        await asyncio.sleep(random.uniform(0.05, 0.3))
        if random.random() < 0.05:
            return PublishResult(
                success=False,
                platform=self.platform,
                error_message="小红书平台内容审核未通过 (mock failure)",
            )
        post_id = f"mock_xhs_{uuid.uuid4().hex[:16]}"
        return PublishResult(
            success=True,
            platform=self.platform,
            platform_post_id=post_id,
            platform_url=f"https://mock.xiaohongshu.com/discovery/item/{post_id}",
            raw_response={"mock": True, "platform": "xiaohongshu"},
        )


class WechatPublisher(PublisherBase):
    """微信公众号发布器 (Mock)"""

    platform = "wechat"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.rules = ADAPTER_RULES["wechat"]

    def adapt(self, request: PublishRequest) -> PublishRequest:
        adapted_title = _truncate(request.title or "", self.rules["title_max"])
        adapted_content = _truncate(request.content, self.rules["content_max"])
        # 微信无标签, 仅保留作为隐藏分类
        adapted_tags = self.format_tags(request.tags, self.rules["tag_prefix"])
        return PublishRequest(
            content=adapted_content,
            title=adapted_title or None,
            images=list(request.images),
            tags=adapted_tags,
            extra=request.extra,
        )

    async def publish(self, request: PublishRequest) -> PublishResult:
        if self.config.get("mode") == "real":
            logger.warning(
                f"⚠️ WARNING: real WeChat API not implemented, "
                f"would call /cgi-bin/message/mass/sendall with title={request.title}"
            )
        # 微信草稿箱 → 群发流程较长, 模拟更长时间
        await asyncio.sleep(random.uniform(0.1, 0.5))
        if random.random() < 0.05:
            return PublishResult(
                success=False,
                platform=self.platform,
                error_message="微信素材上传失败 (mock failure)",
            )
        post_id = f"mock_wx_{uuid.uuid4().hex[:16]}"
        return PublishResult(
            success=True,
            platform=self.platform,
            platform_post_id=post_id,
            platform_url=f"https://mock.weixin.qq.com/s/{post_id}",
            raw_response={"mock": True, "platform": "wechat"},
        )


class WeiboPublisher(PublisherBase):
    """微博发布器 (Mock)"""

    platform = "weibo"

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.rules = ADAPTER_RULES["weibo"]

    def adapt(self, request: PublishRequest) -> PublishRequest:
        adapted_title = _truncate(request.title or "", self.rules["title_max"])
        adapted_content = _truncate(request.content, self.rules["content_max"])
        adapted_tags = self.format_tags(request.tags, self.rules["tag_prefix"])
        return PublishRequest(
            content=adapted_content,
            title=adapted_title or None,
            images=list(request.images),
            tags=adapted_tags,
            extra=request.extra,
        )

    async def publish(self, request: PublishRequest) -> PublishResult:
        if self.config.get("mode") == "real":
            logger.warning(
                f"⚠️ WARNING: real Weibo API not implemented, "
                f"would call /2/statuses/share with text length={len(request.content)}"
            )
        await asyncio.sleep(random.uniform(0.05, 0.3))
        if random.random() < 0.05:
            return PublishResult(
                success=False,
                platform=self.platform,
                error_message="微博平台敏感词拦截 (mock failure)",
            )
        post_id = f"mock_wb_{uuid.uuid4().hex[:16]}"
        return PublishResult(
            success=True,
            platform=self.platform,
            platform_post_id=post_id,
            platform_url=f"https://mock.weibo.com/{post_id}",
            raw_response={"mock": True, "platform": "weibo"},
        )
