-- 配额支付系统数据库表创建脚本
-- 版本: 1.0
-- 创建日期: 2026-01-23

-- 1. 配额套餐表
CREATE TABLE IF NOT EXISTS `quota_packages` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '套餐ID',
    `name` VARCHAR(100) NOT NULL COMMENT '套餐名称',
    `package_type` ENUM('basic', 'standard', 'professional', 'enterprise') NOT NULL DEFAULT 'basic' COMMENT '套餐类型',
    `period` ENUM('monthly', 'quarterly', 'yearly', 'lifetime') NOT NULL DEFAULT 'monthly' COMMENT '套餐周期',
    `price` DECIMAL(10, 2) NOT NULL COMMENT '套餐价格(元)',
    `original_price` DECIMAL(10, 2) NULL COMMENT '原价(用于显示折扣)',
    `chat_quota` INT NOT NULL DEFAULT 0 COMMENT '对话次数配额',
    `generation_quota` INT NOT NULL DEFAULT 0 COMMENT '内容生成次数配额',
    `token_quota` INT NOT NULL DEFAULT 0 COMMENT 'Token配额',
    `storage_quota_mb` INT NOT NULL DEFAULT 0 COMMENT '存储空间配额(MB)',
    `validity_days` INT NOT NULL DEFAULT 30 COMMENT '有效期(天)',
    `description` TEXT NULL COMMENT '套餐描述',
    `features` TEXT NULL COMMENT '套餐特性(JSON格式)',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    `is_recommended` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否推荐',
    `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序顺序',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_package_type` (`package_type`),
    INDEX `idx_is_active` (`is_active`),
    INDEX `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配额套餐表';

-- 2. 订单表
CREATE TABLE IF NOT EXISTS `orders` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '订单ID',
    `order_no` VARCHAR(64) NOT NULL COMMENT '订单号',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `package_id` BIGINT NULL COMMENT '套餐ID',
    `package_name` VARCHAR(100) NOT NULL COMMENT '套餐名称',
    `package_type` VARCHAR(50) NOT NULL COMMENT '套餐类型',
    `amount` DECIMAL(10, 2) NOT NULL COMMENT '订单金额(元)',
    `original_amount` DECIMAL(10, 2) NULL COMMENT '原价',
    `discount_amount` DECIMAL(10, 2) NULL DEFAULT 0 COMMENT '优惠金额',
    `chat_quota` BIGINT NOT NULL DEFAULT 0 COMMENT '对话次数配额',
    `generation_quota` BIGINT NOT NULL DEFAULT 0 COMMENT '生成次数配额',
    `token_quota` BIGINT NOT NULL DEFAULT 0 COMMENT 'Token配额',
    `storage_quota_mb` BIGINT NOT NULL DEFAULT 0 COMMENT '存储配额(MB)',
    `validity_days` BIGINT NOT NULL DEFAULT 30 COMMENT '有效期(天)',
    `status` ENUM('pending', 'paid', 'completed', 'cancelled', 'refunded', 'failed') NOT NULL DEFAULT 'pending' COMMENT '订单状态',
    `remark` TEXT NULL COMMENT '订单备注',
    `paid_at` TIMESTAMP NULL COMMENT '支付时间',
    `completed_at` TIMESTAMP NULL COMMENT '完成时间',
    `cancelled_at` TIMESTAMP NULL COMMENT '取消时间',
    `expired_at` TIMESTAMP NULL COMMENT '过期时间',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `uk_order_no` (`order_no`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_package_id` (`package_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`package_id`) REFERENCES `quota_packages`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';

-- 3. 支付记录表
CREATE TABLE IF NOT EXISTS `payments` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '支付ID',
    `payment_no` VARCHAR(64) NOT NULL COMMENT '支付单号',
    `order_id` BIGINT NOT NULL COMMENT '订单ID',
    `amount` DECIMAL(10, 2) NOT NULL COMMENT '支付金额(元)',
    `payment_method` ENUM('alipay', 'wechat', 'balance', 'bank_card') NOT NULL COMMENT '支付方式',
    `status` ENUM('pending', 'processing', 'success', 'failed', 'cancelled', 'refunded') NOT NULL DEFAULT 'pending' COMMENT '支付状态',
    `transaction_id` VARCHAR(128) NULL COMMENT '第三方交易号',
    `channel_order_no` VARCHAR(128) NULL COMMENT '支付渠道订单号',
    `channel_response` TEXT NULL COMMENT '支付渠道响应(JSON)',
    `paid_at` TIMESTAMP NULL COMMENT '支付成功时间',
    `failed_at` TIMESTAMP NULL COMMENT '支付失败时间',
    `refunded_at` TIMESTAMP NULL COMMENT '退款时间',
    `failure_reason` TEXT NULL COMMENT '失败原因',
    `remark` TEXT NULL COMMENT '备注',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `uk_payment_no` (`payment_no`),
    INDEX `idx_order_id` (`order_id`),
    INDEX `idx_transaction_id` (`transaction_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_payment_method` (`payment_method`),
    INDEX `idx_created_at` (`created_at`),
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付记录表';

-- 4. 配额日志表
CREATE TABLE IF NOT EXISTS `quota_logs` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `order_id` BIGINT NULL COMMENT '关联订单ID',
    `log_type` ENUM('purchase', 'consume', 'expire', 'refund', 'gift', 'adjust') NOT NULL COMMENT '日志类型',
    `status` ENUM('success', 'failed', 'pending') NOT NULL DEFAULT 'success' COMMENT '状态',
    `chat_change` INT NOT NULL DEFAULT 0 COMMENT '对话次数变动',
    `generation_change` INT NOT NULL DEFAULT 0 COMMENT '生成次数变动',
    `token_change` INT NOT NULL DEFAULT 0 COMMENT 'Token变动',
    `storage_change_mb` INT NOT NULL DEFAULT 0 COMMENT '存储空间变动(MB)',
    `chat_balance` INT NULL COMMENT '对话次数余额',
    `generation_balance` INT NULL COMMENT '生成次数余额',
    `token_balance` INT NULL COMMENT 'Token余额',
    `storage_balance_mb` INT NULL COMMENT '存储余额(MB)',
    `description` VARCHAR(500) NULL COMMENT '变动描述',
    `remark` TEXT NULL COMMENT '备注',
    `operator_id` BIGINT NULL COMMENT '操作人ID',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_order_id` (`order_id`),
    INDEX `idx_log_type` (`log_type`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`operator_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配额日志表';

-- 插入默认套餐数据
INSERT INTO `quota_packages` (
    `name`, `package_type`, `period`, `price`, `original_price`,
    `chat_quota`, `generation_quota`, `token_quota`, `storage_quota_mb`,
    `validity_days`, `description`, `is_active`, `is_recommended`, `sort_order`
) VALUES
('基础版-月付', 'basic', 'monthly', 29.00, 39.00, 100, 50, 50000, 500, 30, '适合个人用户轻度使用', TRUE, FALSE, 1),
('标准版-月付', 'standard', 'monthly', 99.00, 129.00, 500, 200, 200000, 2000, 30, '适合个人用户中度使用', TRUE, TRUE, 2),
('专业版-月付', 'professional', 'monthly', 299.00, 399.00, 2000, 1000, 1000000, 10000, 30, '适合专业用户和小团队', TRUE, FALSE, 3),
('企业版-年付', 'enterprise', 'yearly', 9999.00, 12999.00, 50000, 20000, 20000000, 100000, 365, '适合企业用户,提供定制服务', TRUE, FALSE, 4);
