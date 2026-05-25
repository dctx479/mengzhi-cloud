"""
客服转人工记录模型 - SQLAlchemy ORM

版本: 1.0
更新日期: 2026-05-25
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Text, Enum, TIMESTAMP, Index,
    ForeignKey
)

from .base import BaseModel, generate_uuid
import enum


class EscalationStatus(enum.Enum):
    """转人工状态"""
    WAITING = "waiting"  # 等待中
    ASSIGNED = "assigned"  # 已分配
    HANDLING = "handling"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CANCELLED = "cancelled"  # 已取消


class KefuEscalation(BaseModel):
    """客服转人工记录"""

    __tablename__ = "kefu_escalations"

    id = Column(BIGINT, primary_key=True, autoincrement=True)

    escalation_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="转人工UUID"
    )

    # 会话关联
    session_id = Column(VARCHAR(36), nullable=True, index=True, comment="客服会话ID")

    # 用户信息
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 转人工原因
    reason = Column(VARCHAR(200), nullable=False, comment="转人工原因")
    context_summary = Column(Text, nullable=True, comment="上下文摘要")
    emotion_type = Column(VARCHAR(50), nullable=True, comment="情绪类型")
    priority = Column(VARCHAR(20), nullable=False, default="normal", comment="优先级")

    # 状态
    status = Column(
        Enum(EscalationStatus),
        nullable=False,
        default=EscalationStatus.WAITING,
        index=True,
        comment="转人工状态"
    )

    # 处理信息
    assigned_agent = Column(VARCHAR(100), nullable=True, comment="分配的客服")
    assigned_at = Column(TIMESTAMP, nullable=True, comment="分配时间")
    resolved_at = Column(TIMESTAMP, nullable=True, comment="解决时间")

    # 元数据
    extra_data = Column(Text, nullable=True, comment="额外元数据(JSON)")

    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_priority", "priority"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "escalation_uuid": self.escalation_uuid,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "reason": self.reason,
            "context_summary": self.context_summary,
            "emotion_type": self.emotion_type,
            "priority": self.priority,
            "status": self.status.value if self.status else None,
            "assigned_agent": self.assigned_agent,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }