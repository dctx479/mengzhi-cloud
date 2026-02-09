"""Add SLA system

Revision ID: 009_add_sla_system
Revises: 004_add_multi_tenant_ai_support
Create Date: 2026-01-22 10:00:00.000000

添加SLA保障系统：
- sla_agreements: SLA协议表
- sla_metrics: SLA指标记录表
- sla_violations: SLA违约记录表
- performance_logs: 性能日志表
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '009_add_sla_system'
down_revision = '004_add_multi_tenant_ai_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库 - 添加SLA系统表"""

    # 创建sla_agreements表
    op.create_table(
        'sla_agreements',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('agreement_uuid', sa.VARCHAR(36), nullable=False),
        sa.Column('enterprise_id', mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=True),
        sa.Column('name', sa.VARCHAR(200), nullable=False, comment='协议名称'),
        sa.Column('level', sa.Enum('BASIC', 'STANDARD', 'PREMIUM', 'ENTERPRISE', name='slalevel'),
                  nullable=False, server_default='STANDARD', comment='SLA等级'),
        sa.Column('description', sa.TEXT(), nullable=True, comment='协议描述'),
        sa.Column('start_date', sa.VARCHAR(20), nullable=False, comment='开始日期'),
        sa.Column('end_date', sa.VARCHAR(20), nullable=False, comment='结束日期'),
        sa.Column('availability_target', sa.FLOAT(), nullable=False, server_default='99.5', comment='可用性目标(%)'),
        sa.Column('response_time_target', sa.INTEGER(), nullable=False, server_default='2000', comment='响应时间目标(ms)'),
        sa.Column('error_rate_target', sa.FLOAT(), nullable=False, server_default='0.1', comment='错误率目标(%)'),
        sa.Column('throughput_target', sa.INTEGER(), nullable=False, server_default='100', comment='吞吐量目标(req/s)'),
        sa.Column('compensation_enabled', sa.BOOLEAN(), nullable=False, server_default='1', comment='是否启用补偿'),
        sa.Column('compensation_rules', sa.JSON(), nullable=True, comment='补偿规则(JSON)'),
        sa.Column('is_active', sa.BOOLEAN(), nullable=False, server_default='1', comment='是否激活'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agreement_uuid'),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='SLA协议表'
    )

    # 创建索引
    op.create_index('idx_agreement_enterprise', 'sla_agreements', ['enterprise_id'])
    op.create_index('idx_agreement_user', 'sla_agreements', ['user_id'])
    op.create_index('idx_agreement_level', 'sla_agreements', ['level'])
    op.create_index('idx_agreement_active', 'sla_agreements', ['is_active'])
    op.create_index('idx_agreement_dates', 'sla_agreements', ['start_date', 'end_date'])

    # 创建sla_metrics表
    op.create_table(
        'sla_metrics',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('metric_uuid', sa.VARCHAR(36), nullable=False),
        sa.Column('agreement_id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('metric_type', sa.Enum('AVAILABILITY', 'RESPONSE_TIME', 'ERROR_RATE', 'THROUGHPUT', 'SUCCESS_RATE',
                                         name='metrictype'), nullable=False, comment='指标类型'),
        sa.Column('metric_name', sa.VARCHAR(100), nullable=False, comment='指标名称'),
        sa.Column('period_start', sa.VARCHAR(30), nullable=False, comment='统计开始时间'),
        sa.Column('period_end', sa.VARCHAR(30), nullable=False, comment='统计结束时间'),
        sa.Column('target_value', sa.FLOAT(), nullable=False, comment='目标值'),
        sa.Column('actual_value', sa.FLOAT(), nullable=False, comment='实际值'),
        sa.Column('achievement_rate', sa.FLOAT(), nullable=False, comment='达成率(%)'),
        sa.Column('total_requests', sa.INTEGER(), nullable=False, server_default='0', comment='总请求数'),
        sa.Column('successful_requests', sa.INTEGER(), nullable=False, server_default='0', comment='成功请求数'),
        sa.Column('failed_requests', sa.INTEGER(), nullable=False, server_default='0', comment='失败请求数'),
        sa.Column('avg_response_time', sa.FLOAT(), nullable=True, comment='平均响应时间(ms)'),
        sa.Column('min_response_time', sa.FLOAT(), nullable=True, comment='最小响应时间(ms)'),
        sa.Column('max_response_time', sa.FLOAT(), nullable=True, comment='最大响应时间(ms)'),
        sa.Column('p50_response_time', sa.FLOAT(), nullable=True, comment='P50响应时间(ms)'),
        sa.Column('p95_response_time', sa.FLOAT(), nullable=True, comment='P95响应时间(ms)'),
        sa.Column('p99_response_time', sa.FLOAT(), nullable=True, comment='P99响应时间(ms)'),
        sa.Column('is_compliant', sa.BOOLEAN(), nullable=False, server_default='1', comment='是否达标'),
        sa.Column('notes', sa.TEXT(), nullable=True, comment='备注'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_uuid'),
        sa.ForeignKeyConstraint(['agreement_id'], ['sla_agreements.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='SLA指标记录表'
    )

    # 创建索引
    op.create_index('idx_metric_agreement', 'sla_metrics', ['agreement_id'])
    op.create_index('idx_metric_type', 'sla_metrics', ['metric_type'])
    op.create_index('idx_metric_period', 'sla_metrics', ['period_start', 'period_end'])
    op.create_index('idx_metric_compliant', 'sla_metrics', ['is_compliant'])

    # 创建sla_violations表
    op.create_table(
        'sla_violations',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('violation_uuid', sa.VARCHAR(36), nullable=False),
        sa.Column('agreement_id', mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column('metric_type', sa.Enum('AVAILABILITY', 'RESPONSE_TIME', 'ERROR_RATE', 'THROUGHPUT', 'SUCCESS_RATE',
                                         name='metrictype'), nullable=False, comment='违约指标类型'),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='violationseverity'),
                  nullable=False, comment='严重程度'),
        sa.Column('target_value', sa.FLOAT(), nullable=False, comment='目标值'),
        sa.Column('actual_value', sa.FLOAT(), nullable=False, comment='实际值'),
        sa.Column('deviation', sa.FLOAT(), nullable=False, comment='偏差值'),
        sa.Column('deviation_rate', sa.FLOAT(), nullable=False, comment='偏差率(%)'),
        sa.Column('violation_time', sa.VARCHAR(30), nullable=False, comment='违约时间'),
        sa.Column('duration', sa.INTEGER(), nullable=True, comment='持续时间(秒)'),
        sa.Column('affected_users', sa.INTEGER(), nullable=False, server_default='0', comment='影响用户数'),
        sa.Column('affected_requests', sa.INTEGER(), nullable=False, server_default='0', comment='影响请求数'),
        sa.Column('is_resolved', sa.BOOLEAN(), nullable=False, server_default='0', comment='是否已解决'),
        sa.Column('resolved_at', sa.VARCHAR(30), nullable=True, comment='解决时间'),
        sa.Column('resolution_notes', sa.TEXT(), nullable=True, comment='解决说明'),
        sa.Column('compensation_amount', sa.FLOAT(), nullable=True, comment='补偿金额'),
        sa.Column('compensation_status', sa.VARCHAR(20), nullable=True, comment='补偿状态'),
        sa.Column('description', sa.TEXT(), nullable=True, comment='违约描述'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('violation_uuid'),
        sa.ForeignKeyConstraint(['agreement_id'], ['sla_agreements.id'], ondelete='CASCADE'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='SLA违约记录表'
    )

    # 创建索引
    op.create_index('idx_violation_agreement', 'sla_violations', ['agreement_id'])
    op.create_index('idx_violation_type', 'sla_violations', ['metric_type'])
    op.create_index('idx_violation_severity', 'sla_violations', ['severity'])
    op.create_index('idx_violation_time', 'sla_violations', ['violation_time'])
    op.create_index('idx_violation_resolved', 'sla_violations', ['is_resolved'])

    # 创建performance_logs表
    op.create_table(
        'performance_logs',
        sa.Column('id', mysql.BIGINT(unsigned=True), nullable=False, autoincrement=True),
        sa.Column('log_uuid', sa.VARCHAR(36), nullable=False),
        sa.Column('request_id', sa.VARCHAR(36), nullable=False, comment='请求ID'),
        sa.Column('endpoint', sa.VARCHAR(500), nullable=False, comment='请求端点'),
        sa.Column('method', sa.VARCHAR(10), nullable=False, comment='请求方法'),
        sa.Column('user_id', mysql.BIGINT(unsigned=True), nullable=True, comment='用户ID'),
        sa.Column('enterprise_id', mysql.BIGINT(unsigned=True), nullable=True, comment='企业ID'),
        sa.Column('response_time', sa.FLOAT(), nullable=False, comment='响应时间(ms)'),
        sa.Column('status_code', sa.INTEGER(), nullable=False, comment='HTTP状态码'),
        sa.Column('is_success', sa.BOOLEAN(), nullable=False, comment='是否成功'),
        sa.Column('request_size', sa.INTEGER(), nullable=True, comment='请求大小(bytes)'),
        sa.Column('response_size', sa.INTEGER(), nullable=True, comment='响应大小(bytes)'),
        sa.Column('error_message', sa.TEXT(), nullable=True, comment='错误信息'),
        sa.Column('timestamp', sa.VARCHAR(30), nullable=False, comment='时间戳'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('log_uuid'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
        comment='性能日志表'
    )

    # 创建索引
    op.create_index('idx_perflog_timestamp', 'performance_logs', ['timestamp'])
    op.create_index('idx_perflog_endpoint', 'performance_logs', ['endpoint'])
    op.create_index('idx_perflog_user', 'performance_logs', ['user_id'])
    op.create_index('idx_perflog_enterprise', 'performance_logs', ['enterprise_id'])
    op.create_index('idx_perflog_success', 'performance_logs', ['is_success'])
    op.create_index('idx_perflog_response_time', 'performance_logs', ['response_time'])


def downgrade() -> None:
    """降级数据库 - 删除SLA系统表"""

    # 删除表（按依赖关系逆序删除）
    op.drop_table('performance_logs')
    op.drop_table('sla_violations')
    op.drop_table('sla_metrics')
    op.drop_table('sla_agreements')

    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS slalevel")
    op.execute("DROP TYPE IF EXISTS metrictype")
    op.execute("DROP TYPE IF EXISTS violationseverity")
