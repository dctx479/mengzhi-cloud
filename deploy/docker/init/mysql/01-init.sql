-- 内蒙古农畜产品AI平台数据库初始化脚本
-- 创建日期: 2026-01-17
-- 开发者: dctx479

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 创建用户表
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `user_uuid` VARCHAR(36) NOT NULL COMMENT '用户UUID',
  `username` VARCHAR(50) NOT NULL COMMENT '用户名',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `phone` VARCHAR(20) DEFAULT NULL COMMENT '手机号',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
  `user_type` ENUM('personal', 'enterprise') DEFAULT 'personal' COMMENT '用户类型',
  `status` ENUM('active', 'inactive', 'banned', 'pending') DEFAULT 'pending' COMMENT '状态',
  `role` VARCHAR(50) DEFAULT 'user' COMMENT '角色',
  `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_uuid` (`user_uuid`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  UNIQUE KEY `uk_phone` (`phone`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ----------------------------
-- 插入测试用户（密码: Test1234）
-- ----------------------------
INSERT INTO `users` (`user_uuid`, `username`, `email`, `password_hash`, `user_type`, `status`, `role`) VALUES
('00000000-0000-0000-0000-000000000001', 'admin', 'admin@example.com', '$2b$12$KIXxBvN9M6x6hKZv7gZGBOQp7qhZ7Zq0W5yJ9J9J9J9J9J9J9J9J9', 'enterprise', 'active', 'admin'),
('00000000-0000-0000-0000-000000000002', 'testuser', 'test@example.com', '$2b$12$KIXxBvN9M6x6hKZv7gZGBOQp7qhZ7Zq0W5yJ9J9J9J9J9J9J9J9J9', 'personal', 'active', 'user');

-- ----------------------------
-- 创建产品表（简化版）
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '产品ID',
  `product_uuid` VARCHAR(36) NOT NULL COMMENT '产品UUID',
  `name` VARCHAR(100) NOT NULL COMMENT '产品名称',
  `category` VARCHAR(50) DEFAULT NULL COMMENT '产品类别',
  `region` VARCHAR(100) DEFAULT NULL COMMENT '产地',
  `description` TEXT COMMENT '产品描述',
  `cultural_tags` JSON COMMENT '文化标签',
  `status` ENUM('active', 'inactive', 'draft') DEFAULT 'draft' COMMENT '状态',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_product_uuid` (`product_uuid`),
  KEY `idx_category` (`category`),
  KEY `idx_region` (`region`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品表';

-- ----------------------------
-- 插入示例产品
-- ----------------------------
INSERT INTO `products` (`product_uuid`, `name`, `category`, `region`, `description`, `cultural_tags`, `status`) VALUES
('10000000-0000-0000-0000-000000000001', '乌兰察布马铃薯', '农产品', '内蒙古乌兰察布', '乌兰察布马铃薯以其优良品质闻名全国', '["地理标志产品", "火山土壤", "昼夜温差大"]', 'active'),
('10000000-0000-0000-0000-000000000002', '苏尼特羊肉', '畜产品', '内蒙古锡林郭勒', '苏尼特羊肉鲜嫩多汁，营养丰富', '["地理标志产品", "草原放养", "蒙古族传统"]', 'active');

SET FOREIGN_KEY_CHECKS = 1;

-- 初始化完成
SELECT '数据库初始化完成' AS message;
