"""Add RBAC tables

Revision ID: 003_add_rbac
Revises: 002_add_audit_logs
Create Date: 2026-01-17 12:00:00.000000

添加基于角色的访问控制（RBAC）表:
- roles: 角色表
- permissions: 权限表
- role_permissions: 角色-权限关联表
- user_roles: 用户-角色关联表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_add_rbac'
down_revision = '002_add_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 创建RBAC表"""

    # 创建 roles 表
    op.create_table(
        'roles',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('name', sa.VARCHAR(50), nullable=False, comment='角色名称'),
        sa.Column('code', sa.VARCHAR(50), nullable=False, comment='角色代码'),
        sa.Column('description', sa.VARCHAR(200), nullable=True, comment='角色描述'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0', comment='是否系统角色'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uk_role_name'),
        sa.UniqueConstraint('code', name='uk_role_code'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='角色表'
    )

    # 创建 roles 表索引
    op.create_index('idx_role_code', 'roles', ['code'])
    op.create_index('idx_role_is_system', 'roles', ['is_system'])
    op.create_index('idx_role_created_at', 'roles', ['created_at'])

    # 创建 permissions 表
    op.create_table(
        'permissions',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('resource', sa.VARCHAR(50), nullable=False, comment='资源名称'),
        sa.Column('action', sa.VARCHAR(20), nullable=False, comment='操作名称'),
        sa.Column('name', sa.VARCHAR(100), nullable=False, comment='权限显示名称'),
        sa.Column('description', sa.VARCHAR(200), nullable=True, comment='权限描述'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resource', 'action', name='uix_resource_action'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='权限表'
    )

    # 创建 permissions 表索引
    op.create_index('idx_permission_resource', 'permissions', ['resource'])
    op.create_index('idx_permission_action', 'permissions', ['action'])
    op.create_index('idx_permission_created_at', 'permissions', ['created_at'])

    # 创建 role_permissions 关联表
    op.create_table(
        'role_permissions',
        sa.Column('role_id', mysql.BIGINT(unsigned=True), nullable=False, comment='角色ID'),
        sa.Column('permission_id', mysql.BIGINT(unsigned=True), nullable=False, comment='权限ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='分配时间'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
        sa.ForeignKeyConstraint(
            ['role_id'], ['roles.id'],
            name='fk_rp_role_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['permission_id'], ['permissions.id'],
            name='fk_rp_permission_id',
            ondelete='CASCADE'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='角色权限关联表'
    )

    # 创建 role_permissions 索引
    op.create_index('idx_rp_role_id', 'role_permissions', ['role_id'])
    op.create_index('idx_rp_permission_id', 'role_permissions', ['permission_id'])

    # 创建 user_roles 关联表
    op.create_table(
        'user_roles',
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=False, comment='用户ID'),
        sa.Column('role_id', mysql.BIGINT(unsigned=True), nullable=False, comment='角色ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='分配时间'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_ur_user_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['role_id'], ['roles.id'],
            name='fk_ur_role_id',
            ondelete='CASCADE'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='用户角色关联表'
    )

    # 创建 user_roles 索引
    op.create_index('idx_ur_user_id', 'user_roles', ['user_id'])
    op.create_index('idx_ur_role_id', 'user_roles', ['role_id'])


def downgrade() -> None:
    """降级数据库 - 删除RBAC表"""

    # 删除关联表（先删除有外键依赖的表）
    op.drop_table('user_roles')
    op.drop_table('role_permissions')

    # 删除主表
    op.drop_table('permissions')
    op.drop_table('roles')
