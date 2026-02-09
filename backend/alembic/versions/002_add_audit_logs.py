"""
添加审计日志表和产品全文索引 - BUG-028, BUG-025修复

Revision ID: 002
Revises: 001
Create Date: 2026-01-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_audit_logs'
down_revision = '001_add_enterprises'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库"""
    
    # 创建审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.BIGINT(unsigned=True), primary_key=True, autoincrement=True, comment='日志ID'),
        sa.Column('user_id', sa.BIGINT(unsigned=True), nullable=True, comment='操作用户ID'),
        sa.Column('username', sa.VARCHAR(50), nullable=True, comment='操作用户名'),
        sa.Column('action', sa.VARCHAR(50), nullable=False, comment='操作类型'),
        sa.Column('resource', sa.VARCHAR(50), nullable=False, comment='资源类型'),
        sa.Column('resource_id', sa.BIGINT(unsigned=True), nullable=True, comment='资源ID'),
        sa.Column('details', sa.Text, nullable=True, comment='操作详情'),
        sa.Column('changes', sa.Text, nullable=True, comment='变更内容'),
        sa.Column('ip_address', sa.VARCHAR(45), nullable=True, comment='IP地址'),
        sa.Column('user_agent', sa.VARCHAR(500), nullable=True, comment='User-Agent'),
        sa.Column('request_method', sa.VARCHAR(10), nullable=True, comment='HTTP方法'),
        sa.Column('request_path', sa.VARCHAR(500), nullable=True, comment='请求路径'),
        sa.Column('status_code', sa.Integer, nullable=True, comment='响应状态码'),
        sa.Column('is_success', sa.Integer, default=1, comment='是否成功'),
        sa.Column('error_message', sa.Text, nullable=True, comment='错误消息'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # 创建索引
    op.create_index('idx_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_action', 'audit_logs', ['action'])
    op.create_index('idx_resource', 'audit_logs', ['resource', 'resource_id'])
    op.create_index('idx_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_user_action', 'audit_logs', ['user_id', 'action'])
    
    # 添加产品表全文索引 (BUG-025修复)
    op.execute("""
        ALTER TABLE products 
        ADD FULLTEXT INDEX idx_product_search (name, description, cultural_description)
    """)
    
    print("✓ 审计日志表创建成功")
    print("✓ 产品全文索引创建成功")


def downgrade():
    """降级数据库"""
    
    # 删除产品全文索引
    op.execute("ALTER TABLE products DROP INDEX idx_product_search")
    
    # 删除索引
    op.drop_index('idx_user_action', 'audit_logs')
    op.drop_index('idx_created_at', 'audit_logs')
    op.drop_index('idx_resource', 'audit_logs')
    op.drop_index('idx_action', 'audit_logs')
    op.drop_index('idx_user_id', 'audit_logs')
    
    # 删除审计日志表
    op.drop_table('audit_logs')
    
    print("✓ 审计日志表已删除")
    print("✓ 产品全文索引已删除")
