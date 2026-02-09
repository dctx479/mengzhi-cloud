"""
添加多租户隔离支持

Revision ID: 004_add_tenant_isolation
Revises: 003_add_rbac
Create Date: 2026-01-22

Changes:
- 在enterprises表添加isolation_mode字段
- 在enterprises表添加database_name字段
- 在enterprises表添加database_created_at字段
- 添加相关索引
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '004_add_tenant_isolation'
down_revision = '003_add_rbac'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    # 添加isolation_mode字段
    op.add_column(
        'enterprises',
        sa.Column(
            'isolation_mode',
            sa.Enum('shared', 'isolated', name='isolationmode'),
            nullable=False,
            server_default='shared',
            comment='数据隔离模式：shared共享/isolated独立'
        )
    )

    # 添加database_name字段
    op.add_column(
        'enterprises',
        sa.Column(
            'database_name',
            sa.VARCHAR(100),
            nullable=True,
            comment='独立数据库名称'
        )
    )

    # 添加database_created_at字段
    op.add_column(
        'enterprises',
        sa.Column(
            'database_created_at',
            sa.TIMESTAMP,
            nullable=True,
            comment='数据库创建时间'
        )
    )

    # 添加索引
    op.create_index(
        'idx_isolation_mode',
        'enterprises',
        ['isolation_mode']
    )

    # 添加唯一约束
    op.create_unique_constraint(
        'uk_database_name',
        'enterprises',
        ['database_name']
    )


def downgrade():
    """降级数据库"""
    # 删除唯一约束
    op.drop_constraint('uk_database_name', 'enterprises', type_='unique')

    # 删除索引
    op.drop_index('idx_isolation_mode', 'enterprises')

    # 删除字段
    op.drop_column('enterprises', 'database_created_at')
    op.drop_column('enterprises', 'database_name')
    op.drop_column('enterprises', 'isolation_mode')
