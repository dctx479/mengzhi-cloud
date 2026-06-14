"""rename duplicate index names to table-prefixed names

Revision ID: 014_rename_duplicate_indexes
Revises: 5a100c74baa3
Create Date: 2026-06-14 00:00:00.000000

背景:
    旧迁移 (001-011) 使用了通用索引名 (idx_status / idx_user_id / idx_created_at 等),
    同一名称在多张表上重复。MySQL 索引名是「表内作用域」,重复合法,生产库正常;
    但 SQLite (单元测试 create_all) 索引名是「库内作用域」,重复会碰撞导致建表失败。

    模型层已统一改为表前缀命名 (idx_<table>_<suffix>)。本迁移把生产 MySQL 中
    残留的旧通用名重命名为新表前缀名,使库结构与模型定义一致。

设计:
    - **仅 MySQL 执行**: 生产库是 MySQL;SQLite/其它方言直接跳过 (测试走 create_all,不跑迁移)。
    - **information_schema 防御性检查**: 逐条校验「旧名存在 且 新名不存在」才重命名,
      因此对「旧名不存在 / 新名已存在 / 重复执行」都安全幂等 (生产库未必有全部索引)。
    - **不删除任何索引**: 若旧名与新名同时存在 (历史冗余),仅跳过并告警,不做破坏性删除。
"""
from alembic import op
import sqlalchemy as sa


revision = "014_rename_duplicate_indexes"
down_revision = "5a100c74baa3"
branch_labels = None
depends_on = None


# (table_name, old_generic_index_name, new_table_prefixed_index_name)
# 由 app.models 元数据权威导出,共 79 条。
RENAMES = [
    ("ai_conversations", "idx_created_at", "idx_ai_conversations_created_at"),
    ("ai_conversations", "idx_status", "idx_ai_conversations_status"),
    ("ai_conversations", "idx_user_id", "idx_ai_conversations_user_id"),
    ("ai_messages", "idx_created_at", "idx_ai_messages_created_at"),
    ("audit_logs", "idx_created_at", "idx_audit_logs_created_at"),
    ("audit_logs", "idx_resource", "idx_audit_logs_resource"),
    ("audit_logs", "idx_user_id", "idx_audit_logs_user_id"),
    ("billing_plans", "idx_billing_mode", "idx_billing_plans_billing_mode"),
    ("billing_plans", "idx_is_active", "idx_billing_plans_is_active"),
    ("billing_plans", "idx_sort_order", "idx_billing_plans_sort_order"),
    ("billing_records", "idx_billing_mode", "idx_billing_records_billing_mode"),
    ("billing_records", "idx_resource", "idx_billing_records_resource"),
    ("billing_records", "idx_user_id", "idx_billing_records_user_id"),
    ("billing_transactions", "idx_created_at", "idx_billing_transactions_created_at"),
    ("billing_transactions", "idx_enterprise_id", "idx_billing_transactions_enterprise_id"),
    ("billing_transactions", "idx_quota_id", "idx_billing_transactions_quota_id"),
    ("billing_transactions", "idx_status", "idx_billing_transactions_status"),
    ("content_records", "idx_content_type", "idx_content_records_content_type"),
    ("content_records", "idx_created_at", "idx_content_records_created_at"),
    ("content_records", "idx_platform", "idx_content_records_platform"),
    ("content_records", "idx_product_id", "idx_content_records_product_id"),
    ("content_records", "idx_status", "idx_content_records_status"),
    ("content_records", "idx_user_id", "idx_content_records_user_id"),
    ("enterprises", "idx_created_at", "idx_enterprises_created_at"),
    ("enterprises", "idx_name", "idx_enterprises_name"),
    ("generation_templates", "idx_content_type", "idx_generation_templates_content_type"),
    ("generation_templates", "idx_created_by", "idx_generation_templates_created_by"),
    ("generation_templates", "idx_is_active", "idx_generation_templates_is_active"),
    ("generation_templates", "idx_platform", "idx_generation_templates_platform"),
    ("invoices", "idx_status", "idx_invoices_status"),
    ("invoices", "idx_user_id", "idx_invoices_user_id"),
    ("kefu_conversations", "idx_created", "idx_kefu_conversations_created"),
    ("kefu_conversations", "idx_user_status", "idx_kefu_conversations_user_status"),
    ("kefu_escalations", "idx_priority", "idx_kefu_escalations_priority"),
    ("kefu_escalations", "idx_user_status", "idx_kefu_escalations_user_status"),
    ("kefu_tickets", "idx_created", "idx_kefu_tickets_created"),
    ("kefu_tickets", "idx_priority", "idx_kefu_tickets_priority"),
    ("kefu_tickets", "idx_user_status", "idx_kefu_tickets_user_status"),
    ("media", "idx_category", "idx_media_category"),
    ("media", "idx_created_at", "idx_media_created_at"),
    ("media", "idx_deleted_at", "idx_media_deleted_at"),
    ("media", "idx_product_id", "idx_media_product_id"),
    ("media", "idx_user_id", "idx_media_user_id"),
    ("orders", "idx_created_at", "idx_orders_created_at"),
    ("orders", "idx_status", "idx_orders_status"),
    ("orders", "idx_user_id", "idx_orders_user_id"),
    ("payments", "idx_created_at", "idx_payments_created_at"),
    ("payments", "idx_order_id", "idx_payments_order_id"),
    ("payments", "idx_status", "idx_payments_status"),
    ("products", "idx_category", "idx_products_category"),
    ("products", "idx_created_at", "idx_products_created_at"),
    ("products", "idx_created_by", "idx_products_created_by"),
    ("products", "idx_enterprise_id", "idx_products_enterprise_id"),
    ("products", "idx_name", "idx_products_name"),
    ("products", "idx_status", "idx_products_status"),
    ("quota_logs", "idx_created_at", "idx_quota_logs_created_at"),
    ("quota_logs", "idx_order_id", "idx_quota_logs_order_id"),
    ("quota_logs", "idx_status", "idx_quota_logs_status"),
    ("quota_logs", "idx_user_id", "idx_quota_logs_user_id"),
    ("quota_packages", "idx_is_active", "idx_quota_packages_is_active"),
    ("quota_packages", "idx_sort_order", "idx_quota_packages_sort_order"),
    ("quota_usage", "idx_quota_id", "idx_quota_usage_quota_id"),
    ("quota_usage", "idx_resource", "idx_quota_usage_resource"),
    ("reconciliation_differences", "idx_created_at", "idx_reconciliation_differences_created_at"),
    ("reconciliation_differences", "idx_status", "idx_reconciliation_differences_status"),
    ("reconciliation_records", "idx_created_at", "idx_reconciliation_records_created_at"),
    ("reconciliation_records", "idx_status", "idx_reconciliation_records_status"),
    ("tenant_ai_configs", "idx_is_active", "idx_tenant_ai_configs_is_active"),
    ("tenant_ai_configs", "idx_priority", "idx_tenant_ai_configs_priority"),
    ("tenant_quotas", "idx_enterprise_id", "idx_tenant_quotas_enterprise_id"),
    ("tenant_quotas", "idx_is_active", "idx_tenant_quotas_is_active"),
    ("tenant_quotas", "idx_period_end", "idx_tenant_quotas_period_end"),
    ("tenant_quotas", "idx_user_id", "idx_tenant_quotas_user_id"),
    ("user_quotas", "idx_period_end", "idx_user_quotas_period_end"),
    ("user_quotas", "idx_user_id", "idx_user_quotas_user_id"),
    ("users", "idx_created_at", "idx_users_created_at"),
    ("users", "idx_deleted_at", "idx_users_deleted_at"),
    ("users", "idx_enterprise_id", "idx_users_enterprise_id"),
    ("users", "idx_status", "idx_users_status"),
]


def _index_exists(bind, table: str, index_name: str) -> bool:
    """检查当前库 (DATABASE()) 中某表是否存在指定索引名"""
    count = bind.execute(
        sa.text(
            "SELECT COUNT(1) FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = :t AND index_name = :i"
        ),
        {"t": table, "i": index_name},
    ).scalar()
    return (count or 0) > 0


def _rename_indexes(pairs) -> None:
    """逐条防御性重命名;仅在「源名存在 且 目标名不存在」时执行"""
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        # 生产库为 MySQL;SQLite/其它方言不跑迁移 (单元测试走 create_all)
        return

    renamed = 0
    skipped = 0
    for table, src, dst in pairs:
        if _index_exists(bind, table, src) and not _index_exists(bind, table, dst):
            op.execute(f"ALTER TABLE `{table}` RENAME INDEX `{src}` TO `{dst}`")
            renamed += 1
        else:
            # 源不存在 / 目标已存在 → 跳过 (幂等;不做破坏性删除)
            skipped += 1
    print(f"[014_rename_duplicate_indexes] renamed={renamed} skipped={skipped} total={len(pairs)}")


def upgrade() -> None:
    _rename_indexes(RENAMES)


def downgrade() -> None:
    # 反向: 新表前缀名 → 旧通用名 (MySQL 索引名表内作用域,通用名跨表重复合法)
    _rename_indexes([(table, dst, src) for table, src, dst in RENAMES])
