"""Add sku column to products table

Revision ID: 013_add_sku
Revises: 012_merge_all_heads
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "013_add_sku"
down_revision = "012_merge_all_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("sku", sa.VARCHAR(50), nullable=True, unique=True, comment="产品SKU编码"))
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_column("products", "sku")