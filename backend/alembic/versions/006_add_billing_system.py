"""Add billing system tables

Revision ID: 006_add_billing_system
Revises: 004_add_multi_tenant_ai_support
Create Date: 2026-01-22 10:00:00.000000

添加计费系统表:
- billing_plans: 计费方案表
- billing_records: 计费记录表
- invoices: 账单表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '006_add_billing_system'
down_revision = '004_add_multi_tenant_ai_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 创建计费系统表"""

    # 创建 billing_plans 表
    op.create_table(
        'billing_plans',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('plan_uuid', sa.VARCHAR(36), nullable=False, comment='方案UUID'),
        sa.Column('name', sa.VARCHAR(100), nullable=False, comment='方案名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='方案描述'),
        sa.Column('billing_mode', sa.Enum('token', 'message', 'api_call', 'monthly', 'tiered', name='billing_mode'),
                  nullable=False, comment='计费模式'),
        sa.Column('pricing_type', sa.Enum('fixed', 'unit', 'tiered', name='pricing_type'),
                  nullable=False, comment='定价类型'),
        sa.Column('pricing_rules', sa.JSON(), nullable=False, comment='定价规则配置'),
        sa.Column('quota_limits', sa.JSON(), nullable=True, comment='配额限制配置'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='是否启用'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='0', comment='是否为默认方案'),
        sa.Column('applicable_to', sa.VARCHAR(50), nullable=True, comment='适用对象'),
        sa.Column('valid_from', sa.DATE(), nullable=True, comment='生效日期'),
        sa.Column('valid_until', sa.DATE(), nullable=True, comment='失效日期'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序顺序'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_uuid', name='uk_plan_uuid'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='计费方案表'
    )

    # 创建 billing_plans 表索引
    op.create_index('idx_bp_plan_uuid', 'billing_plans', ['plan_uuid'])
    op.create_index('idx_bp_billing_mode', 'billing_plans', ['billing_mode'])
    op.create_index('idx_bp_is_active', 'billing_plans', ['is_active'])
    op.create_index('idx_bp_is_default', 'billing_plans', ['is_default'])
    op.create_index('idx_bp_sort_order', 'billing_plans', ['sort_order'])

    # 创建 billing_records 表
    op.create_table(
        'billing_records',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('record_uuid', sa.VARCHAR(36), nullable=False, comment='记录UUID'),
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=False, comment='用户ID'),
        sa.Column('plan_id', mysql.BIGINT(unsigned=True), nullable=True, comment='计费方案ID'),
        sa.Column('billing_mode', sa.Enum('token', 'message', 'api_call', 'monthly', 'tiered', name='billing_mode'),
                  nullable=False, comment='计费模式'),
        sa.Column('usage_data', sa.JSON(), nullable=False, comment='使用量数据'),
        sa.Column('unit_price', mysql.DECIMAL(10, 6), nullable=False, comment='单价'),
        sa.Column('quantity', sa.Integer(), nullable=False, comment='数量'),
        sa.Column('amount', mysql.DECIMAL(10, 2), nullable=False, comment='金额'),
        sa.Column('currency', sa.VARCHAR(10), nullable=False, server_default='CNY', comment='货币单位'),
        sa.Column('resource_type', sa.VARCHAR(50), nullable=True, comment='资源类型'),
        sa.Column('resource_id', mysql.BIGINT(unsigned=True), nullable=True, comment='资源ID'),
        sa.Column('billing_date', sa.DATE(), nullable=False, comment='计费日期'),
        sa.Column('billing_month', sa.VARCHAR(7), nullable=False, comment='计费月份'),
        sa.Column('invoice_id', mysql.BIGINT(unsigned=True), nullable=True, comment='所属账单ID'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注信息'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('record_uuid', name='uk_record_uuid'),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_br_user_id',
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['plan_id'], ['billing_plans.id'],
            name='fk_br_plan_id',
            ondelete='SET NULL'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='计费记录表'
    )

    # 创建 billing_records 表索引
    op.create_index('idx_br_record_uuid', 'billing_records', ['record_uuid'])
    op.create_index('idx_br_user_id', 'billing_records', ['user_id'])
    op.create_index('idx_br_plan_id', 'billing_records', ['plan_id'])
    op.create_index('idx_br_billing_mode', 'billing_records', ['billing_mode'])
    op.create_index('idx_br_billing_date', 'billing_records', ['billing_date'])
    op.create_index('idx_br_billing_month', 'billing_records', ['billing_month'])
    op.create_index('idx_br_invoice_id', 'billing_records', ['invoice_id'])
    op.create_index('idx_br_resource', 'billing_records', ['resource_type', 'resource_id'])

    # 创建 invoices 表
    op.create_table(
        'invoices',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('invoice_uuid', sa.VARCHAR(36), nullable=False, comment='账单UUID'),
        sa.Column('invoice_number', sa.VARCHAR(50), nullable=False, comment='账单编号'),
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=False, comment='用户ID'),
        sa.Column('billing_period_start', sa.DATE(), nullable=False, comment='账单周期开始日期'),
        sa.Column('billing_period_end', sa.DATE(), nullable=False, comment='账单周期结束日期'),
        sa.Column('subtotal', mysql.DECIMAL(10, 2), nullable=False, server_default='0', comment='小计金额'),
        sa.Column('discount', mysql.DECIMAL(10, 2), nullable=False, server_default='0', comment='折扣金额'),
        sa.Column('tax', mysql.DECIMAL(10, 2), nullable=False, server_default='0', comment='税费'),
        sa.Column('total', mysql.DECIMAL(10, 2), nullable=False, server_default='0', comment='总金额'),
        sa.Column('currency', sa.VARCHAR(10), nullable=False, server_default='CNY', comment='货币单位'),
        sa.Column('status', sa.Enum('pending', 'paid', 'overdue', 'cancelled', 'refunded', name='invoice_status'),
                  nullable=False, server_default='pending', comment='账单状态'),
        sa.Column('payment_method', sa.Enum('wechat', 'alipay', 'bank', 'balance', 'other', name='payment_method'),
                  nullable=True, comment='支付方式'),
        sa.Column('paid_at', sa.TIMESTAMP(), nullable=True, comment='支付时间'),
        sa.Column('payment_transaction_id', sa.VARCHAR(100), nullable=True, comment='支付交易ID'),
        sa.Column('due_date', sa.DATE(), nullable=False, comment='到期日期'),
        sa.Column('usage_summary', sa.JSON(), nullable=True, comment='使用量汇总'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注信息'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True, comment='软删除时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_uuid', name='uk_invoice_uuid'),
        sa.UniqueConstraint('invoice_number', name='uk_invoice_number'),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_inv_user_id',
            ondelete='CASCADE'
        ),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        mysql_engine='InnoDB',
        comment='账单表'
    )

    # 创建 invoices 表索引
    op.create_index('idx_inv_invoice_uuid', 'invoices', ['invoice_uuid'])
    op.create_index('idx_inv_invoice_number', 'invoices', ['invoice_number'])
    op.create_index('idx_inv_user_id', 'invoices', ['user_id'])
    op.create_index('idx_inv_status', 'invoices', ['status'])
    op.create_index('idx_inv_due_date', 'invoices', ['due_date'])
    op.create_index('idx_inv_billing_period', 'invoices', ['billing_period_start', 'billing_period_end'])

    # 添加外键约束（billing_records.invoice_id -> invoices.id）
    # 注意：这个外键在创建billing_records表时无法添加，因为invoices表还不存在
    # 所以在这里单独添加
    op.create_foreign_key(
        'fk_br_invoice_id',
        'billing_records',
        'invoices',
        ['invoice_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """降级数据库 - 删除计费系统表"""

    # 删除外键约束
    op.drop_constraint('fk_br_invoice_id', 'billing_records', type_='foreignkey')

    # 删除表（先删除有外键依赖的表）
    op.drop_table('billing_records')
    op.drop_table('invoices')
    op.drop_table('billing_plans')

    # 删除枚举类型（如果数据库支持）
    # MySQL会自动删除，PostgreSQL需要手动删除
    # op.execute('DROP TYPE IF EXISTS billing_mode')
    # op.execute('DROP TYPE IF EXISTS pricing_type')
    # op.execute('DROP TYPE IF EXISTS invoice_status')
    # op.execute('DROP TYPE IF EXISTS payment_method')
