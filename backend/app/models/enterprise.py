"""
企业数据模型 - SQLAlchemy ORM

包含：
- 企业基本信息
- 企业认证
- 订阅套餐
- 企业统计

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Enum, TIMESTAMP, Index,
    UniqueConstraint, Text, TEXT, Integer
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any
import enum

from .base import BaseModel, generate_uuid


class EnterpriseScale(enum.Enum):
    """企业规模枚举"""
    MICRO = "micro"  # 微型
    SMALL = "small"  # 小型
    MEDIUM = "medium"  # 中型
    LARGE = "large"  # 大型


class VerifyStatus(enum.Enum):
    """认证状态枚举"""
    PENDING = "pending"  # 待审核
    VERIFIED = "verified"  # 已认证
    REJECTED = "rejected"  # 已拒绝


class PlanType(enum.Enum):
    """套餐类型枚举"""
    FREE = "free"  # 免费版
    BASIC = "basic"  # 基础版
    PRO = "pro"  # 专业版
    ENTERPRISE = "enterprise"  # 企业版


class IsolationMode(enum.Enum):
    """数据隔离模式枚举"""
    SHARED = "shared"  # 共享数据库
    ISOLATED = "isolated"  # 独立数据库


class Enterprise(BaseModel):
    """企业模型

    企业可以拥有多个用户，其中一个或多个为企业管理员。
    企业可以创建和管理产品，并订阅不同的套餐。
    """

    __tablename__ = "enterprises"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="企业ID"
    )

    # UUID标识
    enterprise_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="企业UUID"
    )

    # 基本信息
    name = Column(
        VARCHAR(200),
        nullable=False,
        index=True,
        comment="企业名称"
    )
    short_name = Column(
        VARCHAR(100),
        nullable=True,
        comment="企业简称"
    )
    license_no = Column(
        VARCHAR(50),
        nullable=False,
        unique=True,
        comment="营业执照号"
    )
    license_image_url = Column(
        VARCHAR(500),
        nullable=True,
        comment="营业执照图片URL"
    )

    # 联系信息
    contact_name = Column(
        VARCHAR(50),
        nullable=True,
        comment="联系人姓名"
    )
    contact_phone = Column(
        VARCHAR(20),
        nullable=True,
        comment="联系人电话"
    )
    contact_email = Column(
        VARCHAR(100),
        nullable=True,
        comment="联系人邮箱"
    )

    # 地址信息
    province = Column(
        VARCHAR(50),
        nullable=True,
        comment="省份"
    )
    city = Column(
        VARCHAR(50),
        nullable=True,
        comment="城市"
    )
    district = Column(
        VARCHAR(50),
        nullable=True,
        comment="区县"
    )
    address = Column(
        VARCHAR(500),
        nullable=True,
        comment="详细地址"
    )

    # 企业详情
    industry = Column(
        VARCHAR(100),
        nullable=True,
        comment="所属行业"
    )
    scale = Column(
        Enum(EnterpriseScale),
        default=EnterpriseScale.SMALL,
        comment="企业规模"
    )
    description = Column(
        TEXT,
        nullable=True,
        comment="企业简介"
    )
    logo_url = Column(
        VARCHAR(500),
        nullable=True,
        comment="企业Logo URL"
    )
    website = Column(
        VARCHAR(200),
        nullable=True,
        comment="企业官网"
    )

    # 认证状态
    verify_status = Column(
        Enum(VerifyStatus),
        nullable=False,
        default=VerifyStatus.PENDING,
        index=True,
        comment="认证状态"
    )
    verified_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="认证通过时间"
    )
    reject_reason = Column(
        VARCHAR(500),
        nullable=True,
        comment="拒绝原因"
    )

    # 套餐信息
    plan_type = Column(
        Enum(PlanType),
        nullable=False,
        default=PlanType.FREE,
        index=True,
        comment="套餐类型"
    )
    plan_expires_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="套餐到期时间"
    )

    # 数据隔离配置
    isolation_mode = Column(
        Enum(IsolationMode),
        nullable=False,
        default=IsolationMode.SHARED,
        index=True,
        comment="数据隔离模式：shared共享/isolated独立"
    )
    database_name = Column(
        VARCHAR(100),
        nullable=True,
        unique=True,
        comment="独立数据库名称"
    )
    database_created_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="数据库创建时间"
    )

    # 关系
    users = relationship(
        "User",
        foreign_keys="User.enterprise_id",
        back_populates="enterprise"
    )
    products = relationship(
        "Product",
        foreign_keys="Product.enterprise_id",
        back_populates="enterprise"
    )
    ai_configs = relationship(
        "TenantAIConfig",
        back_populates="enterprise",
        cascade="all, delete-orphan"
    )
    quotas = relationship(
        "TenantQuota",
        foreign_keys="TenantQuota.enterprise_id",
        back_populates="enterprise",
        cascade="all, delete-orphan"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("enterprise_uuid", name="uk_enterprise_uuid"),
        UniqueConstraint("license_no", name="uk_license_no"),
        UniqueConstraint("database_name", name="uk_database_name"),
        Index("idx_name", "name"),
        Index("idx_verify_status", "verify_status"),
        Index("idx_plan_type", "plan_type"),
        Index("idx_isolation_mode", "isolation_mode"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Enterprise(id={self.id}, name={self.name}, verify_status={self.verify_status.value})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "enterprise_uuid": self.enterprise_uuid,
            "name": self.name,
            "short_name": self.short_name,
            "license_no": self.license_no,
            "license_image_url": self.license_image_url,
            "contact_name": self.contact_name,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "province": self.province,
            "city": self.city,
            "district": self.district,
            "address": self.address,
            "industry": self.industry,
            "scale": self.scale.value if self.scale else None,
            "description": self.description,
            "logo_url": self.logo_url,
            "website": self.website,
            "verify_status": self.verify_status.value if self.verify_status else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "reject_reason": self.reject_reason,
            "plan_type": self.plan_type.value if self.plan_type else None,
            "plan_expires_at": self.plan_expires_at.isoformat() if self.plan_expires_at else None,
            "isolation_mode": self.isolation_mode.value if self.isolation_mode else None,
            "database_name": self.database_name,
            "database_created_at": self.database_created_at.isoformat() if self.database_created_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_verified(self) -> bool:
        """检查企业是否已认证"""
        return self.verify_status == VerifyStatus.VERIFIED

    def is_plan_active(self) -> bool:
        """检查订阅套餐是否有效"""
        if self.plan_type == PlanType.FREE:
            return True
        if self.plan_expires_at is None:
            return False
        return datetime.utcnow() < self.plan_expires_at

    def get_plan_quota(self) -> Dict[str, int]:
        """获取当前套餐的配额"""
        quotas = {
            PlanType.FREE: {
                "daily_chat_limit": 50,
                "daily_generation_limit": 20,
                "monthly_token_limit": 100000
            },
            PlanType.BASIC: {
                "daily_chat_limit": 200,
                "daily_generation_limit": 100,
                "monthly_token_limit": 1000000
            },
            PlanType.PRO: {
                "daily_chat_limit": 1000,
                "daily_generation_limit": 500,
                "monthly_token_limit": 10000000
            },
            PlanType.ENTERPRISE: {
                "daily_chat_limit": 999999,
                "daily_generation_limit": 999999,
                "monthly_token_limit": 999999999
            }
        }
        return quotas.get(self.plan_type, quotas[PlanType.FREE])

    @classmethod
    def get_by_uuid(cls, enterprise_uuid: str) -> Optional["Enterprise"]:
        """根据UUID获取企业"""
        pass

    @classmethod
    def get_by_license(cls, license_no: str) -> Optional["Enterprise"]:
        """根据营业执照号获取企业"""
        pass

    @classmethod
    def get_verified_enterprises(cls) -> list:
        """获取所有已认证的企业"""
        pass
