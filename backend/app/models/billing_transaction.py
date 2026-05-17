"""
计费事务模型
"""
from sqlalchemy import Column, BIGINT, VARCHAR, DECIMAL, TEXT, TIMESTAMP, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import BaseModel


class BillingStatus(str, enum.Enum):
    """计费状态"""
    PENDING = "pending"          # 待确认（预扣费）
    COMPLETED = "completed"      # 已完成
    REFUNDED = "refunded"        # 已退款
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class BillingTransaction(BaseModel):
    """计费事务模型"""

    __tablename__ = "billing_transactions"

    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="交易ID")

    # 关联信息
    enterprise_id = Column(
        BIGINT,
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="企业ID"
    )
    quota_id = Column(BIGINT, ForeignKey("tenant_quotas.id"), nullable=False, comment="配额ID")

    # 交易信息
    service_type = Column(VARCHAR(50), nullable=False, comment="服务类型")
    amount = Column(DECIMAL(10, 4), nullable=False, comment="金额")
    status = Column(SQLEnum(BillingStatus), nullable=False, default=BillingStatus.PENDING, comment="状态")

    # 幂等性
    idempotency_key = Column(VARCHAR(64), unique=True, nullable=True, comment="幂等性key")

    # 请求参数
    request_params = Column(TEXT, nullable=True, comment="请求参数（JSON）")
    actual_usage = Column(TEXT, nullable=True, comment="实际使用情况（JSON）")

    # 退款信息
    refund_amount = Column(DECIMAL(10, 4), nullable=True, comment="退款金额")
    refund_reason = Column(VARCHAR(200), nullable=True, comment="退款原因")

    # 时间戳（completed_at/refunded_at 补充字段，created_at/updated_at 继承自 BaseModel）
    completed_at = Column(TIMESTAMP, nullable=True, comment="完成时间")
    refunded_at = Column(TIMESTAMP, nullable=True, comment="退款时间")

    # 关系
    quota = relationship("TenantQuota", back_populates="transactions")

    # 索引
    __table_args__ = (
        Index("idx_enterprise_id", "enterprise_id"),
        Index("idx_quota_id", "quota_id"),
        Index("idx_status", "status"),
        Index("idx_created_at", "created_at"),
        Index("idx_idempotency_key", "idempotency_key"),
    )

    def __repr__(self):
        return f"<BillingTransaction(id={self.id}, enterprise_id={self.enterprise_id}, amount={self.amount}, status={self.status})>"
