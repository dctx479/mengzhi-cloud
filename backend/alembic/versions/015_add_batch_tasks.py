"""add batch_tasks table

Revision ID: 015_add_batch_tasks
Revises: 014_rename_duplicate_indexes
Create Date: 2026-06-14 12:00:00.000000

背景:
    批量内容生成功能（Batch Content Generation）需要持久化任务的配置快照、
    进度与结果。新增 batch_tasks 表，状态机 pending → running → completed/failed/cancelled。

设计:
    - 通用 SQLAlchemy 类型，兼容 MySQL（生产）与 SQLite（测试 create_all）。
    - 索引名遵循表前缀强约定 idx_batch_tasks_*，避免与其它表索引重名（SQLite 库内作用域）。
"""
from alembic import op
import sqlalchemy as sa


revision = "015_add_batch_tasks"
down_revision = "014_rename_duplicate_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_uuid", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=True),
        sa.Column("template_name", sa.String(length=200), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_uuid", name="uk_batch_task_uuid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_batch_tasks_user"),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
        comment="批量内容生成任务表",
    )

    op.create_index("idx_batch_tasks_user_id", "batch_tasks", ["user_id"])
    op.create_index("idx_batch_tasks_status", "batch_tasks", ["status"])


def downgrade() -> None:
    op.drop_index("idx_batch_tasks_status", table_name="batch_tasks")
    op.drop_index("idx_batch_tasks_user_id", table_name="batch_tasks")
    op.drop_table("batch_tasks")
