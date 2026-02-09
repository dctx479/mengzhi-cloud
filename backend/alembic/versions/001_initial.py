"""Create initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-01-17 10:00:00.000000

初始迁移: 创建所有核心表
- users: 用户表
- products: 产品表
- conversations: 对话表
- messages: 消息表

包含所有索引、约束和外键关系
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 创建初始表结构"""

    # 创建users表
    op.create_table(
        'users',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('user_uuid', sa.VARCHAR(36), nullable=False),
        sa.Column('username', sa.VARCHAR(50), nullable=False),
        sa.Column('email', sa.VARCHAR(100), nullable=True),
        sa.Column('phone', sa.VARCHAR(20), nullable=True),
        sa.Column('password_hash', sa.VARCHAR(255), nullable=False),
        sa.Column('user_type', sa.Enum('PERSONAL', 'ENTERPRISE', name='usertype'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', 'BANNED', 'PENDING', name='userstatus'), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'ENTERPRISE_ADMIN', 'USER', name='userrole'), nullable=False),
        sa.Column('enterprise_id', mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column('wechat_openid', sa.VARCHAR(100), nullable=True),
        sa.Column('wechat_unionid', sa.VARCHAR(100), nullable=True),
        sa.Column('douyin_openid', sa.VARCHAR(100), nullable=True),
        sa.Column('nickname', sa.VARCHAR(100), nullable=True),
        sa.Column('avatar_url', sa.VARCHAR(500), nullable=True),
        sa.Column('gender', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('login_attempts', mysql.INTEGER(unsigned=True), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_login_ip', sa.VARCHAR(45), nullable=True),
        sa.Column('password_changed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_uuid', name='uk_user_uuid'),
        sa.UniqueConstraint('username', name='uk_username'),
        sa.UniqueConstraint('email', name='uk_email'),
        sa.UniqueConstraint('phone', name='uk_phone'),
        sa.UniqueConstraint('wechat_openid', name='uk_wechat_openid'),
        sa.UniqueConstraint('douyin_openid', name='uk_douyin_openid'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB'
    )

    # 创建users表索引
    op.create_index('idx_user_type', 'users', ['user_type'])
    op.create_index('idx_status', 'users', ['status'])
    op.create_index('idx_enterprise_id', 'users', ['enterprise_id'])
    op.create_index('idx_created_at', 'users', ['created_at'])
    op.create_index('idx_deleted_at', 'users', ['deleted_at'])

    # 创建products表
    op.create_table(
        'products',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('sku', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('stock', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('region_code', sa.String(20), nullable=True),
        sa.Column('cultural_tags', sa.JSON(), nullable=True),
        sa.Column('cultural_description', sa.Text(), nullable=True),
        sa.Column('origin_story', sa.Text(), nullable=True),
        sa.Column('efficacy', sa.Text(), nullable=True),
        sa.Column('usage', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column('updated_by', mysql.BIGINT(unsigned=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sku', name='uk_sku'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB'
    )

    # 创建products表索引
    op.create_index('ix_sku', 'products', ['sku'])
    op.create_index('ix_name', 'products', ['name'])
    op.create_index('ix_category', 'products', ['category'])
    op.create_index('ix_region', 'products', ['region'])
    op.create_index('ix_status', 'products', ['status'])
    op.create_index('ix_category_status', 'products', ['category', 'status'])
    op.create_index('ix_region_status', 'products', ['region', 'status'])
    op.create_index('ix_created_at', 'products', ['created_at'])

    # 创建conversations表
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_favorited', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB'
    )

    # 创建conversations表索引
    op.create_index('idx_user_id', 'conversations', ['user_id'])
    op.create_index('idx_user_created', 'conversations', ['user_id', 'created_at'])
    op.create_index('idx_user_status', 'conversations', ['user_id', 'status'])

    # 创建messages表
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('model', sa.String(100), nullable=False, server_default='deepseek-chat'),
        sa.Column('finish_reason', sa.String(50), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], name='fk_messages_conversation_id'),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB'
    )

    # 创建messages表索引
    op.create_index('idx_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_conversation_role', 'messages', ['conversation_id', 'role'])
    op.create_index('idx_created_at', 'messages', ['created_at'])


def downgrade() -> None:
    """降级数据库 - 删除所有表"""

    # 删除外键约束
    op.drop_constraint('fk_messages_conversation_id', 'messages', type_='foreignkey')

    # 删除表
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('products')
    op.drop_table('users')
