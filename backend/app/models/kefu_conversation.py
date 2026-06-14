"""
客服会话模型 - SQLAlchemy ORM

包含：
- 客服会话（KefuConversation）
- 客服消息（KefuMessage）

版本: 1.0
更新日期: 2026-05-25
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Text, Enum, TIMESTAMP, Index,
    Integer, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel, generate_uuid


class KefuConversationStatus(enum.Enum):
    """客服会话状态"""
    ACTIVE = "active"  # 进行中
    ARCHIVED = "archived"  # 已归档
    DELETED = "deleted"  # 已删除


class KefuConversation(BaseModel):
    """客服会话模型"""

    __tablename__ = "kefu_conversations"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    session_id = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="会话UUID"
    )

    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    status = Column(
        Enum(KefuConversationStatus),
        nullable=False,
        default=KefuConversationStatus.ACTIVE,
        index=True,
        comment="会话状态"
    )

    title = Column(VARCHAR(200), nullable=False, default="新会话", comment="会话标题")
    user_name = Column(VARCHAR(100), nullable=True, comment="用户姓名")

    # 统计
    message_count = Column(Integer, default=0, comment="消息数量")

    # 路由信息
    emotion_type = Column(VARCHAR(50), nullable=True, comment="最近情绪")
    intent_type = Column(VARCHAR(50), nullable=True, comment="最近意图")

    # 元数据
    extra_data = Column(JSON, nullable=True, comment="额外元数据")

    user = relationship("User", foreign_keys=[user_id])
    messages = relationship(
        "KefuMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="KefuMessage.created_at"
    )

    __table_args__ = (
        Index("idx_kefu_conversations_user_status", "user_id", "status"),
        Index("idx_kefu_conversations_created", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "user_name": self.user_name,
            "message_count": self.message_count,
            "emotion_type": self.emotion_type,
            "intent_type": self.intent_type,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class KefuMessage(BaseModel):
    """客服消息模型"""

    __tablename__ = "kefu_messages"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    conversation_id = Column(
        BIGINT,
        ForeignKey("kefu_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="会话ID"
    )

    role = Column(VARCHAR(20), nullable=False, comment="发送者: user/agent/system")
    content = Column(Text, nullable=False, comment="消息内容")

    # 路由信息
    emotion = Column(VARCHAR(50), nullable=True, comment="情绪类型")
    emotion_intensity = Column(Integer, nullable=True, comment="情绪强度")
    intent = Column(VARCHAR(50), nullable=True, comment="意图类型")
    confidence = Column(Integer, nullable=True, comment="置信度 0-100")
    action = Column(VARCHAR(50), nullable=True, comment="路由动作")

    # 元数据
    extra_data = Column(JSON, nullable=True, comment="额外元数据")

    conversation = relationship("KefuConversation", back_populates="messages")

    __table_args__ = (
        Index("idx_conv_created", "conversation_id", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "emotion": self.emotion,
            "emotion_intensity": self.emotion_intensity,
            "intent": self.intent,
            "confidence": self.confidence,
            "action": self.action,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }