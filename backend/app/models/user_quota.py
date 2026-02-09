"""
用户配额数据模型 - SQLAlchemy ORM

包含：
- 对话配额
- 内容生成配额
- Token配额
- 存储配额
- 配额周期

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, Enum, Integer, DATE, TIMESTAMP, Index,
    UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import date, datetime
from typing import Optional, Dict, Any
import enum

from .base import BaseModel


class QuotaType(enum.Enum):
    """配额类型枚举"""
    DAILY = "daily"  # 每日
    MONTHLY = "monthly"  # 每月
    TOTAL = "total"  # 总计


class UserQuota(BaseModel):
    """用户配额模型

    配额包含：
    - 对话次数限制和使用量
    - 内容生成次数限制和使用量
    - Token限制和使用量
    - 存储空间限制和使用量
    - 配额周期（开始日期和结束日期）
    """

    __tablename__ = "user_quotas"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="配额ID"
    )

    # 关联信息
    user_id = Column(
        BIGINT,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )

    # 配额类型
    quota_type = Column(
        Enum(QuotaType),
        nullable=False,
        default=QuotaType.DAILY,
        index=True,
        comment="配额类型"
    )

    # AI对话配额
    chat_limit = Column(
        Integer,
        default=50,
        comment="对话次数限制"
    )
    chat_used = Column(
        Integer,
        default=0,
        comment="已使用对话次数"
    )

    # 内容生成配额
    generation_limit = Column(
        Integer,
        default=20,
        comment="生成次数限制"
    )
    generation_used = Column(
        Integer,
        default=0,
        comment="已使用生成次数"
    )

    # Token配额
    token_limit = Column(
        Integer,
        default=100000,
        comment="Token限制"
    )
    token_used = Column(
        Integer,
        default=0,
        comment="已使用Token"
    )

    # 存储配额
    storage_limit_mb = Column(
        Integer,
        default=100,
        comment="存储空间限制(MB)"
    )
    storage_used_mb = Column(
        Integer,
        default=0,
        comment="已使用存储(MB)"
    )

    # 配额周期
    period_start = Column(
        DATE,
        nullable=False,
        comment="配额周期开始日期"
    )
    period_end = Column(
        DATE,
        nullable=False,
        comment="配额周期结束日期"
    )

    # 关系
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="quotas"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("user_id", "quota_type", "period_start", name="uk_user_quota_period"),
        Index("idx_user_id", "user_id"),
        Index("idx_quota_type", "quota_type"),
        Index("idx_period_end", "period_end"),
    )

    def __repr__(self) -> str:
        return f"<UserQuota(id={self.id}, user_id={self.user_id}, quota_type={self.quota_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "quota_type": self.quota_type.value if self.quota_type else None,
            "chat": {
                "limit": self.chat_limit,
                "used": self.chat_used,
                "remaining": self.chat_limit - self.chat_used,
            },
            "generation": {
                "limit": self.generation_limit,
                "used": self.generation_used,
                "remaining": self.generation_limit - self.generation_used,
            },
            "token": {
                "limit": self.token_limit,
                "used": self.token_used,
                "remaining": self.token_limit - self.token_used,
            },
            "storage": {
                "limit_mb": self.storage_limit_mb,
                "used_mb": self.storage_used_mb,
                "remaining_mb": self.storage_limit_mb - self.storage_used_mb,
            },
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_chat_usage(self) -> Dict[str, int]:
        """获取对话配额使用情况"""
        return {
            "limit": self.chat_limit,
            "used": self.chat_used,
            "remaining": max(0, self.chat_limit - self.chat_used),
            "percentage": round((self.chat_used / self.chat_limit * 100), 2) if self.chat_limit > 0 else 0,
        }

    def get_generation_usage(self) -> Dict[str, int]:
        """获取生成配额使用情况"""
        return {
            "limit": self.generation_limit,
            "used": self.generation_used,
            "remaining": max(0, self.generation_limit - self.generation_used),
            "percentage": round((self.generation_used / self.generation_limit * 100), 2) if self.generation_limit > 0 else 0,
        }

    def get_token_usage(self) -> Dict[str, int]:
        """获取Token配额使用情况"""
        return {
            "limit": self.token_limit,
            "used": self.token_used,
            "remaining": max(0, self.token_limit - self.token_used),
            "percentage": round((self.token_used / self.token_limit * 100), 2) if self.token_limit > 0 else 0,
        }

    def get_storage_usage(self) -> Dict[str, Any]:
        """获取存储配额使用情况"""
        return {
            "limit_mb": self.storage_limit_mb,
            "used_mb": self.storage_used_mb,
            "remaining_mb": max(0, self.storage_limit_mb - self.storage_used_mb),
            "percentage": round((self.storage_used_mb / self.storage_limit_mb * 100), 2) if self.storage_limit_mb > 0 else 0,
        }

    def can_chat(self) -> bool:
        """检查是否可以进行对话"""
        return self.chat_used < self.chat_limit

    def can_generate(self) -> bool:
        """检查是否可以生成内容"""
        return self.generation_used < self.generation_limit

    def can_use_tokens(self, required_tokens: int = 1) -> bool:
        """检查是否有足够的Token"""
        return self.token_used + required_tokens <= self.token_limit

    def can_use_storage(self, required_mb: int = 1) -> bool:
        """检查是否有足够的存储空间"""
        return self.storage_used_mb + required_mb <= self.storage_limit_mb

    def is_in_period(self) -> bool:
        """检查是否在配额周期内"""
        today = date.today()
        return self.period_start <= today <= self.period_end

    def is_expired(self) -> bool:
        """检查配额是否已过期"""
        today = date.today()
        return today > self.period_end

    def increment_chat_usage(self, count: int = 1) -> int:
        """增加对话使用计数"""
        new_value = min(self.chat_used + count, self.chat_limit)
        self.chat_used = new_value
        return new_value

    def increment_generation_usage(self, count: int = 1) -> int:
        """增加生成使用计数"""
        new_value = min(self.generation_used + count, self.generation_limit)
        self.generation_used = new_value
        return new_value

    def increment_token_usage(self, tokens: int) -> int:
        """增加Token使用计数"""
        new_value = min(self.token_used + tokens, self.token_limit)
        self.token_used = new_value
        return new_value

    def increment_storage_usage(self, mb: int) -> int:
        """增加存储使用计数"""
        new_value = min(self.storage_used_mb + mb, self.storage_limit_mb)
        self.storage_used_mb = new_value
        return new_value

    @classmethod
    def get_user_quota(cls, user_id: int, quota_type: str = "daily") -> Optional["UserQuota"]:
        """获取用户的配额"""
        pass

    @classmethod
    def create_daily_quota(cls, user_id: int, start_date: date) -> "UserQuota":
        """为用户创建每日配额"""
        from datetime import timedelta
        end_date = start_date + timedelta(days=1) - timedelta(seconds=1)
        return cls(
            user_id=user_id,
            quota_type=QuotaType.DAILY,
            period_start=start_date,
            period_end=end_date,
        )

    @classmethod
    def create_monthly_quota(cls, user_id: int, start_date: date) -> "UserQuota":
        """为用户创建月度配额"""
        from dateutil.relativedelta import relativedelta
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        return cls(
            user_id=user_id,
            quota_type=QuotaType.MONTHLY,
            period_start=start_date,
            period_end=end_date,
        )
