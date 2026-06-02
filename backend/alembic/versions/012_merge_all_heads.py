"""Merge all divergent heads into a single migration history

Revision ID: 012_merge_all_heads
Revises: 011_add_price_and_original_images, 003_add_cultural_tags, 004_add_tenant_isolation, 005_add_quota_system, 006_add_billing_system, 008_optimize_query_indices, 009_add_sla_system
Create Date: 2026-06-02 00:00:00.000000
"""

revision = "012_merge_all_heads"
down_revision = (
    "011_add_price_and_original_images",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This merge revision has no DDL — all schema changes are in the merged heads.
    # Its only purpose is to give Alembic a single linear history.
    pass


def downgrade() -> None:
    pass