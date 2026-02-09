"""
添加审计日志before_data和after_data字段

Revision ID: 007
Revises: 004
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_audit_logs_data_fields'
down_revision = '004_add_multi_tenant_ai_support'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""

    # 添加before_data和after_data字段到audit_logs表
    op.add_column(
        'audit_logs',
        sa.Column('before_data', sa.Text, nullable=True, comment='操作前数据（JSON格式）')
    )

    op.add_column(
        'audit_logs',
        sa.Column('after_data', sa.Text, nullable=True, comment='操作后数据（JSON格式）')
    )

    print("✓ 审计日志表字段添加成功")


def downgrade():
    """降级数据库"""

    # 删除before_data和after_data字段
    op.drop_column('audit_logs', 'after_data')
    op.drop_column('audit_logs', 'before_data')

    print("✓ 审计日志表字段已删除")
