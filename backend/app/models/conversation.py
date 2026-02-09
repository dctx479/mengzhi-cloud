"""
AI对话会话模型 - SQLAlchemy ORM

包含：
- 对话会话管理
- 对话统计
- Agent类型
- 会话状态

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Text, Enum, TIMESTAMP, Index,
    UniqueConstraint, Integer, ForeignKey, Float, JSON, Boolean
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from .base import BaseModel, generate_uuid


class AgentType(enum.Enum):
    """AI代理类型枚举"""
    MARKETING = "marketing"  # 营销顾问
    CULTURAL = "cultural"  # 文化专家
    DATA = "data"  # 数据分析师
    GENERAL = "general"  # 通用助手


class ConversationStatus(enum.Enum):
    """对话状态枚举"""
    ACTIVE = "active"  # 进行中
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


class ContentType(enum.Enum):
    """内容类型枚举"""
    TEXT = "text"  # 文本
    IMAGE = "image"  # 图片
    FILE = "file"  # 文件


class Conversation(BaseModel):
    """AI对话会话模型

    对话会话包含：
    - 会话标题和描述
    - Agent类型
    - Token和成本统计
    - 会话状态
    - 关联的消息列表
    """

    __tablename__ = "ai_conversations"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="对话ID"
    )

    # UUID标识
    conversation_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="对话UUID"
    )

    # 关联信息
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 对话信息
    title = Column(
        VARCHAR(200),
        nullable=False,
        default="新对话",
        comment="对话标题"
    )
    description = Column(
        Text,
        nullable=True,
        comment="对话描述"
    )

    # Agent类型
    agent_type = Column(
        Enum(AgentType),
        nullable=False,
        default=AgentType.GENERAL,
        index=True,
        comment="Agent类型"
    )

    # 会话状态
    status = Column(
        Enum(ConversationStatus),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        index=True,
        comment="会话状态"
    )

    # 统计信息
    message_count = Column(
        Integer,
        default=0,
        comment="消息数量"
    )
    total_tokens = Column(
        Integer,
        default=0,
        comment="总Token数"
    )
    total_cost = Column(
        Float,
        default=0.0,
        comment="总成本（元）"
    )

    # 会话配置
    model = Column(
        VARCHAR(100),
        default="deepseek-chat",
        comment="默认模型"
    )
    temperature = Column(
        Float,
        default=0.7,
        comment="温度参数"
    )
    max_tokens = Column(
        Integer,
        default=2000,
        comment="最大Token数"
    )

    # 元数据
    metadata_info = Column(
        JSON,
        nullable=True,
        comment="额外元数据"
    )

    # 归档和删除时间
    archived_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="归档时间"
    )
    deleted_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="软删除时间"
    )

    # 关系
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="conversations"
    )
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("conversation_uuid", name="uk_conversation_uuid"),
        Index("idx_user_id", "user_id"),
        Index("idx_agent_type", "agent_type"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
        Index("idx_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, title={self.title}, agent_type={self.agent_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "conversation_uuid": self.conversation_uuid,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "status": self.status.value if self.status else None,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata_info": self.metadata_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }

    def is_active(self) -> bool:
        """检查是否为活跃对话"""
        return self.status == ConversationStatus.ACTIVE

    def is_archived(self) -> bool:
        """检查是否已归档"""
        return self.status == ConversationStatus.ARCHIVED

    def archive(self) -> None:
        """归档对话"""
        self.status = ConversationStatus.ARCHIVED
        self.archived_at = datetime.utcnow()

    def activate(self) -> None:
        """激活对话"""
        self.status = ConversationStatus.ACTIVE
        self.archived_at = None

    def soft_delete(self) -> None:
        """软删除对话"""
        self.status = ConversationStatus.DELETED
        self.deleted_at = datetime.utcnow()

    def get_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        return {
            "id": self.id,
            "title": self.title,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def get_by_uuid(cls, conversation_uuid: str) -> Optional["Conversation"]:
        """根据UUID获取对话"""
        pass

    @classmethod
    def get_user_conversations(cls, user_id: int, status: ConversationStatus = None) -> list:
        """获取用户的所有对话"""
        pass

    @classmethod
    def get_active_conversations(cls, user_id: int) -> list:
        """获取用户的活跃对话"""
        pass
