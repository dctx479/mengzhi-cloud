"""add_cultural_elements_tables

Revision ID: 5a100c74baa3
Revises: 013_add_sku
Create Date: 2026-06-12 16:23:08.397429

知识图谱数据库迁移:
- 创建 cultural_elements 表（文化元素）
- 创建 product_culture_links 表（产品-文化关联）
- 创建 origin_culture_links 表（产地-文化关联）
- 添加索引优化查询性能

注：原迁移使用无符号 BIGINT，与 products.id 等有符号 BIGINT 外键不兼容；
且 cultural_elements 表可能已由 Base.metadata.create_all 创建。
本迁移改为幂等 + 有符号 BIGINT，外键类型保持一致。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql, postgresql

# revision identifiers, used by Alembic.
revision = '5a100c74baa3'
down_revision = '013_add_sku'
branch_labels = None
depends_on = None


def _table_exists(op, name: str) -> bool:
    bind = op.get_bind()
    return bind.dialect.has_table(bind, name)


def _index_exists(op, table: str, index: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return index in [i['name'] for i in insp.get_indexes(table)]


def upgrade() -> None:
    """升级数据库 - 创建知识图谱表（幂等）"""

    # 创建 cultural_elements 表（文化元素）
    if not _table_exists(op, 'cultural_elements'):
        op.create_table(
            'cultural_elements',
            # 有符号 BIGINT，与 products.id 等主键保持一致，避免 FK 类型不兼容
            sa.Column('id', sa.BIGINT(), nullable=False, autoincrement=True),
            sa.Column('name', sa.VARCHAR(100), nullable=False, unique=True),
            sa.Column('type', sa.VARCHAR(50), nullable=False, comment='文化类型：节日/传说/工艺/饮食/建筑等'),
            sa.Column('story', sa.TEXT(), nullable=False, comment='文化故事或背景描述'),
            sa.Column('origin_region', sa.VARCHAR(100), nullable=True, comment='起源地区'),
            sa.Column('hot_score', sa.INTEGER(), nullable=False, server_default='50', comment='热度分数 0-100'),
            sa.Column('metadata', sa.JSON(), nullable=True, comment='扩展元数据（图片、关键词等）'),
            sa.Column('view_count', sa.INTEGER(), nullable=False, server_default='0', comment='浏览次数'),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name', name='uk_cultural_element_name'),
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci',
            mysql_engine='InnoDB',
            comment='文化元素表'
        )

    # cultural_elements 索引（幂等）
    if not _index_exists(op, 'cultural_elements', 'idx_cultural_elements_type'):
        op.create_index('idx_cultural_elements_type', 'cultural_elements', ['type'])
    if not _index_exists(op, 'cultural_elements', 'idx_cultural_elements_hot_score'):
        op.create_index('idx_cultural_elements_hot_score', 'cultural_elements', ['hot_score'], mysql_length=None)
    if not _index_exists(op, 'cultural_elements', 'idx_cultural_elements_region'):
        op.create_index('idx_cultural_elements_region', 'cultural_elements', ['origin_region'])
    if not _index_exists(op, 'cultural_elements', 'idx_cultural_elements_created_at'):
        op.create_index('idx_cultural_elements_created_at', 'cultural_elements', ['created_at'])

    # 创建 product_culture_links 表（产品-文化关联）
    if not _table_exists(op, 'product_culture_links'):
        op.create_table(
            'product_culture_links',
            # 有符号 BIGINT 与 products.id 兼容
            sa.Column('product_id', sa.BIGINT(), nullable=False),
            sa.Column('culture_id', sa.BIGINT(), nullable=False),
            sa.Column('relevance_score', sa.DECIMAL(3, 2), nullable=False, server_default='0.50', comment='关联度分数 0.00-1.00'),
            sa.Column('link_type', sa.VARCHAR(50), nullable=False, server_default='manual', comment='关联类型：manual/ai/curated'),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('product_id', 'culture_id'),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE', name='fk_product_culture_product'),
            sa.ForeignKeyConstraint(['culture_id'], ['cultural_elements.id'], ondelete='CASCADE', name='fk_product_culture_element'),
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci',
            mysql_engine='InnoDB',
            comment='产品-文化元素关联表'
        )
        op.create_index('idx_product_culture_product', 'product_culture_links', ['product_id'])
        op.create_index('idx_product_culture_culture', 'product_culture_links', ['culture_id'])
        op.create_index('idx_product_culture_relevance', 'product_culture_links', ['relevance_score'])
        op.create_index('idx_product_culture_link_type', 'product_culture_links', ['link_type'])

    # 创建 origin_culture_links 表（产地-文化关联）
    # 仅当 origins 表存在时创建（当前 schema 无 origins 表，跳过以避免外键失败）
    if _table_exists(op, 'origins') and not _table_exists(op, 'origin_culture_links'):
        op.create_table(
            'origin_culture_links',
            sa.Column('origin_id', sa.BIGINT(), nullable=False),
            sa.Column('culture_id', sa.BIGINT(), nullable=False),
            sa.Column('strength', sa.DECIMAL(3, 2), nullable=False, server_default='1.00', comment='关联强度 0.00-1.00'),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('origin_id', 'culture_id'),
            sa.ForeignKeyConstraint(['origin_id'], ['origins.id'], ondelete='CASCADE', name='fk_origin_culture_origin'),
            sa.ForeignKeyConstraint(['culture_id'], ['cultural_elements.id'], ondelete='CASCADE', name='fk_origin_culture_element'),
            mysql_charset='utf8mb4',
            mysql_collate='utf8mb4_unicode_ci',
            mysql_engine='InnoDB',
            comment='产地-文化元素关联表'
        )
        op.create_index('idx_origin_culture_origin', 'origin_culture_links', ['origin_id'])
        op.create_index('idx_origin_culture_culture', 'origin_culture_links', ['culture_id'])
        op.create_index('idx_origin_culture_strength', 'origin_culture_links', ['strength'])


def downgrade() -> None:
    """降级数据库 - 删除知识图谱表"""
    if _table_exists(op, 'origin_culture_links'):
        if _index_exists(op, 'origin_culture_links', 'idx_origin_culture_strength'):
            op.drop_index('idx_origin_culture_strength', table_name='origin_culture_links')
        if _index_exists(op, 'origin_culture_links', 'idx_origin_culture_culture'):
            op.drop_index('idx_origin_culture_culture', table_name='origin_culture_links')
        if _index_exists(op, 'origin_culture_links', 'idx_origin_culture_origin'):
            op.drop_index('idx_origin_culture_origin', table_name='origin_culture_links')
        op.drop_table('origin_culture_links')

    if _table_exists(op, 'product_culture_links'):
        if _index_exists(op, 'product_culture_links', 'idx_product_culture_link_type'):
            op.drop_index('idx_product_culture_link_type', table_name='product_culture_links')
        if _index_exists(op, 'product_culture_links', 'idx_product_culture_relevance'):
            op.drop_index('idx_product_culture_relevance', table_name='product_culture_links')
        if _index_exists(op, 'product_culture_links', 'idx_product_culture_culture'):
            op.drop_index('idx_product_culture_culture', table_name='product_culture_links')
        if _index_exists(op, 'product_culture_links', 'idx_product_culture_product'):
            op.drop_index('idx_product_culture_product', table_name='product_culture_links')
        op.drop_table('product_culture_links')

    if _table_exists(op, 'cultural_elements'):
        if _index_exists(op, 'cultural_elements', 'idx_cultural_elements_created_at'):
            op.drop_index('idx_cultural_elements_created_at', table_name='cultural_elements')
        if _index_exists(op, 'cultural_elements', 'idx_cultural_elements_region'):
            op.drop_index('idx_cultural_elements_region', table_name='cultural_elements')
        if _index_exists(op, 'cultural_elements', 'idx_cultural_elements_hot_score'):
            op.drop_index('idx_cultural_elements_hot_score', table_name='cultural_elements')
        if _index_exists(op, 'cultural_elements', 'idx_cultural_elements_type'):
            op.drop_index('idx_cultural_elements_type', table_name='cultural_elements')
        op.drop_table('cultural_elements')
