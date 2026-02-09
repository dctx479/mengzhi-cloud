"""Add quota management system

Revision ID: 005_add_quota_system
Revises: 004_add_multi_tenant_ai_support
Create Date: 2026-01-22 14:00:00.000000

添加配额管理系统:
- tenant_quotas: 租户配额表
- quota_usage: 配额使用记录表
- 创建相关索引和约束
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '005_add_quota_system'
down_revision = '004_add_multi_tenant_ai_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 添加配额管理系统"""

    # 创建 tenant_quotas 表
    op.create_table(
        'tenant_quotas',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('enterprise_id', mysql.BIGINT(unsigned=True), nullable=True, comment='企业ID（企业用户）'),
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=True, comment='用户ID（个人用户）'),
        sa.Column(
            'resource_type',
            sa.Enum('token', 'message', 'api_call', 'generation', 'storage', name='quota_resource_type'),
            nullable=False,
            comment='资源类型'
        ),
        sa.Column(
            'period_type',
            sa.Enum('daily', 'monthly', 'yearly', 'total', name='quota_period_type'),
            nullable=False,
            comment='周期类型'
        ),
        sa.Column('quota_limit', mysql.BIGINT(), nullable=False, server_default='0', comment='配额限制'),
        sa.Column('quota_used', mysql.BIGINT(), nullable=False, server_default='0', comment='已使用配额'),
        sa.Column('period_start', sa.DATE(), nullable=False, comment='周期开始日期'),
        sa.Column('period_end', sa.DATE(), nullable=False, comment='周期结束日期'),
        sa.Column('warning_threshold', sa.Integer(), nullable=False, server_default='80', comment='预警阈值（百分比）'),
        sa.Column('critical_threshold', sa.Integer(), nullable=False, server_default='90', comment='严重预警阈值（百分比）'),
        sa.Column(
            'last_alert_level',
            sa.Enum('warning', 'critical', 'exhausted', name='quota_alert_level'),
            nullable=True,
            comment='最后预警级别'
        ),
        sa.Column('last_alert_at', sa.DateTime(), nullable=True, comment='最后预警时间'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1', comment='是否启用（1启用，0禁用）'),
        sa.Column('description', sa.VARCHAR(500), nullable=True, comment='配额描述'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['enterprise_id'], ['enterprises.id'],
            name='fk_tq_enterprise_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_tq_user_id',
            ondelete='CASCADE'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='租户配额表'
    )

    # 创建 tenant_quotas 表索引
    op.create_index('idx_enterprise_id', 'tenant_quotas', ['enterprise_id'])
    op.create_index('idx_user_id', 'tenant_quotas', ['user_id'])
    op.create_index('idx_resource_type', 'tenant_quotas', ['resource_type'])
    op.create_index('idx_period_type', 'tenant_quotas', ['period_type'])
    op.create_index('idx_period_end', 'tenant_quotas', ['period_end'])
    op.create_index('idx_is_active', 'tenant_quotas', ['is_active'])

    # 创建唯一约束
    op.create_index(
        'uk_enterprise_quota_period',
        'tenant_quotas',
        ['enterprise_id', 'resource_type', 'period_type', 'period_start'],
        unique=True
    )
    op.create_index(
        'uk_user_quota_period',
        'tenant_quotas',
        ['user_id', 'resource_type', 'period_type', 'period_start'],
        unique=True
    )

    # 创建 quota_usage 表
    op.create_table(
        'quota_usage',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('quota_id', mysql.BIGINT(unsigned=True), nullable=False, comment='配额ID'),
        sa.Column('amount', sa.Integer(), nullable=False, comment='使用量'),
        sa.Column('operation', sa.VARCHAR(100), nullable=True, comment='操作类型'),
        sa.Column('resource_id', sa.VARCHAR(100), nullable=True, comment='关联资源ID'),
        sa.Column('resource_type', sa.VARCHAR(50), nullable=True, comment='关联资源类型'),
        sa.Column('metadata', sa.TEXT(), nullable=True, comment='元数据（JSON格式）'),
        sa.Column('used_at', sa.DateTime(), nullable=False, comment='使用时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(
            ['quota_id'], ['tenant_quotas.id'],
            name='fk_qu_quota_id',
            ondelete='CASCADE'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='配额使用记录表'
    )

    # 创建 quota_usage 表索引
    op.create_index('idx_quota_id', 'quota_usage', ['quota_id'])
    op.create_index('idx_operation', 'quota_usage', ['operation'])
    op.create_index('idx_used_at', 'quota_usage', ['used_at'])
    op.create_index('idx_resource', 'quota_usage', ['resource_type', 'resource_id'])


def downgrade() -> None:
    """降级数据库 - 移除配额管理系统"""

    # 删除 quota_usage 表索引
    op.drop_index('idx_resource', table_name='quota_usage')
    op.drop_index('idx_used_at', table_name='quota_usage')
    op.drop_index('idx_operation', table_name='quota_usage')
    op.drop_index('idx_quota_id', table_name='quota_usage')

    # 删除 quota_usage 表
    op.drop_table('quota_usage')

    # 删除 tenant_quotas 表索引
    op.drop_index('uk_user_quota_period', table_name='tenant_quotas')
    op.drop_index('uk_enterprise_quota_period', table_name='tenant_quotas')
    op.drop_index('idx_is_active', table_name='tenant_quotas')
    op.drop_index('idx_period_end', table_name='tenant_quotas')
    op.drop_index('idx_period_type', table_name='tenant_quotas')
    op.drop_index('idx_resource_type', table_name='tenant_quotas')
    op.drop_index('idx_user_id', table_name='tenant_quotas')
    op.drop_index('idx_enterprise_id', table_name='tenant_quotas')

    # 删除 tenant_quotas 表
    op.drop_table('tenant_quotas')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS quota_alert_level")
    op.execute("DROP TYPE IF EXISTS quota_period_type")
    op.execute("DROP TYPE IF EXISTS quota_resource_type")
