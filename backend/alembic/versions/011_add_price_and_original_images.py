"""Add price column and original_image_urls to products

Revision ID: 011_add_price_and_original_images
Revises: 010_add_ai_media_generation
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "011_add_price_and_original_images"
down_revision = "010_add_ai_media_generation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("price", sa.DECIMAL(10, 2), nullable=True, server_default="0", comment="产品价格(元)"))
    op.add_column("products", sa.Column("original_image_urls", sa.JSON(), nullable=True, comment="原始外部图片URL(备份)"))
    op.create_index("ix_products_price", "products", ["price"])

    # Backfill price from specifications JSON for existing records
    op.execute(
        "UPDATE products SET price = CAST(JSON_UNQUOTE(JSON_EXTRACT(specifications, '$.price')) AS DECIMAL(10,2)) "
        "WHERE specifications IS NOT NULL AND JSON_EXTRACT(specifications, '$.price') IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_products_price", table_name="products")
    op.drop_column("products", "original_image_urls")
    op.drop_column("products", "price")
