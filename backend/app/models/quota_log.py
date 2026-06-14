"""
配额日志数据模型 - SQLAlchemy ORM

版本: 1.0
创建日期: 2026-01-23
"""

from sqlalchemy import Column, BIGINT, String, Integer, Enum, TIMESTAMP, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any
import enum

from .base import BaseModel


class QuotaLogType(enum.Enum):
    """配额日志类型枚举"""

    PURCHASE = "purchase"  # 购买充值
    CONSUME = "consume"  # 消费扣减
    EXPIRE = "expire"  # 过期清零
    REFUND = "refund"  # 退款返还
    GIFT = "gift"  # 赠送
    ADJUST = "adjust"  # 管理员调整


class QuotaLogStatus(enum.Enum):
    """配额日志状态枚举"""

    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    PENDING = "pending"  # 处理中


class QuotaLog(BaseModel):
    """配额日志模型

    记录用户配额的所有变动:
    - 购买充值
    - 使用消费
    - 过期清零
    - 退款返还
    - 管理员调整
    """

    __tablename__ = "quota_logs"

    # 主键
    id = Column(BIGINT, primary_key=True, autoincrement=True, comment="日志ID")

    # 关联信息
    user_id = Column(BIGINT, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")

    order_id = Column(
        BIGINT, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True, comment="关联订单ID"
    )

    # 日志类型
    log_type = Column(Enum(QuotaLogType), nullable=False, index=True, comment="日志类型")

    status = Column(Enum(QuotaLogStatus), nullable=False, default=QuotaLogStatus.SUCCESS, index=True, comment="状态")

    # 配额变动(正数为增加,负数为减少)
    chat_change = Column(Integer, nullable=False, default=0, comment="对话次数变动")

    generation_change = Column(Integer, nullable=False, default=0, comment="生成次数变动")

    token_change = Column(Integer, nullable=False, default=0, comment="Token变动")

    storage_change_mb = Column(Integer, nullable=False, default=0, comment="存储空间变动(MB)")

    # 变动后余额
    chat_balance = Column(Integer, nullable=True, comment="对话次数余额")

    generation_balance = Column(Integer, nullable=True, comment="生成次数余额")

    token_balance = Column(Integer, nullable=True, comment="Token余额")

    storage_balance_mb = Column(Integer, nullable=True, comment="存储余额(MB)")

    # 描述
    description = Column(String(500), nullable=True, comment="变动描述")

    # 备注
    remark = Column(Text, nullable=True, comment="备注")

    # 操作人(管理员调整时记录)
    operator_id = Column(BIGINT, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="操作人ID")

    # 关系
    user = relationship("User", foreign_keys=[user_id], back_populates="quota_logs")

    order = relationship("Order", foreign_keys=[order_id])

    operator = relationship("User", foreign_keys=[operator_id])

    # 索引
    __table_args__ = (
        Index("idx_quota_logs_user_id", "user_id"),
        Index("idx_quota_logs_order_id", "order_id"),
        Index("idx_log_type", "log_type"),
        Index("idx_quota_logs_status", "status"),
        Index("idx_quota_logs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<QuotaLog(id={self.id}, user_id={self.user_id}, type={self.log_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_id": self.order_id,
            "log_type": self.log_type.value if self.log_type else None,
            "status": self.status.value if self.status else None,
            "changes": {
                "chat": self.chat_change,
                "generation": self.generation_change,
                "token": self.token_change,
                "storage_mb": self.storage_change_mb,
            },
            "balances": {
                "chat": self.chat_balance,
                "generation": self.generation_balance,
                "token": self.token_balance,
                "storage_mb": self.storage_balance_mb,
            },
            "description": self.description,
            "remark": self.remark,
            "operator_id": self.operator_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_increase(self) -> bool:
        """检查是否为增加配额"""
        return self.log_type in [QuotaLogType.PURCHASE, QuotaLogType.GIFT, QuotaLogType.REFUND]

    def is_decrease(self) -> bool:
        """检查是否为减少配额"""
        return self.log_type in [QuotaLogType.CONSUME, QuotaLogType.EXPIRE]

    @classmethod
    def create_purchase_log(
        cls,
        user_id: int,
        order_id: int,
        chat_change: int = 0,
        generation_change: int = 0,
        token_change: int = 0,
        storage_change_mb: int = 0,
        description: str = "购买配额套餐",
    ) -> "QuotaLog":
        """创建购买日志"""
        return cls(
            user_id=user_id,
            order_id=order_id,
            log_type=QuotaLogType.PURCHASE,
            status=QuotaLogStatus.SUCCESS,
            chat_change=chat_change,
            generation_change=generation_change,
            token_change=token_change,
            storage_change_mb=storage_change_mb,
            description=description,
        )

    @classmethod
    def create_consume_log(
        cls,
        user_id: int,
        chat_change: int = 0,
        generation_change: int = 0,
        token_change: int = 0,
        storage_change_mb: int = 0,
        description: str = "使用配额",
    ) -> "QuotaLog":
        """创建消费日志"""
        return cls(
            user_id=user_id,
            log_type=QuotaLogType.CONSUME,
            status=QuotaLogStatus.SUCCESS,
            chat_change=-abs(chat_change),  # 确保为负数
            generation_change=-abs(generation_change),
            token_change=-abs(token_change),
            storage_change_mb=-abs(storage_change_mb),
            description=description,
        )
