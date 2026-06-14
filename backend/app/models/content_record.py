"""
内容生成记录数据模型 - SQLAlchemy ORM

包含：
- 内容生成配置
- 生成结果
- AI调用信息
- 质量评估
- 使用统计

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column,
    BIGINT,
    VARCHAR,
    Enum,
    TIMESTAMP,
    Index,
    UniqueConstraint,
    TEXT,
    Integer,
    ForeignKey,
    JSON,
    DECIMAL,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from .base import BaseModel, generate_uuid


class ContentType(enum.Enum):
    """内容类型枚举"""

    COPY = "copy"  # 营销文案
    SCRIPT = "script"  # 直播脚本
    VIDEO_COPY = "video_copy"  # 短视频文案
    SLOGAN = "slogan"  # 广告标语
    STORY = "story"  # 品牌故事


class Platform(enum.Enum):
    """目标平台枚举"""

    DOUYIN = "douyin"  # 抖音
    XIAOHONGSHU = "xiaohongshu"  # 小红书
    WECHAT = "wechat"  # 微信公众号
    WEIBO = "weibo"  # 微博
    KUAISHOU = "kuaishou"  # 快手
    GENERAL = "general"  # 通用


class Style(enum.Enum):
    """内容风格枚举"""

    FORMAL = "formal"  # 正式
    CASUAL = "casual"  # 轻松
    HUMOROUS = "humorous"  # 幽默
    EMOTIONAL = "emotional"  # 情感
    PROFESSIONAL = "professional"  # 专业


class LengthType(enum.Enum):
    """长度类型枚举"""

    SHORT = "short"  # 短（<500字）
    MEDIUM = "medium"  # 中等（500-1500字）
    LONG = "long"  # 长（>1500字）


class RecordStatus(enum.Enum):
    """记录状态枚举"""

    GENERATING = "generating"  # 生成中
    COMPLETED = "completed"  # 完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class ContentRecord(BaseModel):
    """内容生成记录模型

    记录包含：
    - 用户和产品关联
    - 生成配置参数
    - 输入和输出内容
    - AI调用信息
    - 质量评估
    - 使用统计
    """

    __tablename__ = "content_records"

    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="记录ID")

    # UUID标识
    record_uuid = Column(
        VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="记录UUID"
    )

    # 关联信息
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    product_id = Column(
        BIGINT, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True, comment="产品ID"
    )
    conversation_id = Column(
        BIGINT, ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True, comment="关联对话ID"
    )

    # 生成配置
    content_type = Column(Enum(ContentType), nullable=False, index=True, comment="内容类型")
    platform = Column(Enum(Platform), nullable=False, default=Platform.GENERAL, index=True, comment="目标平台")
    style = Column(Enum(Style), default=Style.CASUAL, comment="风格")
    length_type = Column(Enum(LengthType), default=LengthType.MEDIUM, comment="长度类型")

    # 输入参数
    input_params = Column(JSON, nullable=False, comment="输入参数(JSON)")
    keywords = Column(JSON, nullable=True, comment="关键词数组")

    # 生成结果
    generated_content = Column(TEXT, nullable=False, comment="生成的内容")
    edited_content = Column(TEXT, nullable=True, comment="用户编辑后的内容")

    # AI调用信息
    model_name = Column(VARCHAR(100), nullable=True, comment="使用的模型名称")
    prompt_tokens = Column(Integer, default=0, comment="Prompt Token数")
    completion_tokens = Column(Integer, default=0, comment="生成Token数")
    total_tokens = Column(Integer, default=0, comment="总Token数")
    generation_time_ms = Column(Integer, nullable=True, comment="生成耗时(毫秒)")

    # 质量评估
    quality_score = Column(DECIMAL(3, 2), nullable=True, comment="质量评分(0-5)")
    user_rating = Column(Integer, nullable=True, comment="用户评分(1-5)")
    user_feedback = Column(TEXT, nullable=True, comment="用户反馈")

    # 状态
    status = Column(Enum(RecordStatus), nullable=False, default=RecordStatus.GENERATING, index=True, comment="状态")
    error_message = Column(TEXT, nullable=True, comment="错误信息")

    # 使用统计
    copy_count = Column(Integer, default=0, comment="复制次数")
    export_count = Column(Integer, default=0, comment="导出次数")

    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="content_records")
    product = relationship("Product", foreign_keys=[product_id], back_populates="content_records")

    # 索引定义
    __table_args__ = (
        UniqueConstraint("record_uuid", name="uk_record_uuid"),
        Index("idx_content_records_user_id", "user_id"),
        Index("idx_content_records_product_id", "product_id"),
        Index("idx_content_records_content_type", "content_type"),
        Index("idx_content_records_platform", "platform"),
        Index("idx_content_records_status", "status"),
        Index("idx_content_records_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        ct_val = self.content_type.value if hasattr(self.content_type, "value") else (self.content_type or "unknown")
        return f"<ContentRecord(id={self.id}, user_id={self.user_id}, content_type={ct_val})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "record_uuid": self.record_uuid,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "conversation_id": self.conversation_id,
            "content_type": self.content_type.value if self.content_type else None,
            "platform": self.platform.value if self.platform else None,
            "style": self.style.value if self.style else None,
            "length_type": self.length_type.value if self.length_type else None,
            "input_params": self.input_params,
            "keywords": self.keywords,
            "generated_content": self.generated_content,
            "edited_content": self.edited_content,
            "model_name": self.model_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "generation_time_ms": self.generation_time_ms,
            "quality_score": float(self.quality_score) if self.quality_score else None,
            "user_rating": self.user_rating,
            "user_feedback": self.user_feedback,
            "status": self.status.value if self.status else None,
            "error_message": self.error_message,
            "copy_count": self.copy_count,
            "export_count": self.export_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_completed(self) -> bool:
        """检查是否生成完成"""
        return self.status == RecordStatus.COMPLETED

    def is_failed(self) -> bool:
        """检查是否生成失败"""
        return self.status == RecordStatus.FAILED

    def get_token_cost(self) -> Dict[str, int]:
        """获取Token消耗"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def get_usage_count(self) -> Dict[str, int]:
        """获取使用计数"""
        return {
            "copy_count": self.copy_count,
            "export_count": self.export_count,
        }

    @classmethod
    def get_by_uuid(cls, record_uuid: str) -> Optional["ContentRecord"]:
        """根据UUID获取记录"""
        pass

    @classmethod
    def get_user_records(cls, user_id: int, limit: int = 20) -> list:
        """获取用户的内容记录"""
        pass

    @classmethod
    def get_by_type_and_platform(cls, content_type: str, platform: str) -> list:
        """按内容类型和平台获取记录"""
        pass

    @classmethod
    def get_recent_successful_records(cls, user_id: int, limit: int = 10) -> list:
        """获取用户最近成功的记录"""
        pass
