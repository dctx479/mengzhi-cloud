-- 配额和计费系统优化迁移脚本
-- 版本: 005_optimize_quota_billing
-- 日期: 2026-01-22

USE agri_platform;

-- 1. 更新 tenant_quotas 表，添加新字段
ALTER TABLE tenant_quotas
ADD COLUMN monthly_images INT DEFAULT 0 COMMENT '每月图片配额',
ADD COLUMN daily_images INT DEFAULT 0 COMMENT '每日图片配额',
ADD COLUMN monthly_video_seconds INT DEFAULT 0 COMMENT '每月视频秒数配额',
ADD COLUMN daily_video_seconds INT DEFAULT 0 COMMENT '每日视频秒数配额',
ADD COLUMN max_concurrent_requests INT DEFAULT 1 COMMENT '最大并发请求数',
ADD COLUMN balance DECIMAL(10,2) DEFAULT 0.00 COMMENT '账户余额',
ADD COLUMN pending_amount DECIMAL(10,2) DEFAULT 0.00 COMMENT '待确认金额';

-- 2. 创建计费事务表
CREATE TABLE IF NOT EXISTS billing_transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '交易ID',
    enterprise_id BIGINT NOT NULL COMMENT '企业ID',
    quota_id BIGINT NOT NULL COMMENT '配额ID',

    service_type VARCHAR(50) NOT NULL COMMENT '服务类型',
    amount DECIMAL(10,4) NOT NULL COMMENT '金额',
    status ENUM('pending', 'completed', 'refunded', 'failed', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '状态',

    idempotency_key VARCHAR(64) UNIQUE COMMENT '幂等性key',

    request_params TEXT COMMENT '请求参数（JSON）',
    actual_usage TEXT COMMENT '实际使用情况（JSON）',

    refund_amount DECIMAL(10,4) COMMENT '退款金额',
    refund_reason VARCHAR(200) COMMENT '退款原因',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    refunded_at TIMESTAMP NULL COMMENT '退款时间',

    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_quota_id (quota_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_idempotency_key (idempotency_key),

    FOREIGN KEY (quota_id) REFERENCES tenant_quotas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='计费事务表';

-- 3. 创建配额使用详情表（如果不存在）
CREATE TABLE IF NOT EXISTS quota_usage_details (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    quota_id BIGINT NOT NULL COMMENT '配额ID',
    transaction_id BIGINT COMMENT '关联交易ID',

    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型（image/video/token）',
    amount INT NOT NULL COMMENT '使用量',

    resolution VARCHAR(20) COMMENT '分辨率',
    duration INT COMMENT '时长（秒）',

    metadata TEXT COMMENT '元数据（JSON）',
    used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '使用时间',

    INDEX idx_quota_id (quota_id),
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_resource_type (resource_type),
    INDEX idx_used_at (used_at),

    FOREIGN KEY (quota_id) REFERENCES tenant_quotas(id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES billing_transactions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配额使用详情表';

-- 4. 创建计费审计日志表
CREATE TABLE IF NOT EXISTS billing_audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    transaction_id BIGINT NOT NULL COMMENT '交易ID',

    action VARCHAR(50) NOT NULL COMMENT '操作（pre_deduct/confirm/refund）',
    old_status VARCHAR(20) COMMENT '旧状态',
    new_status VARCHAR(20) COMMENT '新状态',

    operator_id BIGINT COMMENT '操作人ID',
    operator_type VARCHAR(20) COMMENT '操作人类型（system/user/admin）',

    details TEXT COMMENT '详情（JSON）',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_transaction_id (transaction_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (transaction_id) REFERENCES billing_transactions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='计费审计日志表';

-- 5. 初始化企业余额（给现有企业充值）
UPDATE tenant_quotas SET balance = 100.00 WHERE balance = 0.00;

-- 6. 添加索引优化查询性能
CREATE INDEX idx_enterprise_balance ON tenant_quotas(enterprise_id, balance);
CREATE INDEX idx_status_created ON billing_transactions(status, created_at);

-- 完成
SELECT 'Migration 005 completed successfully' AS status;
