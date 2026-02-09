"""
权限数据模型 - SQLAlchemy ORM

实现基于角色的访问控制（RBAC）中的权限实体

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import (
    Column, BIGINT, VARCHAR, DateTime, Text,
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any

from .base import BaseModel


class Permission(BaseModel):
    """权限模型

    权限由资源和操作组成，例如：
    - resource="product", action="create" 表示创建产品权限
    - resource="user", action="read" 表示查看用户权限
    """

    __tablename__ = "permissions"

    # 主键
    id = Column(
        BIGINT,
        primary_key=True,
        autoincrement=True,
        comment="权限ID，主键自增"
    )

    # 权限定义
    resource = Column(
        VARCHAR(50),
        nullable=False,
        index=True,
        comment="资源名称，如：product、user、chat、enterprise"
    )
    action = Column(
        VARCHAR(20),
        nullable=False,
        index=True,
        comment="操作名称，如：create、read、update、delete"
    )
    name = Column(
        VARCHAR(100),
        nullable=False,
        comment="权限显示名称，如：创建产品、查看用户"
    )
    description = Column(
        VARCHAR(200),
        nullable=True,
        comment="权限描述"
    )

    # 关系
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="dynamic"
    )

    # 索引和约束
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uix_resource_action"),
        Index("idx_permission_resource", "resource"),
        Index("idx_permission_action", "action"),
        Index("idx_permission_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, resource={self.resource}, action={self.action})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "resource": self.resource,
            "action": self.action,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_code(self) -> str:
        """获取权限代码（resource:action格式）"""
        return f"{self.resource}:{self.action}"
