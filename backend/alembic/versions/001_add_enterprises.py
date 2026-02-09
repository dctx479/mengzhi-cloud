"""Add enterprises table

Revision ID: 001_add_enterprises
Revises: 001_initial
Create Date: 2026-01-23 10:00:00.000000

创建企业表:
- enterprises: 企业基本信息表
- 为users表添加外键约束
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_add_enterprises'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 创建enterprises表"""

    # 创建enterprises表
    op.create_table(
        'enterprises',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('enterprise_uuid', sa.VARCHAR(36), nullable=False),
        sa.Column('name', sa.VARCHAR(200), nullable=False, comment='企业名称'),
        sa.Column('short_name', sa.VARCHAR(100), nullable=True, comment='企业简称'),
        sa.Column('license_no', sa.VARCHAR(50), nullable=False, comment='营业执照号'),
        sa.Column('license_image_url', sa.VARCHAR(500), nullable=True, comment='营业执照图片URL'),
        sa.Column('contact_name', sa.VARCHAR(50), nullable=True, comment='联系人姓名'),
        sa.Column('contact_phone', sa.VARCHAR(20), nullable=True, comment='联系人电话'),
        sa.Column('contact_email', sa.VARCHAR(100), nullable=True, comment='联系人邮箱'),
        sa.Column('province', sa.VARCHAR(50), nullable=True, comment='省份'),
        sa.Column('city', sa.VARCHAR(50), nullable=True, comment='城市'),
        sa.Column('district', sa.VARCHAR(50), nullable=True, comment='区县'),
        sa.Column('address', sa.VARCHAR(500), nullable=True, comment='详细地址'),
        sa.Column('industry', sa.VARCHAR(100), nullable=True, comment='所属行业'),
        sa.Column('scale', sa.Enum('MICRO', 'SMALL', 'MEDIUM', 'LARGE', name='enterprisescale'),
                  nullable=False, server_default='SMALL', comment='企业规模'),
        sa.Column('description', sa.TEXT(), nullable=True, comment='企业简介'),
        sa.Column('logo_url', sa.VARCHAR(500), nullable=True, comment='企业Logo URL'),
        sa.Column('website', sa.VARCHAR(200), nullable=True, comment='企业官网'),
        sa.Column('verify_status', sa.Enum('PENDING', 'VERIFIED', 'REJECTED', name='verifystatus'),
                  nullable=False, server_default='PENDING', comment='认证状态'),
        sa.Column('verified_at', sa.TIMESTAMP(), nullable=True, comment='认证通过时间'),
        sa.Column('reject_reason', sa.VARCHAR(500), nullable=True, comment='拒绝原因'),
        sa.Column('plan_type', sa.Enum('FREE', 'BASIC', 'PRO', 'ENTERPRISE', name='plantype'),
                  nullable=False, server_default='FREE', comment='套餐类型'),
        sa.Column('plan_expires_at', sa.TIMESTAMP(), nullable=True, comment='套餐到期时间'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enterprise_uuid', name='uk_enterprise_uuid'),
        sa.UniqueConstraint('license_no', name='uk_license_no'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='企业表'
    )

    # 创建索引
    op.create_index('idx_name', 'enterprises', ['name'])
    op.create_index('idx_verify_status', 'enterprises', ['verify_status'])
    op.create_index('idx_plan_type', 'enterprises', ['plan_type'])
    op.create_index('idx_created_at', 'enterprises', ['created_at'])

    # 现在为users表添加外键约束（之前创建users表时没有enterprises表，所以无法创建外键）
    op.create_foreign_key(
        'fk_users_enterprise_id',
        'users', 'enterprises',
        ['enterprise_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """降级数据库 - 删除enterprises表"""

    # 删除users表的外键约束
    op.drop_constraint('fk_users_enterprise_id', 'users', type_='foreignkey')

    # 删除enterprises表
    op.drop_table('enterprises')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS enterprisescale")
    op.execute("DROP TYPE IF EXISTS verifystatus")
    op.execute("DROP TYPE IF EXISTS plantype")