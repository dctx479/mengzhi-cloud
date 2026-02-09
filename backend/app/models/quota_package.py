"""
配额套餐数据模型 - SQLAlchemy ORM

版本: 1.0
创建日期: 2026-01-23
"""

from sqlalchemy import (
    Column, BIGINT, String, Integer, DECIMAL, Boolean, Text,
    Enum, TIMESTAMP, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional
import enum

from .base import BaseModel


class PackageType(enum.Enum):
    """套餐类型枚举"""
    BASIC = "basic"  # 基础版
    STANDARD = "standard"  # 标准版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"  # 企业版


class PackagePeriod(enum.Enum):
    """套餐周期枚举"""
    MONTHLY = "monthly"  # 月付
    QUARTERLY = "quarterly"  # 季付
    YEARLY = "yearly"  # 年付
    LIFETIME = "lifetime"  # 终身


class QuotaPackage(BaseModel):
    """配额套餐模型

    定义可购买的配额套餐,包括:
    - 套餐基本信息(名称、类型、价格)
    - 配额内容(对话、生成、Token、存储)
    - 有效期和状态
    """

    __tablename__ = "quota_packages"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="套餐ID"
    )

    # 套餐基本信息
    name = Column(
        String(100),
        nullable=False,
        comment="套餐名称"
    )

    package_type = Column(
        Enum(PackageType),
        nullable=False,
        default=PackageType.BASIC,
        index=True,
        comment="套餐类型"
    )

    period = Column(
        Enum(PackagePeriod),
        nullable=False,
        default=PackagePeriod.MONTHLY,
        comment="套餐周期"
    )

    # 价格信息
    price = Column(
        DECIMAL(10, 2),
        nullable=False,
        comment="套餐价格(元)"
    )

    original_price = Column(
        DECIMAL(10, 2),
        nullable=True,
        comment="原价(用于显示折扣)"
    )

    # 配额内容
    chat_quota = Column(
        Integer,
        nullable=False,
        default=0,
        comment="对话次数配额"
    )

    generation_quota = Column(
        Integer,
        nullable=False,
        default=0,
        comment="内容生成次数配额"
    )

    token_quota = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Token配额"
    )

    storage_quota_mb = Column(
        Integer,
        nullable=False,
        default=0,
        comment="存储空间配额(MB)"
    )

    # 有效期(天数)
    validity_days = Column(
        Integer,
        nullable=False,
        default=30,
        comment="有效期(天)"
    )

    # 套餐描述
    description = Column(
        Text,
        nullable=True,
        comment="套餐描述"
    )

    features = Column(
        Text,
        nullable=True,
        comment="套餐特性(JSON格式)"
    )

    # 状态
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否启用"
    )

    is_recommended = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否推荐"
    )

    # 排序
    sort_order = Column(
        Integer,
        nullable=False,
        default=0,
        comment="排序顺序"
    )

    # 关系
    orders = relationship(
        "Order",
        back_populates="package",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_package_type", "package_type"),
        Index("idx_is_active", "is_active"),
        Index("idx_sort_order", "sort_order"),
    )

    def __repr__(self) -> str:
        return f"<QuotaPackage(id={self.id}, name={self.name}, type={self.package_type.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "package_type": self.package_type.value if self.package_type else None,
            "period": self.period.value if self.period else None,
            "price": float(self.price) if self.price else 0,
            "original_price": float(self.original_price) if self.original_price else None,
            "quotas": {
                "chat": self.chat_quota,
                "generation": self.generation_quota,
                "token": self.token_quota,
                "storage_mb": self.storage_quota_mb,
            },
            "validity_days": self.validity_days,
            "description": self.description,
            "features": self.features,
            "is_active": self.is_active,
            "is_recommended": self.is_recommended,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_discount_percentage(self) -> Optional[int]:
        """计算折扣百分比"""
        if self.original_price and self.original_price > self.price:
            discount = (1 - float(self.price) / float(self.original_price)) * 100
            return round(discount)
        return None

    def is_available(self) -> bool:
        """检查套餐是否可购买"""
        return self.is_active
