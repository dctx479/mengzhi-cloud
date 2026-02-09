-- 数据库迁移脚本
-- 版本: 004_add_multi_tenant_ai_support
-- 日期: 2026-01-22

USE agri_platform;

-- 1. 创建 tenant_ai_configs 表
CREATE TABLE IF NOT EXISTS tenant_ai_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    enterprise_id BIGINT NOT NULL COMMENT '所属企业ID',
    provider VARCHAR(50) NOT NULL COMMENT 'AI服务商: deepseek, openai, qwen',
    api_key_encrypted TEXT NOT NULL COMMENT '加密的API密钥',
    base_url VARCHAR(255) DEFAULT NULL COMMENT '自定义API地址',
    default_model VARCHAR(100) DEFAULT NULL COMMENT '默认模型',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL DEFAULT NULL COMMENT '删除时间',

    CONSTRAINT fk_tenant_ai_configs_enterprise
        FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE,

    UNIQUE KEY idx_enterprise_provider (enterprise_id, provider),
    KEY idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户AI配置表';

-- 2. 添加 users.is_admin 字段
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否为系统管理员'
AFTER password_changed_at;

-- 3. 添加索引
ALTER TABLE users
ADD INDEX IF NOT EXISTS idx_is_admin (is_admin);

-- 验证
SELECT 'Migration completed successfully!' AS status;
SHOW TABLES LIKE 'tenant_ai_configs';
SHOW COLUMNS FROM users LIKE 'is_admin';
