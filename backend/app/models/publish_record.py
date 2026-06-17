"""
内容发布记录数据模型

包含:
- PublishRecord: 单平台发布记录
- PublishMetric: 表现数据 (PV/UV/点赞/转化)
- PublishStatus: 发布状态枚举
- 平台特定 URL/错误追踪

版本: 1.0
创建日期: 2026-06-17
"""

from sqlalchemy import (
    Column,
    BIGINT,
    VARCHAR,
    Enum,
    TIMESTAMP,
    Index,
    JSON,
    TEXT,
    Integer,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
import enum

from .base import BaseModel, generate_uuid
from .content_record import Platform


class PublishStatus(enum.Enum):
    """发布状态枚举"""

    PENDING = "pending"        # 排队中
    PUBLISHING = "publishing"  # 发布中
    PUBLISHED = "published"    # 已发布
    FAILED = "failed"          # 失败
    DELETED = "deleted"        # 已下架


class PublishRecord(BaseModel):
    """内容发布记录模型

    追踪一条 content_record 在某个平台上的发布尝试/结果。
    同一 content_record 可发布到多个平台，每平台一条记录。
    """

    __tablename__ = "publish_records"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="记录ID")

    publish_uuid = Column(
        VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="发布UUID"
    )

    # 关联
    content_record_id = Column(
        BIGINT,
        ForeignKey("content_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="内容记录ID",
    )
    user_id = Column(
        BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID"
    )
    product_id = Column(
        BIGINT, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True, comment="产品ID"
    )

    # 平台
    platform = Column(Enum(Platform), nullable=False, index=True, comment="目标平台")

    # 适配后内容
    adapted_title = Column(VARCHAR(200), nullable=True, comment="适配后标题")
    adapted_content = Column(TEXT, nullable=True, comment="适配后正文")
    adapted_tags = Column(JSON, nullable=True, comment="适配后标签列表")
    media_urls = Column(JSON, nullable=True, comment="媒体URL列表")

    # 发布结果
    status = Column(
        Enum(PublishStatus),
        nullable=False,
        default=PublishStatus.PENDING,
        index=True,
        comment="发布状态",
    )
    platform_post_id = Column(VARCHAR(128), nullable=True, comment="平台返回的帖子ID")
    platform_url = Column(VARCHAR(500), nullable=True, comment="平台帖子URL")
    error_message = Column(TEXT, nullable=True, comment="错误信息")
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")

    # 时间
    published_at = Column(TIMESTAMP, nullable=True, comment="发布时间")
    is_mock = Column(Integer, nullable=False, default=1, comment="是否 Mock 发布 (0=real, 1=mock)")

    # 关系
    content_record = relationship("ContentRecord", foreign_keys=[content_record_id])
    metrics = relationship(
        "PublishMetric", back_populates="publish_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_publish_user_status", "user_id", "status"),
        Index("idx_publish_platform_status", "platform", "status"),
        Index("idx_publish_content", "content_record_id"),
        Index("idx_publish_published_at", "published_at"),
    )

    def __repr__(self) -> str:
        return f"<PublishRecord(id={self.id}, platform={self.platform.value if self.platform else None}, status={self.status.value if self.status else None})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "publish_uuid": self.publish_uuid,
            "content_record_id": self.content_record_id,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "platform": self.platform.value if self.platform else None,
            "adapted_title": self.adapted_title,
            "adapted_content": self.adapted_content,
            "adapted_tags": self.adapted_tags,
            "media_urls": self.media_urls,
            "status": self.status.value if self.status else None,
            "platform_post_id": self.platform_post_id,
            "platform_url": self.platform_url,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "is_mock": bool(self.is_mock),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_terminal(self) -> bool:
        """是否终态（已发布/失败/已删除）"""
        return self.status in (PublishStatus.PUBLISHED, PublishStatus.FAILED, PublishStatus.DELETED)


class PublishMetric(BaseModel):
    """发布表现数据 (按日聚合)

    同一 publish_record + 同一 metric_date 唯一（一日一行）。
    支持 PV/UV/点赞/分享/评论/收藏/转化。
    """

    __tablename__ = "publish_metrics"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="指标ID")

    publish_record_id = Column(
        BIGINT,
        ForeignKey("publish_records.id", ondelete="CASCADE"),
        nullable=False,
        comment="发布记录ID",
    )

    metric_date = Column(String(10), nullable=False, index=True, comment="数据日期 YYYY-MM-DD")

    # 基础指标
    pv = Column(Integer, nullable=False, default=0, comment="浏览量")
    uv = Column(Integer, nullable=False, default=0, comment="独立访客")
    like_count = Column(Integer, nullable=False, default=0, comment="点赞数")
    share_count = Column(Integer, nullable=False, default=0, comment="分享数")
    comment_count = Column(Integer, nullable=False, default=0, comment="评论数")
    favorite_count = Column(Integer, nullable=False, default=0, comment="收藏数")
    conversion_count = Column(Integer, nullable=False, default=0, comment="转化数")

    # 平台原始数据
    raw_data = Column(JSON, nullable=True, comment="平台原始指标JSON")

    # 关系
    publish_record = relationship("PublishRecord", back_populates="metrics", foreign_keys=[publish_record_id])

    __table_args__ = (
        UniqueConstraint("publish_record_id", "metric_date", name="uk_publish_metric_date"),
        Index("idx_metric_publish_date", "publish_record_id", "metric_date"),
    )

    def __repr__(self) -> str:
        return f"<PublishMetric(id={self.id}, publish_record_id={self.publish_record_id}, date={self.metric_date})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "publish_record_id": self.publish_record_id,
            "metric_date": self.metric_date,
            "pv": self.pv,
            "uv": self.uv,
            "like_count": self.like_count,
            "share_count": self.share_count,
            "comment_count": self.comment_count,
            "favorite_count": self.favorite_count,
            "conversion_count": self.conversion_count,
            "raw_data": self.raw_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
