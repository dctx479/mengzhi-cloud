"""
配额管理数据模型 - SQLAlchemy ORM

包含：
- 租户配额（tenant_quotas）
- 配额使用记录（quota_usage）
- 配额类型和周期管理

版本: 1.0
更新日期: 2026-01-22
"""

from sqlalchemy import (
    Column, BIGINT, Enum, Integer, DATE, TIMESTAMP, Index,
    UniqueConstraint, ForeignKey, String, VARCHAR, Float, TEXT, CheckConstraint
)
from sqlalchemy.orm import relationship
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List
import enum

from .base import BaseModel


class QuotaResourceType(enum.Enum):
    """配额资源类型枚举"""
    TOKEN = "token"  # Token配额
    MESSAGE = "message"  # 消息数配额
    API_CALL = "api_call"  # API调用次数
    GENERATION = "generation"  # 内容生成次数
    STORAGE = "storage"  # 存储空间(MB)


class QuotaPeriodType(enum.Enum):
    """配额周期类型枚举"""
    DAILY = "daily"  # 每日
    MONTHLY = "monthly"  # 每月
    YEARLY = "yearly"  # 每年
    TOTAL = "total"  # 总计（不重置）


class QuotaAlertLevel(enum.Enum):
    """配额预警级别枚举"""
    WARNING = "warning"  # 警告（80%）
    CRITICAL = "critical"  # 严重（90%）
    EXHAUSTED = "exhausted"  # 耗尽（100%）


class TenantQuota(BaseModel):
    """租户配额模型

    定义租户的配额限制，支持多种资源类型和周期
    """

    __tablename__ = "tenant_quotas"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="配额ID"
    )

    # 租户关联（支持企业和个人用户）
    enterprise_id = Column(
        BIGINT,
        ForeignKey("enterprises.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="企业ID（企业用户）"
    )
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="用户ID（个人用户）"
    )

    # 配额类型
    resource_type = Column(
        Enum(QuotaResourceType),
        nullable=False,
        index=True,
        comment="资源类型"
    )
    period_type = Column(
        Enum(QuotaPeriodType),
        nullable=False,
        index=True,
        comment="周期类型"
    )

    # 配额限制
    quota_limit = Column(
        BIGINT,
        nullable=False,
        default=0,
        comment="配额限制"
    )
    quota_used = Column(
        BIGINT,
        nullable=False,
        default=0,
        comment="已使用配额"
    )

    # 配额周期
    period_start = Column(
        DATE,
        nullable=False,
        comment="周期开始日期"
    )
    period_end = Column(
        DATE,
        nullable=False,
        comment="周期结束日期"
    )

    # 预警设置
    warning_threshold = Column(
        Integer,
        default=80,
        comment="预警阈值（百分比，默认80%）"
    )
    critical_threshold = Column(
        Integer,
        default=90,
        comment="严重预警阈值（百分比，默认90%）"
    )

    # 预警状态
    last_alert_level = Column(
        Enum(QuotaAlertLevel),
        nullable=True,
        comment="最后预警级别"
    )
    last_alert_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="最后预警时间"
    )

    # 是否启用
    is_active = Column(
        Integer,
        default=1,
        comment="是否启用（1启用，0禁用）"
    )

    # 备注
    description = Column(
        VARCHAR(500),
        nullable=True,
        comment="配额描述"
    )

    # 关系
    enterprise = relationship(
        "Enterprise",
        foreign_keys=[enterprise_id],
        back_populates="quotas"
    )
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="tenant_quotas"
    )
    usage_records = relationship(
        "QuotaUsage",
        back_populates="quota",
        cascade="all, delete-orphan"
    )
    transactions = relationship(
        "BillingTransaction",
        back_populates="quota",
        cascade="all, delete-orphan"
    )

    # 索引定义
    __table_args__ = (
        # 确保同一租户、资源类型、周期类型在同一时间段内只有一条记录
        UniqueConstraint(
            "enterprise_id", "resource_type", "period_type", "period_start",
            name="uk_enterprise_quota_period"
        ),
        UniqueConstraint(
            "user_id", "resource_type", "period_type", "period_start",
            name="uk_user_quota_period"
        ),
        # 确保企业ID和用户ID至少有一个不为NULL
        CheckConstraint(
            "(enterprise_id IS NOT NULL) OR (user_id IS NOT NULL)",
            name="ck_quota_tenant_not_null"
        ),
        Index("idx_enterprise_id", "enterprise_id"),
        Index("idx_user_id", "user_id"),
        Index("idx_resource_type", "resource_type"),
        Index("idx_period_type", "period_type"),
        Index("idx_period_end", "period_end"),
        Index("idx_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        tenant = f"enterprise_{self.enterprise_id}" if self.enterprise_id else f"user_{self.user_id}"
        return f"<TenantQuota(id={self.id}, {tenant}, {self.resource_type.value}, {self.period_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "enterprise_id": self.enterprise_id,
            "user_id": self.user_id,
            "resource_type": self.resource_type.value if self.resource_type else None,
            "period_type": self.period_type.value if self.period_type else None,
            "quota_limit": self.quota_limit,
            "quota_used": self.quota_used,
            "quota_remaining": max(0, self.quota_limit - self.quota_used),
            "usage_percentage": self.get_usage_percentage(),
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
            },
            "thresholds": {
                "warning": self.warning_threshold,
                "critical": self.critical_threshold,
            },
            "alert": {
                "level": self.last_alert_level.value if self.last_alert_level else None,
                "at": self.last_alert_at.isoformat() if self.last_alert_at else None,
            },
            "is_active": bool(self.is_active),
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_usage_percentage(self) -> float:
        """获取使用百分比"""
        if self.quota_limit <= 0:
            return 0.0
        return round((self.quota_used / self.quota_limit * 100), 2)

    def get_remaining(self) -> int:
        """获取剩余配额"""
        return max(0, self.quota_limit - self.quota_used)

    def is_sufficient(self, required: int = 1) -> bool:
        """检查配额是否充足"""
        if not self.is_active:
            return False
        if not self.is_in_period():
            return False
        return self.quota_used + required <= self.quota_limit

    def is_in_period(self) -> bool:
        """检查是否在配额周期内"""
        today = date.today()
        return self.period_start <= today <= self.period_end

    def is_expired(self) -> bool:
        """检查配额是否已过期"""
        today = date.today()
        return today > self.period_end

    def should_alert(self) -> Optional[QuotaAlertLevel]:
        """检查是否需要预警"""
        percentage = self.get_usage_percentage()

        if percentage >= 100:
            return QuotaAlertLevel.EXHAUSTED
        elif percentage >= self.critical_threshold:
            return QuotaAlertLevel.CRITICAL
        elif percentage >= self.warning_threshold:
            return QuotaAlertLevel.WARNING

        return None

    def increment_usage(self, amount: int) -> int:
        """增加使用量"""
        new_value = min(self.quota_used + amount, self.quota_limit)
        self.quota_used = new_value
        return new_value

    def reset_usage(self) -> None:
        """重置使用量"""
        self.quota_used = 0
        self.last_alert_level = None
        self.last_alert_at = None

    @classmethod
    def create_for_period(
        cls,
        resource_type: QuotaResourceType,
        period_type: QuotaPeriodType,
        quota_limit: int,
        start_date: date,
        enterprise_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> "TenantQuota":
        """为指定周期创建配额"""
        # 计算周期结束日期
        if period_type == QuotaPeriodType.DAILY:
            end_date = start_date
        elif period_type == QuotaPeriodType.MONTHLY:
            # 月末
            if start_date.month == 12:
                end_date = date(start_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(start_date.year, start_date.month + 1, 1) - timedelta(days=1)
        elif period_type == QuotaPeriodType.YEARLY:
            # 年末
            end_date = date(start_date.year, 12, 31)
        else:  # TOTAL
            # 10年后
            end_date = date(start_date.year + 10, 12, 31)

        return cls(
            enterprise_id=enterprise_id,
            user_id=user_id,
            resource_type=resource_type,
            period_type=period_type,
            quota_limit=quota_limit,
            period_start=start_date,
            period_end=end_date,
            **kwargs
        )


class QuotaUsage(BaseModel):
    """配额使用记录模型

    记录每次配额使用的详细信息，用于统计和审计
    """

    __tablename__ = "quota_usage"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="记录ID"
    )

    # 配额关联
    quota_id = Column(
        BIGINT,
        ForeignKey("tenant_quotas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="配额ID"
    )

    # 使用信息
    amount = Column(
        Integer,
        nullable=False,
        comment="使用量"
    )
    operation = Column(
        VARCHAR(100),
        nullable=True,
        comment="操作类型（如：chat, generation, api_call）"
    )

    # 关联资源
    resource_id = Column(
        VARCHAR(100),
        nullable=True,
        comment="关联资源ID（如：conversation_id, message_id）"
    )
    resource_type = Column(
        VARCHAR(50),
        nullable=True,
        comment="关联资源类型"
    )

    # 使用详情
    usage_metadata = Column(
        TEXT,
        nullable=True,
        comment="元数据（JSON格式）"
    )

    # 使用时间
    used_at = Column(
        TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        comment="使用时间"
    )

    # 关系
    quota = relationship(
        "TenantQuota",
        foreign_keys=[quota_id],
        back_populates="usage_records"
    )

    # 索引定义
    __table_args__ = (
        Index("idx_quota_id", "quota_id"),
        Index("idx_operation", "operation"),
        Index("idx_used_at", "used_at"),
        Index("idx_resource", "resource_type", "resource_id"),
    )

    def __repr__(self) -> str:
        return f"<QuotaUsage(id={self.id}, quota_id={self.quota_id}, amount={self.amount})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "quota_id": self.quota_id,
            "amount": self.amount,
            "operation": self.operation,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "metadata": self.usage_metadata,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
