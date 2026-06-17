"""
效果监测数据模型

包含:
- EffectEvent: 单次事件记录 (内容发布/对话/购买)
- EffectMetric: 聚合指标 (按维度 group by)
- EffectType: 效果类型枚举

设计:
- EffectEvent 记录原始事件 (who/what/when/where)
- EffectMetric 提供 Dashboard 聚合查询 (按 content_id / platform / time)
- 与 publish_records 解耦, 可独立追踪任意效果数据

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
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any
import enum

from .base import BaseModel, generate_uuid


class EffectType(enum.Enum):
    """效果类型"""

    CONTENT_PUBLISH = "content_publish"  # 内容发布
    CONTENT_VIEW = "content_view"        # 内容查看
    CHAT_MESSAGE = "chat_message"        # 对话消息
    GENERATION_CALL = "generation_call"  # 内容生成调用
    PRODUCT_CLICK = "product_click"      # 产品点击
    CONVERSION = "conversion"            # 转化（购买/留资）
    AI_RESPONSE = "ai_response"          # AI 响应


class EffectEvent(BaseModel):
    """单次效果事件记录

    每条事件包含: 事件类型 + 用户 + 产品 + 平台 + 时间 + 元数据
    用于: 实时事件流, 后续 ETL 入仓
    """

    __tablename__ = "effect_events"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="事件ID")

    event_uuid = Column(
        VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="事件UUID"
    )

    # 事件类型
    event_type = Column(Enum(EffectType), nullable=False, index=True, comment="事件类型")

    # 上下文
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="用户ID")
    product_id = Column(BIGINT, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True, comment="产品ID")
    content_record_id = Column(
        BIGINT, ForeignKey("content_records.id", ondelete="SET NULL"), nullable=True, index=True, comment="内容记录ID"
    )
    publish_record_id = Column(
        BIGINT, ForeignKey("publish_records.id", ondelete="SET NULL"), nullable=True, index=True, comment="发布记录ID"
    )

    # 平台维度
    platform = Column(String(32), nullable=True, index=True, comment="平台 (douyin/xiaohongshu/wechat/weibo/...)")
    channel = Column(String(64), nullable=True, comment="渠道 (web/app/miniprogram/...)")

    # 时间
    event_time = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, index=True, comment="事件时间")

    # 元数据 (JSON: 设备/位置/停留时长/转化金额等)
    extra_data = Column(JSON, nullable=True, comment="额外数据")

    __table_args__ = (
        Index("idx_event_type_time", "event_type", "event_time"),
        Index("idx_event_user_time", "user_id", "event_time"),
        Index("idx_event_product_time", "product_id", "event_time"),
        Index("idx_event_platform_time", "platform", "event_time"),
    )

    def __repr__(self) -> str:
        return f"<EffectEvent(id={self.id}, type={self.event_type.value if self.event_type else None})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_uuid": self.event_uuid,
            "event_type": self.event_type.value if self.event_type else None,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "content_record_id": self.content_record_id,
            "publish_record_id": self.publish_record_id,
            "platform": self.platform,
            "channel": self.channel,
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EffectMetricSnapshot(BaseModel):
    """效果指标快照 (按日聚合)

    用于快速查询 Dashboard, 避免每次都 GROUP BY 大量事件。
    每个 (date + dimension_key) 唯一一行。
    """

    __tablename__ = "effect_metric_snapshots"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="快照ID")

    metric_date = Column(String(10), nullable=False, index=True, comment="数据日期 YYYY-MM-DD")
    dimension_type = Column(
        String(32), nullable=False, index=True, comment="维度类型 (platform/product/total)"
    )
    dimension_key = Column(String(128), nullable=False, index=True, comment="维度值")

    # 指标
    pv = Column(Integer, nullable=False, default=0, comment="浏览量")
    uv = Column(Integer, nullable=False, default=0, comment="独立访客数")
    event_count = Column(Integer, nullable=False, default=0, comment="事件总数")
    conversion_count = Column(Integer, nullable=False, default=0, comment="转化数")
    ai_call_count = Column(Integer, nullable=False, default=0, comment="AI 调用次数")

    extra_data = Column(JSON, nullable=True, comment="扩展指标")

    __table_args__ = (
        Index("idx_metric_date_dimension", "metric_date", "dimension_type", "dimension_key"),
    )

    def __repr__(self) -> str:
        return (
            f"<EffectMetricSnapshot(date={self.metric_date}, "
            f"dim={self.dimension_type}:{self.dimension_key})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "metric_date": self.metric_date,
            "dimension_type": self.dimension_type,
            "dimension_key": self.dimension_key,
            "pv": self.pv,
            "uv": self.uv,
            "event_count": self.event_count,
            "conversion_count": self.conversion_count,
            "ai_call_count": self.ai_call_count,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
