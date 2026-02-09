"""
角色数据模型 - SQLAlchemy ORM

实现基于角色的访问控制（RBAC）中的角色实体

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, Boolean, DateTime, Text,
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, List

from .base import BaseModel


class Role(BaseModel):
    """角色模型

    角色是权限的集合，用户通过角色获得权限。
    系统预置的角色（is_system=True）不可删除。
    """

    __tablename__ = "roles"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="角色ID，主键自增"
    )

    # 角色信息
    name = Column(
        VARCHAR(50),
        nullable=False,
        unique=True,
        comment="角色名称，如：超级管理员、企业用户"
    )
    code = Column(
        VARCHAR(50),
        nullable=False,
        unique=True,
        index=True,
        comment="角色代码，如：ADMIN、ENTERPRISE、PERSONAL"
    )
    description = Column(
        VARCHAR(200),
        nullable=True,
        comment="角色描述"
    )
    is_system = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否系统角色，系统角色不可删除"
    )

    # 关系
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin"
    )
    users = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
        lazy="dynamic"
    )

    # 索引定义
    __table_args__ = (
        UniqueConstraint("name", name="uk_role_name"),
        UniqueConstraint("code", name="uk_role_code"),
        Index("idx_role_code", "code"),
        Index("idx_role_is_system", "is_system"),
        Index("idx_role_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, code={self.code}, name={self.name})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict_with_permissions(self) -> Dict[str, Any]:
        """转换为字典，包含权限列表"""
        data = self.to_dict()
        data["permissions"] = [perm.to_dict() for perm in self.permissions]
        return data

    def has_permission(self, resource: str, action: str) -> bool:
        """检查角色是否有指定权限

        参数:
            resource: 资源名称，如 product, user
            action: 操作名称，如 create, read, update, delete

        返回:
            bool: 是否有权限
        """
        for permission in self.permissions:
            if permission.resource == resource and permission.action == action:
                return True
        return False
