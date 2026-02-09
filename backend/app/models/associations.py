"""
关联表定义 - 多对多关系

定义角色-权限和用户-角色的多对多关联表

版本: 1.0
更新日期: 2026-01-17
"""

from sqlalchemy import Table, Column, BIGINT, ForeignKey, DateTime, Index
from datetime import datetime
from sqlalchemy.dialects.mysql import BIGINT as MYSQL_BIGINT

from .base import Base


# 角色-权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column(
        'role_id',
        MYSQL_BIGINT,
        ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
        comment="角色ID"
    ),
    Column(
        'permission_id',
        MYSQL_BIGINT,
        ForeignKey('permissions.id', ondelete='CASCADE'),
        primary_key=True,
        comment="权限ID"
    ),
    Column(
        'created_at',
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="分配时间"
    ),
    Index('idx_rp_role_id', 'role_id'),
    Index('idx_rp_permission_id', 'permission_id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
)


# 用户-角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column(
        'user_id',
        MYSQL_BIGINT,
        ForeignKey('users.id', ondelete='CASCADE'),
        primary_key=True,
        comment="用户ID"
    ),
    Column(
        'role_id',
        MYSQL_BIGINT,
        ForeignKey('roles.id', ondelete='CASCADE'),
        primary_key=True,
        comment="角色ID"
    ),
    Column(
        'created_at',
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="分配时间"
    ),
    Index('idx_ur_user_id', 'user_id'),
    Index('idx_ur_role_id', 'role_id'),
    mysql_charset='utf8mb4',
    mysql_collate='utf8mb4_unicode_ci',
    mysql_engine='InnoDB'
)


__all__ = ["role_permissions", "user_roles"]
