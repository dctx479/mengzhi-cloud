"""Add AI media generation tables

Revision ID: 010_add_ai_media_generation
Revises: 005_add_failover_support
Create Date: 2026-05-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "010_add_ai_media_generation"
down_revision = "005_add_failover_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 添加AI媒体生成表"""

    op.create_table(
        "media_providers",
        sa.Column("id", mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True, comment="服务商ID"),
        sa.Column("provider_uuid", sa.VARCHAR(36), nullable=False, comment="服务商UUID"),
        sa.Column("provider_code", sa.VARCHAR(50), nullable=False, comment="服务商代码"),
        sa.Column("provider_name", sa.VARCHAR(100), nullable=False, comment="服务商名称"),
        sa.Column(
            "provider_type", sa.Enum("image", "video", name="mediaprovidertype"), nullable=False, comment="服务商类型"
        ),
        sa.Column("api_key_encrypted", sa.TEXT(), nullable=False, comment="加密的API密钥"),
        sa.Column("app_id", sa.VARCHAR(100), nullable=True, comment="应用ID"),
        sa.Column("api_endpoint", sa.VARCHAR(500), nullable=True, comment="API地址"),
        sa.Column("default_model", sa.VARCHAR(100), nullable=True, comment="默认模型"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1"), comment="是否启用"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("0"), comment="是否主服务商"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0", comment="优先级"),
        sa.Column("cost_per_unit", sa.Float(), nullable=False, server_default="0", comment="单次生成成本"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="60", comment="每分钟限流"),
        sa.Column("config", sa.JSON(), nullable=True, comment="扩展配置"),
        sa.Column("health_status", sa.VARCHAR(20), nullable=False, server_default="healthy", comment="健康状态"),
        sa.Column("last_check_time", sa.DateTime(), nullable=True, comment="最后健康检查时间"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0", comment="连续错误计数"),
        sa.Column("last_error_message", sa.TEXT(), nullable=True, comment="最后错误信息"),
        sa.Column("last_error_time", sa.DateTime(), nullable=True, comment="最后错误时间"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_uuid"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="AI媒体生成服务商配置表",
    )
    op.create_index("ix_media_providers_provider_uuid", "media_providers", ["provider_uuid"])
    op.create_index("idx_media_provider_code", "media_providers", ["provider_code"])
    op.create_index("idx_media_provider_type_active", "media_providers", ["provider_type", "is_active", "priority"])
    op.create_index("idx_media_provider_primary", "media_providers", ["provider_type", "is_primary", "is_active"])
    op.create_index("ix_media_providers_provider_type", "media_providers", ["provider_type"])

    op.create_table(
        "media_generation_tasks",
        sa.Column("id", mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True, comment="任务ID"),
        sa.Column("task_uuid", sa.VARCHAR(36), nullable=False, comment="任务UUID"),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False, comment="用户ID"),
        sa.Column("enterprise_id", mysql.BIGINT(unsigned=True), nullable=True, comment="企业ID"),
        sa.Column("provider_id", mysql.BIGINT(unsigned=True), nullable=True, comment="服务商ID"),
        sa.Column(
            "media_type",
            sa.Enum("image", "video", name="mediaprovidertype", create_constraint=False),
            nullable=False,
            comment="媒体类型",
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "succeeded", "failed", "canceled", name="mediataskstatus"),
            nullable=False,
            comment="任务状态",
        ),
        sa.Column("prompt", sa.TEXT(), nullable=False, comment="生成提示词"),
        sa.Column("negative_prompt", sa.TEXT(), nullable=True, comment="反向提示词"),
        sa.Column("model", sa.VARCHAR(100), nullable=True, comment="模型名称"),
        sa.Column("width", sa.Integer(), nullable=True, comment="宽度"),
        sa.Column("height", sa.Integer(), nullable=True, comment="高度"),
        sa.Column("duration", sa.Integer(), nullable=True, comment="视频时长秒"),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="1", comment="结果数量"),
        sa.Column("provider_task_id", sa.VARCHAR(255), nullable=True, comment="第三方任务ID"),
        sa.Column("request_params", sa.JSON(), nullable=True, comment="请求参数"),
        sa.Column("error_message", sa.TEXT(), nullable=True, comment="错误信息"),
        sa.Column("cost_amount", sa.Float(), nullable=False, server_default="0", comment="成本金额"),
        sa.Column("started_at", sa.DateTime(), nullable=True, comment="开始时间"),
        sa.Column("completed_at", sa.DateTime(), nullable=True, comment="完成时间"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间"),
        sa.ForeignKeyConstraint(["enterprise_id"], ["enterprises.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["media_providers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_uuid"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="AI媒体生成任务表",
    )
    op.create_index("ix_media_generation_tasks_task_uuid", "media_generation_tasks", ["task_uuid"])
    op.create_index("ix_media_generation_tasks_user_id", "media_generation_tasks", ["user_id"])
    op.create_index("ix_media_generation_tasks_enterprise_id", "media_generation_tasks", ["enterprise_id"])
    op.create_index("ix_media_generation_tasks_provider_id", "media_generation_tasks", ["provider_id"])
    op.create_index("ix_media_generation_tasks_media_type", "media_generation_tasks", ["media_type"])
    op.create_index("ix_media_generation_tasks_status", "media_generation_tasks", ["status"])
    op.create_index("ix_media_generation_tasks_provider_task_id", "media_generation_tasks", ["provider_task_id"])
    op.create_index("idx_media_task_user_status", "media_generation_tasks", ["user_id", "status", "created_at"])
    op.create_index(
        "idx_media_task_enterprise_status", "media_generation_tasks", ["enterprise_id", "status", "created_at"]
    )
    op.create_index("idx_media_task_provider_status", "media_generation_tasks", ["provider_id", "status"])
    op.create_index("idx_media_task_type_status", "media_generation_tasks", ["media_type", "status"])

    op.create_table(
        "media_generation_results",
        sa.Column("id", mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True, comment="结果ID"),
        sa.Column("result_uuid", sa.VARCHAR(36), nullable=False, comment="结果UUID"),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=False, comment="任务ID"),
        sa.Column("media_id", mysql.BIGINT(unsigned=True), nullable=True, comment="媒体素材ID"),
        sa.Column("file_url", sa.VARCHAR(1000), nullable=False, comment="文件URL"),
        sa.Column("thumbnail_url", sa.VARCHAR(1000), nullable=True, comment="缩略图URL"),
        sa.Column("file_size", mysql.BIGINT(unsigned=True), nullable=True, comment="文件大小"),
        sa.Column("width", sa.Integer(), nullable=True, comment="宽度"),
        sa.Column("height", sa.Integer(), nullable=True, comment="高度"),
        sa.Column("duration", sa.Integer(), nullable=True, comment="视频时长秒"),
        sa.Column("metadata_json", sa.JSON(), nullable=True, comment="结果元数据"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间"),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["media_generation_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("result_uuid"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="AI媒体生成结果表",
    )
    op.create_index("ix_media_generation_results_result_uuid", "media_generation_results", ["result_uuid"])
    op.create_index("ix_media_generation_results_task_id", "media_generation_results", ["task_id"])
    op.create_index("ix_media_generation_results_media_id", "media_generation_results", ["media_id"])

    op.create_table(
        "media_generation_costs",
        sa.Column("id", mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True, comment="成本ID"),
        sa.Column("task_id", mysql.BIGINT(unsigned=True), nullable=True, comment="任务ID"),
        sa.Column("provider_id", mysql.BIGINT(unsigned=True), nullable=True, comment="服务商ID"),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=True, comment="用户ID"),
        sa.Column("enterprise_id", mysql.BIGINT(unsigned=True), nullable=True, comment="企业ID"),
        sa.Column(
            "media_type",
            sa.Enum("image", "video", name="mediaprovidertype", create_constraint=False),
            nullable=False,
            comment="媒体类型",
        ),
        sa.Column("unit_count", sa.Integer(), nullable=False, server_default="1", comment="计费单位数"),
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0", comment="单价"),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0", comment="总金额"),
        sa.Column("billing_date", sa.DateTime(), nullable=False, comment="计费时间"),
        sa.Column("created_at", sa.DateTime(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间"),
        sa.ForeignKeyConstraint(["enterprise_id"], ["enterprises.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["media_providers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["media_generation_tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        comment="AI媒体生成成本表",
    )
    op.create_index("ix_media_generation_costs_task_id", "media_generation_costs", ["task_id"])
    op.create_index("ix_media_generation_costs_provider_id", "media_generation_costs", ["provider_id"])
    op.create_index("ix_media_generation_costs_user_id", "media_generation_costs", ["user_id"])
    op.create_index("ix_media_generation_costs_enterprise_id", "media_generation_costs", ["enterprise_id"])
    op.create_index("ix_media_generation_costs_media_type", "media_generation_costs", ["media_type"])
    op.create_index("ix_media_generation_costs_billing_date", "media_generation_costs", ["billing_date"])


def downgrade() -> None:
    """降级数据库 - 删除AI媒体生成表"""

    op.drop_table("media_generation_costs")
    op.drop_table("media_generation_results")
    op.drop_table("media_generation_tasks")
    op.drop_table("media_providers")
    # PostgreSQL 需要显式删除自定义 Enum 类型
    sa.Enum(name="mediaprovidertype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mediataskstatus").drop(op.get_bind(), checkfirst=True)
