"""
客服工单模型 - SQLAlchemy ORM

包含：
- 工单状态、优先级、类别枚举
- 工单主体（KefuTicket）
- 工单消息（KefuTicketMessage）

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


class TicketStatus(enum.Enum):
    """工单状态枚举"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭
    REOPENED = "reopened"  # 已重新打开


class TicketPriority(enum.Enum):
    """工单优先级枚举"""
    LOW = "low"  # 低
    NORMAL = "normal"  # 普通
    HIGH = "high"  # 高
    URGENT = "urgent"  # 紧急


class TicketCategory(enum.Enum):
    """工单类别枚举"""
    REFUND = "refund"  # 退款
    RETURN = "return"  # 退货
    EXCHANGE = "exchange"  # 换货
    REPAIR = "repair"  # 维修
    DELIVERY = "delivery"  # 配送
    COMPLAINT = "complaint"  # 投诉
    INQUIRY = "inquiry"  # 咨询
    PRODUCT = "product"  # 产品咨询
    QUALITY = "quality"  # 质量反馈
    OTHER = "other"  # 其他


class KefuTicket(BaseModel):
    """客服工单模型"""

    __tablename__ = "kefu_tickets"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="工单ID")

    ticket_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="工单UUID"
    )

    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    category = Column(
        Enum(TicketCategory),
        nullable=False,
        default=TicketCategory.INQUIRY,
        index=True,
        comment="工单类别"
    )
    priority = Column(
        Enum(TicketPriority),
        nullable=False,
        default=TicketPriority.NORMAL,
        comment="优先级"
    )
    status = Column(
        Enum(TicketStatus),
        nullable=False,
        default=TicketStatus.PENDING,
        index=True,
        comment="工单状态"
    )

    title = Column(VARCHAR(200), nullable=False, comment="工单标题")
    description = Column(Text, nullable=False, comment="工单描述")
    user_name = Column(VARCHAR(100), nullable=True, comment="用户姓名")

    assigned_to = Column(VARCHAR(100), nullable=True, comment="处理人")
    resolved_at = Column(TIMESTAMP, nullable=True, comment="解决时间")
    closed_at = Column(TIMESTAMP, nullable=True, comment="关闭时间")

    emotion = Column(VARCHAR(50), nullable=True, comment="检测到的情绪")
    emotion_intensity = Column(Integer, nullable=True, comment="情绪强度 1-10")
    intent = Column(VARCHAR(50), nullable=True, comment="用户意图")
    extra_data = Column(JSON, nullable=True, comment="额外元数据")

    user = relationship("User", foreign_keys=[user_id])
    messages = relationship(
        "KefuTicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="KefuTicketMessage.created_at"
    )

    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_priority", "priority"),
        Index("idx_created", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_uuid": self.ticket_uuid,
            "user_id": self.user_id,
            "category": self.category.value if self.category else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "description": self.description,
            "user_name": self.user_name,
            "assigned_to": self.assigned_to,
            "emotion": self.emotion,
            "emotion_intensity": self.emotion_intensity,
            "intent": self.intent,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }


class KefuTicketMessage(BaseModel):
    """客服工单消息模型"""

    __tablename__ = "kefu_ticket_messages"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    ticket_id = Column(
        BIGINT,
        ForeignKey("kefu_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="工单ID"
    )

    role = Column(VARCHAR(20), nullable=False, comment="发送者: user/agent/system")
    content = Column(Text, nullable=False, comment="消息内容")

    msg_metadata = Column(JSON, nullable=True, comment="消息元数据")

    ticket = relationship("KefuTicket", back_populates="messages")

    __table_args__ = (
        Index("idx_ticket_created", "ticket_id", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.msg_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }