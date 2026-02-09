"""
支付记录数据模型 - SQLAlchemy ORM

版本: 1.0
创建日期: 2026-01-23
"""

from sqlalchemy import (
    Column, BIGINT, String, DECIMAL, Enum, TIMESTAMP,
    ForeignKey, Index, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
import enum

from .base import BaseModel, generate_uuid


class PaymentMethod(enum.Enum):
    """支付方式枚举"""
    ALIPAY = "alipay"  # 支付宝
    WECHAT = "wechat"  # 微信支付
    BALANCE = "balance"  # 余额支付
    BANK_CARD = "bank_card"  # 银行卡


class PaymentStatus(enum.Enum):
    """支付状态枚举"""
    PENDING = "pending"  # 待支付
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"  # 支付成功
    FAILED = "failed"  # 支付失败
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款


class Payment(BaseModel):
    """支付记录模型

    记录订单的支付信息:
    - 支付基本信息(支付单号、订单、金额)
    - 支付方式和渠道
    - 支付状态和时间
    - 第三方支付信息
    """

    __tablename__ = "payments"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="支付ID"
    )

    # 支付单号(唯一)
    payment_no = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="支付单号"
    )

    # 关联订单
    order_id = Column(
        BIGINT,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="订单ID"
    )

    # 支付信息
    amount = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="支付金额(元)"
    )

    payment_method = Column(
        Enum(PaymentMethod),
        nullable=False,
        index=True,
        comment="支付方式"
    )

    status = Column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
        comment="支付状态"
    )

    # 第三方支付信息
    transaction_id = Column(
        String(128),
        nullable=True,
        index=True,
        comment="第三方交易号"
    )

    channel_order_no = Column(
        String(128),
        nullable=True,
        comment="支付渠道订单号"
    )

    channel_response = Column(
        Text,
        nullable=True,
        comment="支付渠道响应(JSON)"
    )

    # 支付时间
    paid_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="支付成功时间"
    )

    failed_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="支付失败时间"
    )

    refunded_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="退款时间"
    )

    # 失败原因
    failure_reason = Column(
        Text,
        nullable=True,
        comment="失败原因"
    )

    # 备注
    remark = Column(
        Text,
        nullable=True,
        comment="备注"
    )

    # 关系
    order = relationship(
        "Order",
        foreign_keys=[order_id],
        back_populates="payments"
    )

    # 索引
    __table_args__ = (
        Index("idx_order_id", "order_id"),
        Index("idx_payment_no", "payment_no"),
        Index("idx_transaction_id", "transaction_id"),
        Index("idx_status", "status"),
        Index("idx_payment_method", "payment_method"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, payment_no={self.payment_no}, status={self.status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "payment_no": self.payment_no,
            "order_id": self.order_id,
            "amount": float(self.amount) if self.amount else 0,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "status": self.status.value if self.status else None,
            "transaction_id": self.transaction_id,
            "channel_order_no": self.channel_order_no,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
            "failure_reason": self.failure_reason,
            "remark": self.remark,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_pending(self) -> bool:
        """检查是否待支付"""
        return self.status == PaymentStatus.PENDING

    def is_success(self) -> bool:
        """检查是否支付成功"""
        return self.status == PaymentStatus.SUCCESS

    def is_failed(self) -> bool:
        """检查是否支付失败"""
        return self.status == PaymentStatus.FAILED

    def mark_as_success(self, transaction_id: Optional[str] = None) -> None:
        """标记为支付成功"""
        self.status = PaymentStatus.SUCCESS
        self.paid_at = datetime.utcnow()
        if transaction_id:
            self.transaction_id = transaction_id

    def mark_as_failed(self, reason: Optional[str] = None) -> None:
        """标记为支付失败"""
        self.status = PaymentStatus.FAILED
        self.failed_at = datetime.utcnow()
        if reason:
            self.failure_reason = reason

    def mark_as_refunded(self) -> None:
        """标记为已退款"""
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = datetime.utcnow()
