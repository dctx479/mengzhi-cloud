"""
用户数据模型 - SQLAlchemy ORM

包含：
- 用户账户信息
- 认证和安全
- 社交媒体绑定
- 个人资料

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Enum, Integer, TIMESTAMP, Boolean,
    Index, UniqueConstraint, Text, TEXT, ForeignKey
)
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, Dict, Any, List
import enum

from .base import BaseModel, generate_uuid


class UserType(enum.Enum):
    """用户类型枚举"""
    PERSONAL = "personal"  # 个人用户
    ENTERPRISE = "enterprise"  # 企业用户


class UserStatus(enum.Enum):
    """用户状态枚举"""
    ACTIVE = "active"  # 正常
    INACTIVE = "inactive"  # 未激活
    BANNED = "banned"  # 已禁用
    PENDING = "pending"  # 待审核


class UserRole(enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"  # 系统管理员
    ENTERPRISE_ADMIN = "enterprise_admin"  # 企业管理员
    USER = "user"  # 普通用户


class Gender(enum.Enum):
    """性别枚举"""
    UNKNOWN = 0  # 未知
    MALE = 1  # 男
    FEMALE = 2  # 女


class User(BaseModel):
    """用户模型

    用户可以是个人或企业。个人用户可以单独使用系统，
    企业用户属于某个企业并可以管理企业产品。
    """

    __tablename__ = "users"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="用户ID，主键自增"
    )

    # UUID标识
    user_uuid = Column(
        VARCHAR(36),
        nullable=False,
        unique=True,
        index=True,
        default=generate_uuid,
        comment="用户UUID，对外暴露的唯一标识"
    )

    # 账户信息
    username = Column(
        VARCHAR(50),
        nullable=False,
        unique=True,
        index=True,
        comment="用户名，唯一"
    )
    email = Column(
        VARCHAR(100),
        nullable=True,
        unique=True,
        index=True,
        comment="邮箱地址"
    )
    phone = Column(
        VARCHAR(20),
        nullable=True,
        unique=True,
        index=True,
        comment="手机号码"
    )
    password_hash = Column(
        VARCHAR(255),
        nullable=False,
        comment="密码哈希值(bcrypt)"
    )

    # 用户类型与状态
    user_type = Column(
        Enum(UserType),
        nullable=False,
        default=UserType.PERSONAL,
        index=True,
        comment="用户类型：personal个人/enterprise企业"
    )
    status = Column(
        Enum(UserStatus),
        nullable=False,
        default=UserStatus.PENDING,
        index=True,
        comment="账号状态"
    )
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
        comment="用户角色"
    )

    # 企业关联
    enterprise_id = Column(
        BIGINT,
        ForeignKey("enterprises.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属企业ID"
    )

    # 第三方登录
    wechat_openid = Column(
        VARCHAR(100),
        nullable=True,
        unique=True,
        comment="微信OpenID"
    )
    wechat_unionid = Column(
        VARCHAR(100),
        nullable=True,
        unique=True,
        comment="微信UnionID"
    )
    douyin_openid = Column(
        VARCHAR(100),
        nullable=True,
        unique=True,
        comment="抖音OpenID"
    )

    # 用户资料
    nickname = Column(
        VARCHAR(100),
        nullable=True,
        comment="昵称"
    )
    avatar_url = Column(
        VARCHAR(500),
        nullable=True,
        comment="头像URL"
    )
    gender = Column(
        Integer,
        default=0,
        comment="性别：0未知/1男/2女"
    )

    # 个人资料扩展字段
    bio = Column(
        TEXT,
        nullable=True,
        comment="个人简介"
    )
    location = Column(
        VARCHAR(200),
        nullable=True,
        comment="所在地"
    )
    website = Column(
        VARCHAR(500),
        nullable=True,
        comment="个人网站"
    )
    # 安全相关
    login_attempts = Column(
        Integer,
        default=0,
        comment="登录失败次数"
    )
    locked_until = Column(
        TIMESTAMP,
        nullable=True,
        comment="账号锁定截止时间"
    )
    last_login_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="最后登录时间"
    )
    last_login_ip = Column(
        VARCHAR(45),
        nullable=True,
        comment="最后登录IP"
    )
    password_changed_at = Column(
        TIMESTAMP,
        nullable=True,
        comment="密码修改时间"
    )

    # 管理员标志
    is_admin = Column(
        sa.Boolean,
        default=False,
        server_default=sa.text("0"),
        nullable=False,
        comment="是否为系统管理员"
    )

    # 关系
    enterprise = relationship(
        "Enterprise",
        foreign_keys=[enterprise_id],
        back_populates="users"
    )
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    content_records = relationship(
        "ContentRecord",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    quotas = relationship(
        "UserQuota",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    tenant_quotas = relationship(
        "TenantQuota",
        foreign_keys="TenantQuota.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    products = relationship(
        "Product",
        foreign_keys="Product.created_by",
        back_populates="creator"
    )
    roles = relationship(
        "Role",
        secondary="user_roles",
        back_populates="users",
        lazy="selectin"
    )
    media = relationship(
        "Media",
        foreign_keys="Media.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    orders = relationship(
        "Order",
        foreign_keys="Order.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    quota_logs = relationship(
        "QuotaLog",
        foreign_keys="QuotaLog.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("user_uuid", name="uk_user_uuid"),
        UniqueConstraint("username", name="uk_username"),
        UniqueConstraint("email", name="uk_email"),
        UniqueConstraint("phone", name="uk_phone"),
        UniqueConstraint("wechat_openid", name="uk_wechat_openid"),
        UniqueConstraint("douyin_openid", name="uk_douyin_openid"),
        Index("idx_user_type", "user_type"),
        Index("idx_status", "status"),
        Index("idx_enterprise_id", "enterprise_id"),
        Index("idx_is_admin", "is_admin"),
        Index("idx_created_at", "created_at"),
        Index("idx_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        user_type_val = self.user_type.value if hasattr(self.user_type, 'value') else (self.user_type or "unknown")
        return f"<User(id={self.id}, username={self.username}, user_type={user_type_val})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_uuid": self.user_uuid,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "user_type": self.user_type.value if self.user_type else None,
            "status": self.status.value if self.status else None,
            "role": self.role.value if self.role else None,
            "enterprise_id": self.enterprise_id,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url,
            "gender": self.gender,
            "is_admin": self.is_admin,
            "bio": self.bio,
            "location": self.location,
            "website": self.website,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_safe(self) -> Dict[str, Any]:
        """转换为安全的字典（不包含敏感信息）"""
        safe_dict = self.to_dict()
        # 移除敏感字段
        safe_dict.pop("password_hash", None)
        safe_dict.pop("login_attempts", None)
        safe_dict.pop("locked_until", None)
        return safe_dict

    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def is_active(self) -> bool:
        """检查账户是否激活"""
        return self.status == UserStatus.ACTIVE

    def has_permission(self, resource: str, action: str) -> bool:
        """检查用户是否有指定权限

        参数:
            resource: 资源名称，如 product, user
            action: 操作名称，如 create, read, update, delete

        返回:
            bool: 是否有权限
        """
        for role in self.roles:
            if role.has_permission(resource, action):
                return True
        return False

    def get_all_permissions(self) -> List[Dict[str, Any]]:
        """获取用户的所有权限

        返回:
            List[Dict]: 权限列表
        """
        permissions = []
        seen = set()
        for role in self.roles:
            for perm in role.permissions:
                perm_code = f"{perm.resource}:{perm.action}"
                if perm_code not in seen:
                    seen.add(perm_code)
                    permissions.append(perm.to_dict())
        return permissions

    @classmethod
    def authenticate(cls, username: str, password_hash: str) -> Optional["User"]:
        """验证用户认证 - 由Service层调用"""
        # 实现由业务层负责
        pass

    @classmethod
    def get_by_uuid(cls, user_uuid: str) -> Optional["User"]:
        """根据UUID获取用户"""
        pass

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """根据用户名获取用户"""
        pass

    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        """根据邮箱获取用户"""
        pass

    @classmethod
    def get_by_phone(cls, phone: str) -> Optional["User"]:
        """根据手机号获取用户"""
        pass
