"""enhance batch_tasks for Phase 2

Revision ID: 016_enhance_batch_tasks
Revises: 015_add_batch_tasks
Create Date: 2026-06-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '016_enhance_batch_tasks'
down_revision = '015_add_batch_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('batch_tasks', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('batch_tasks', sa.Column('last_heartbeat_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('batch_tasks', 'last_heartbeat_at')
    op.drop_column('batch_tasks', 'retry_count')
