"""
创建media表 - 数据库迁移脚本

迁移内容:
- 创建media表
- 添加索引和外键约束
- 支持图片、视频、音频、文档等多种媒体类型

Revision ID: 002_create_media_table
Revises: 001_initial_tables
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = '002_create_media_table'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""

    # 创建media表
    op.create_table(
        'media',
        sa.Column('id', mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True, comment='媒体ID'),
        sa.Column('media_uuid', sa.VARCHAR(36), nullable=False, unique=True, comment='媒体UUID'),

        # 文件信息
        sa.Column('filename', sa.VARCHAR(255), nullable=False, comment='原始文件名'),
        sa.Column('file_path', sa.VARCHAR(500), nullable=False, comment='存储路径'),
        sa.Column('file_url', sa.VARCHAR(500), nullable=False, comment='访问URL'),
        sa.Column('file_size', mysql.BIGINT(unsigned=True), nullable=False, comment='文件大小(字节)'),
        sa.Column('mime_type', sa.VARCHAR(100), nullable=False, comment='MIME类型'),

        # 分类
        sa.Column('media_type', sa.Enum('image', 'video', 'audio', 'document', name='media_type_enum'),
                  nullable=False, comment='媒体类型'),
        sa.Column('category', sa.Enum('product', 'culture', 'certificate', 'user_avatar', 'other', name='media_category_enum'),
                  nullable=False, comment='媒体分类'),

        # 元数据
        sa.Column('width', mysql.INTEGER(unsigned=True), nullable=True, comment='宽度(像素)'),
        sa.Column('height', mysql.INTEGER(unsigned=True), nullable=True, comment='高度(像素)'),
        sa.Column('duration', mysql.INTEGER(unsigned=True), nullable=True, comment='时长(秒)'),
        sa.Column('thumbnail_url', sa.VARCHAR(500), nullable=True, comment='缩略图URL'),

        # 关联
        sa.Column('product_id', mysql.BIGINT(unsigned=True), nullable=True, comment='关联产品ID'),
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=False, comment='上传者用户ID'),

        # 描述信息
        sa.Column('title', sa.VARCHAR(200), nullable=True, comment='标题'),
        sa.Column('description', sa.TEXT, nullable=True, comment='描述'),
        sa.Column('alt_text', sa.VARCHAR(200), nullable=True, comment='图片alt属性'),

        # 状态
        sa.Column('is_public', sa.Boolean, default=True, comment='是否公开'),
        sa.Column('is_processed', sa.Boolean, default=False, comment='是否已处理'),

        # 时间戳
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime, nullable=True, comment='软删除时间'),

        # 主键和约束
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('media_uuid', name='uk_media_uuid'),

        # 外键
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_media_product', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_media_user', ondelete='CASCADE'),

        # 索引
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='媒体素材表'
    )

    # 创建索引
    op.create_index('idx_media_type', 'media', ['media_type'])
    op.create_index('idx_category', 'media', ['category'])
    op.create_index('idx_user_id', 'media', ['user_id'])
    op.create_index('idx_product_id', 'media', ['product_id'])
    op.create_index('idx_created_at', 'media', ['created_at'])
    op.create_index('idx_deleted_at', 'media', ['deleted_at'])


def downgrade():
    """降级数据库"""

    # 删除索引
    op.drop_index('idx_deleted_at', 'media')
    op.drop_index('idx_created_at', 'media')
    op.drop_index('idx_product_id', 'media')
    op.drop_index('idx_user_id', 'media')
    op.drop_index('idx_category', 'media')
    op.drop_index('idx_media_type', 'media')

    # 删除表
    op.drop_table('media')

    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS media_type_enum')
    op.execute('DROP TYPE IF EXISTS media_category_enum')
