"""Add failover support

Revision ID: 005_add_failover_support
Revises: 004_add_multi_tenant_ai_support
Create Date: 2026-01-22 12:00:00.000000

添加故障转移支持:
- tenant_ai_configs: 添加故障转移相关字段
- 创建相关索引
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '005_add_failover_support'
down_revision = '004_add_multi_tenant_ai_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 添加故障转移支持"""

    # 扩展 tenant_ai_configs 表 - 添加故障转移字段
    op.add_column(
        'tenant_ai_configs',
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0', comment='优先级(0-100,数值越大优先级越高)')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('health_status', sa.VARCHAR(20), nullable=False, server_default='healthy', comment='健康状态: healthy, degraded, unhealthy')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('last_check_time', sa.DateTime(), nullable=True, comment='最后健康检查时间')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0', comment='连续错误计数')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('total_requests', mysql.BIGINT(unsigned=True), nullable=False, server_default='0', comment='总请求数')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('failed_requests', mysql.BIGINT(unsigned=True), nullable=False, server_default='0', comment='失败请求数')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('avg_response_time', sa.Float(), nullable=True, comment='平均响应时间(毫秒)')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('last_error_message', sa.TEXT(), nullable=True, comment='最后错误信息')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('last_error_time', sa.DateTime(), nullable=True, comment='最后错误时间')
    )

    op.add_column(
        'tenant_ai_configs',
        sa.Column('circuit_breaker_open_until', sa.DateTime(), nullable=True, comment='熔断器开启截止时间')
    )

    # 创建索引
    op.create_index('idx_health_status', 'tenant_ai_configs', ['health_status'])
    op.create_index('idx_priority', 'tenant_ai_configs', ['priority'])
    op.create_index('idx_enterprise_priority', 'tenant_ai_configs', ['enterprise_id', 'priority', 'health_status'])


def downgrade() -> None:
    """降级数据库 - 移除故障转移支持"""

    # 删除索引
    op.drop_index('idx_enterprise_priority', table_name='tenant_ai_configs')
    op.drop_index('idx_priority', table_name='tenant_ai_configs')
    op.drop_index('idx_health_status', table_name='tenant_ai_configs')

    # 删除字段
    op.drop_column('tenant_ai_configs', 'circuit_breaker_open_until')
    op.drop_column('tenant_ai_configs', 'last_error_time')
    op.drop_column('tenant_ai_configs', 'last_error_message')
    op.drop_column('tenant_ai_configs', 'avg_response_time')
    op.drop_column('tenant_ai_configs', 'failed_requests')
    op.drop_column('tenant_ai_configs', 'total_requests')
    op.drop_column('tenant_ai_configs', 'error_count')
    op.drop_column('tenant_ai_configs', 'last_check_time')
    op.drop_column('tenant_ai_configs', 'health_status')
    op.drop_column('tenant_ai_configs', 'priority')
