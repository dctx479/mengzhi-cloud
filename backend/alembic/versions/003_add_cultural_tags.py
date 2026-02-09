"""Add cultural tags system

Revision ID: 003_add_cultural_tags
Revises: 002_add_audit_logs
Create Date: 2026-01-17 14:00:00.000000

文化标签管理系统迁移:
- 创建 cultural_tags 表
- 创建 product_tags 关联表
- 添加索引和约束
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '003_add_cultural_tags'
down_revision = '002_add_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 创建文化标签表"""

    # 创建 cultural_tags 表
    op.create_table(
        'cultural_tags',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('name', sa.VARCHAR(50), nullable=False),
        sa.Column('category', sa.VARCHAR(30), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=True),
        sa.Column('keywords', sa.VARCHAR(200), nullable=True),
        sa.Column('parent_id', mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column('usage_count', mysql.INTEGER(unsigned=True), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['cultural_tags.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('name', name='uk_cultural_tag_name'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='文化标签表'
    )

    # 创建 cultural_tags 表索引
    op.create_index('idx_cultural_tag_name', 'cultural_tags', ['name'])
    op.create_index('idx_cultural_tag_category', 'cultural_tags', ['category'])
    op.create_index('idx_cultural_tag_parent_id', 'cultural_tags', ['parent_id'])
    op.create_index('idx_cultural_tag_is_active', 'cultural_tags', ['is_active'])
    op.create_index('idx_cultural_tag_usage_count', 'cultural_tags', ['usage_count'])
    op.create_index('idx_cultural_tag_created_at', 'cultural_tags', ['created_at'])

    # 创建 product_tags 关联表（多对多）
    op.create_table(
        'product_tags',
        sa.Column('product_id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('tag_id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('product_id', 'tag_id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['cultural_tags.id'], ondelete='CASCADE'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='产品-标签关联表'
    )

    # 创建 product_tags 表索引
    op.create_index('idx_product_tags_product_id', 'product_tags', ['product_id'])
    op.create_index('idx_product_tags_tag_id', 'product_tags', ['tag_id'])


def downgrade() -> None:
    """降级数据库 - 删除文化标签表"""

    # 删除 product_tags 表
    op.drop_index('idx_product_tags_tag_id', table_name='product_tags')
    op.drop_index('idx_product_tags_product_id', table_name='product_tags')
    op.drop_table('product_tags')

    # 删除 cultural_tags 表
    op.drop_index('idx_cultural_tag_created_at', table_name='cultural_tags')
    op.drop_index('idx_cultural_tag_usage_count', table_name='cultural_tags')
    op.drop_index('idx_cultural_tag_is_active', table_name='cultural_tags')
    op.drop_index('idx_cultural_tag_parent_id', table_name='cultural_tags')
    op.drop_index('idx_cultural_tag_category', table_name='cultural_tags')
    op.drop_index('idx_cultural_tag_name', table_name='cultural_tags')
    op.drop_table('cultural_tags')
