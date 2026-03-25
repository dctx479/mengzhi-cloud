"""
订单数据模型 - SQLAlchemy ORM

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


class OrderStatus(enum.Enum):
    """订单状态枚举"""
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    COMPLETED = "completed"  # 已完成(配额已发放)
    CANCELLED = "cancelled"  # 已取消
    REFUNDED = "refunded"  # 已退款
    FAILED = "failed"  # 支付失败


class Order(BaseModel):
    """订单模型

    记录用户购买配额套餐的订单信息:
    - 订单基本信息(订单号、用户、套餐)
    - 价格信息
    - 订单状态和时间
    """

    __tablename__ = "orders"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="订单ID"
    )

    # 订单号(唯一)
    order_no = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="订单号"
    )

    # 关联信息
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    package_id = Column(
        BIGINT,
        ForeignKey("quota_packages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="套餐ID"
    )

    # 订单信息(冗余存储,防止套餐修改影响历史订单)
    package_name = Column(
        String(100),
        nullable=False,
        comment="套餐名称"
    )

    package_type = Column(
        String(50),
        nullable=False,
        comment="套餐类型"
    )

    # 价格信息
    amount = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="订单金额(元)"
    )

    original_amount = Column(
        DECIMAL(10, 2),
        nullable=True,
        comment="原价"
    )

    discount_amount = Column(
        DECIMAL(10, 2),
        nullable=True,
        default=0,
        comment="优惠金额"
    )

    # 配额信息(冗余存储)
    chat_quota = Column(
        BIGINT,
        nullable=False,
        default=0,
        comment="对话次数配额"
    )

    generation_quota = Column(
        BIGINT,
        nullable=False,
        default=0,
        comment="生成次数配额"
    )

    token_quota = Column(
        BIGINT,
        nullable=False,
        default=0,
        comment="Token配额"
    )

    storage_quota_mb = Column(
        BIGINT,
        nullable=False,
        default=0,
        comment="存储配额(MB)"
    )

    validity_days = Column(
        BIGINT,
        nullable=False,
        default=30,
        comment="有效期(天)"
    )

    # 订单状态
    status = Column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
        comment="订单状态"
    )

    # 备注
    remark = Column(
        Text,
        nullable=True,
        comment="订单备注"
    )

    # 时间信息
    paid_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="支付时间"
    )

    completed_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="完成时间"
    )

    cancelled_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="取消时间"
    )

    expired_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="过期时间"
    )

    # 关系
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="orders"
    )

    package = relationship(
        "QuotaPackage",
        foreign_keys=[package_id],
        back_populates="orders"
    )

    payments = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_package_id", "package_id"),
        Index("idx_status", "status"),
        Index("idx_order_no", "order_no"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_no={self.order_no}, status={self.status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "order_no": self.order_no,
            "user_id": self.user_id,
            "package_id": self.package_id,
            "package_name": self.package_name,
            "package_type": self.package_type,
            "amount": float(self.amount) if self.amount else 0,
            "original_amount": float(self.original_amount) if self.original_amount else None,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "quotas": {
                "chat": self.chat_quota,
                "generation": self.generation_quota,
                "token": self.token_quota,
                "storage_mb": self.storage_quota_mb,
            },
            "validity_days": self.validity_days,
            "status": self.status.value if self.status else None,
            "remark": self.remark,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "expired_at": self.expired_at.isoformat() if self.expired_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_pending(self) -> bool:
        """检查是否待支付"""
        return self.status == OrderStatus.PENDING

    def is_paid(self) -> bool:
        """检查是否已支付"""
        return self.status in [OrderStatus.PAID, OrderStatus.COMPLETED]

    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == OrderStatus.COMPLETED

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self.status == OrderStatus.CANCELLED

    def can_pay(self) -> bool:
        """检查是否可以支付"""
        return self.status == OrderStatus.PENDING

    def can_cancel(self) -> bool:
        """检查是否可以取消"""
        return self.status in [OrderStatus.PENDING, OrderStatus.FAILED]

    def mark_as_paid(self) -> None:
        """标记为已支付
        
        只允许从 PENDING 状态转换到 PAID
        
        Raises:
            ValueError: 如果当前状态不是 PENDING
        """
        if self.status != OrderStatus.PENDING:
            raise ValueError(
                f"Cannot mark order as paid: order is in {self.status.value} status, "
                f"only {OrderStatus.PENDING.value} orders can be paid"
            )
        self.status = OrderStatus.PAID
        self.paid_at = datetime.utcnow()

    def mark_as_completed(self) -> None:
        """标记为已完成
        
        只允许从 PAID 状态转换到 COMPLETED
        
        Raises:
            ValueError: 如果当前状态不是 PAID
        """
        if self.status != OrderStatus.PAID:
            raise ValueError(
                f"Cannot mark order as completed: order is in {self.status.value} status, "
                f"only {OrderStatus.PAID.value} orders can be completed"
            )
        self.status = OrderStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_as_cancelled(self, remark: Optional[str] = None) -> None:
        """标记为已取消
        
        只允许从 PENDING、FAILED 状态转换到 CANCELLED
        
        Raises:
            ValueError: 如果当前状态不允许取消
        """
        if not self.can_cancel():
            raise ValueError(
                f"Cannot mark order as cancelled: order is in {self.status.value} status, "
                f"only {OrderStatus.PENDING.value} or {OrderStatus.FAILED.value} orders can be cancelled"
            )
        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        if remark:
            self.remark = remark

    def mark_as_failed(self, remark: Optional[str] = None) -> None:
        """标记为失败
        
        只允许从 PENDING 状态转换到 FAILED
        
        Raises:
            ValueError: 如果当前状态不是 PENDING
        """
        if self.status != OrderStatus.PENDING:
            raise ValueError(
                f"Cannot mark order as failed: order is in {self.status.value} status, "
                f"only {OrderStatus.PENDING.value} orders can fail"
            )
        self.status = OrderStatus.FAILED
        if remark:
            self.remark = remark
