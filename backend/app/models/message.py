"""
AI对话消息模型 - SQLAlchemy ORM

包含：
- 消息内容
- 消息元数据（Token、成本）
- 消息反馈
- 消息统计

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column,
    BIGINT,
    VARCHAR,
    Text,
    Enum,
    TIMESTAMP,
    Index,
    UniqueConstraint,
    Integer,
    ForeignKey,
    Float,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from .base import BaseModel, generate_uuid


class MessageRole(enum.Enum):
    """消息角色枚举"""

    USER = "user"  # 用户消息
    ASSISTANT = "assistant"  # 助手消息
    SYSTEM = "system"  # 系统消息


class Message(BaseModel):
    """AI对话消息模型

    消息包含：
    - 消息内容和角色
    - Token消耗和成本
    - 消息反馈评分
    - 关联的对话信息
    """

    __tablename__ = "ai_messages"

    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="消息ID")

    # UUID标识
    message_uuid = Column(
        VARCHAR(36), nullable=False, unique=True, index=True, default=generate_uuid, comment="消息UUID"
    )

    # 关联信息
    conversation_id = Column(
        BIGINT, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True, comment="对话ID"
    )

    # 消息内容
    role = Column(Enum(MessageRole), nullable=False, index=True, comment="消息角色")
    content = Column(Text, nullable=False, comment="消息内容")

    # Token统计
    input_tokens = Column(Integer, default=0, comment="输入Token数")
    output_tokens = Column(Integer, default=0, comment="输出Token数")
    total_tokens = Column(Integer, default=0, comment="总Token数")

    # 成本
    cost = Column(Float, default=0.0, comment="消息成本（元）")

    # 模型信息
    model = Column(VARCHAR(100), default="deepseek-chat", comment="使用的模型")
    finish_reason = Column(VARCHAR(50), nullable=True, comment="完成原因：stop/length/error")

    # 反馈
    rating = Column(Integer, nullable=True, comment="用户评分（1-5）")
    feedback = Column(Text, nullable=True, comment="用户反馈")
    feedback_type = Column(VARCHAR(50), nullable=True, comment="反馈类型：helpful/unhelpful/incorrect")

    # 元数据
    metadata_info = Column(JSON, nullable=True, comment="额外元数据")

    # 关系
    conversation = relationship("Conversation", foreign_keys=[conversation_id], back_populates="messages")

    # 索引定义
    __table_args__ = (
        UniqueConstraint("message_uuid", name="uk_message_uuid"),
        Index("idx_conversation_id", "conversation_id"),
        Index("idx_role", "role"),
        Index("idx_ai_messages_created_at", "created_at"),
        Index("idx_conversation_created", "conversation_id", "created_at"),
    )

    def __repr__(self) -> str:
        role_val = self.role.value if hasattr(self.role, "value") else (self.role or "unknown")
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={role_val})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "message_uuid": self.message_uuid,
            "conversation_id": self.conversation_id,
            "role": self.role.value if self.role else None,
            "content": self.content,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "rating": self.rating,
            "feedback": self.feedback,
            "feedback_type": self.feedback_type,
            "metadata_info": self.metadata_info,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_user_message(self) -> bool:
        """检查是否为用户消息"""
        return self.role == MessageRole.USER

    def is_assistant_message(self) -> bool:
        """检查是否为助手消息"""
        return self.role == MessageRole.ASSISTANT

    def get_summary(self) -> Dict[str, Any]:
        """获取消息摘要"""
        return {
            "id": self.id,
            "role": self.role.value if self.role else None,
            "length": len(self.content) if self.content else 0,
            "tokens": self.total_tokens,
            "cost": self.cost,
            "rating": self.rating,
        }

    @classmethod
    def get_by_uuid(cls, message_uuid: str) -> Optional["Message"]:
        """根据UUID获取消息"""
        pass

    @classmethod
    def get_conversation_messages(cls, conversation_id: int, limit: int = 100) -> list:
        """获取对话的所有消息"""
        pass

    @classmethod
    def get_assistant_messages(cls, conversation_id: int) -> list:
        """获取对话中的助手消息"""
        pass
