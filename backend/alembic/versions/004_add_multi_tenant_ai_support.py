"""Add multi-tenant AI support

Revision ID: 004_add_multi_tenant_ai_support
Revises: 003_add_rbac
Create Date: 2026-01-22 10:00:00.000000

添加多租户AI支持:
- tenant_ai_configs: 租户AI配置表
- users: 扩展is_admin字段
- 创建相关索引
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '004_add_multi_tenant_ai_support'
down_revision = '003_add_rbac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 添加多租户AI支持"""

    # 创建 tenant_ai_configs 表
    op.create_table(
        'tenant_ai_configs',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('enterprise_id', mysql.BIGINT(unsigned=True), nullable=False, comment='所属企业ID'),
        sa.Column('provider', sa.VARCHAR(50), nullable=False, comment='AI服务商: deepseek, openai, qwen'),
        sa.Column('api_key_encrypted', sa.TEXT(), nullable=False, comment='加密的API密钥'),
        sa.Column('base_url', sa.VARCHAR(255), nullable=True, comment='自定义API地址'),
        sa.Column('default_model', sa.VARCHAR(100), nullable=True, comment='默认模型'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['enterprise_id'], ['enterprises.id'],
            name='fk_tac_enterprise_id',
            ondelete='CASCADE'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='租户AI配置表'
    )

    # 创建 tenant_ai_configs 表索引
    op.create_index('idx_enterprise_provider', 'tenant_ai_configs', ['enterprise_id', 'provider'], unique=True)
    op.create_index('idx_is_active', 'tenant_ai_configs', ['is_active'])

    # 扩展 users 表 - 添加 is_admin 字段
    op.add_column(
        'users',
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0', comment='是否为系统管理员')
    )

    # 创建 users 表 is_admin 索引
    op.create_index('idx_is_admin', 'users', ['is_admin'])


def downgrade() -> None:
    """降级数据库 - 移除多租户AI支持"""

    # 删除 users 表索引
    op.drop_index('idx_is_admin', table_name='users')

    # 删除 users 表字段
    op.drop_column('users', 'is_admin')

    # 删除 tenant_ai_configs 表索引
    op.drop_index('idx_is_active', table_name='tenant_ai_configs')
    op.drop_index('idx_enterprise_provider', table_name='tenant_ai_configs')

    # 删除 tenant_ai_configs 表
    op.drop_table('tenant_ai_configs')
