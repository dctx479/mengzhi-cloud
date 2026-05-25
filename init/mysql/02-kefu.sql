-- 客服系统数据库迁移脚本
-- 文件: init/mysql/02-kefu.sql
-- 说明: 创建 kefu_tickets / kefu_escalations / kefu_conversations / kefu_messages 表

-- ============================================================
-- 1. 客服工单表
-- ============================================================
CREATE TABLE IF NOT EXISTS `kefu_tickets` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '工单ID',
    `ticket_uuid` VARCHAR(36) NOT NULL COMMENT '工单UUID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `category` ENUM('refund','return','exchange','repair','delivery','complaint','inquiry','product','quality','other')
        NOT NULL DEFAULT 'inquiry' COMMENT '工单类别',
    `priority` ENUM('low','normal','high','urgent') NOT NULL DEFAULT 'normal' COMMENT '优先级',
    `status` ENUM('pending','processing','resolved','closed','reopened') NOT NULL DEFAULT 'pending' COMMENT '工单状态',
    `title` VARCHAR(200) NOT NULL COMMENT '工单标题',
    `description` TEXT NOT NULL COMMENT '工单描述',
    `user_name` VARCHAR(100) DEFAULT NULL COMMENT '用户姓名',
    `assigned_to` VARCHAR(100) DEFAULT NULL COMMENT '处理人',
    `resolved_at` TIMESTAMP NULL DEFAULT NULL COMMENT '解决时间',
    `closed_at` TIMESTAMP NULL DEFAULT NULL COMMENT '关闭时间',
    `emotion` VARCHAR(50) DEFAULT NULL COMMENT '检测到的情绪',
    `emotion_intensity` INT DEFAULT NULL COMMENT '情绪强度 1-10',
    `intent` VARCHAR(50) DEFAULT NULL COMMENT '用户意图',
    `extra_data` JSON DEFAULT NULL COMMENT '额外元数据',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_ticket_uuid` (`ticket_uuid`),
    KEY `idx_user_status` (`user_id`, `status`),
    KEY `idx_priority` (`priority`),
    KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服工单表';

-- ============================================================
-- 2. 客服工单消息表
-- ============================================================
CREATE TABLE IF NOT EXISTS `kefu_ticket_messages` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    `ticket_id` BIGINT NOT NULL COMMENT '工单ID',
    `role` VARCHAR(20) NOT NULL COMMENT '发送者: user/agent/system',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `msg_metadata` JSON DEFAULT NULL COMMENT '消息元数据',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `idx_ticket_created` (`ticket_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服工单消息表';

-- ============================================================
-- 3. 客服转人工记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS `kefu_escalations` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '转人工ID',
    `escalation_uuid` VARCHAR(36) NOT NULL COMMENT '转人工UUID',
    `session_id` VARCHAR(36) DEFAULT NULL COMMENT '客服会话ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `reason` VARCHAR(200) NOT NULL COMMENT '转人工原因',
    `context_summary` TEXT DEFAULT NULL COMMENT '上下文摘要',
    `emotion_type` VARCHAR(50) DEFAULT NULL COMMENT '情绪类型',
    `priority` VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT '优先级',
    `status` ENUM('waiting','assigned','handling','resolved','cancelled')
        NOT NULL DEFAULT 'waiting' COMMENT '转人工状态',
    `assigned_agent` VARCHAR(100) DEFAULT NULL COMMENT '分配的客服',
    `assigned_at` TIMESTAMP NULL DEFAULT NULL COMMENT '分配时间',
    `resolved_at` TIMESTAMP NULL DEFAULT NULL COMMENT '解决时间',
    `extra_data` TEXT DEFAULT NULL COMMENT '额外元数据(JSON)',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_escalation_uuid` (`escalation_uuid`),
    KEY `idx_user_status` (`user_id`, `status`),
    KEY `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服转人工记录表';

-- ============================================================
-- 4. 客服会话表
-- ============================================================
CREATE TABLE IF NOT EXISTS `kefu_conversations` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '会话ID',
    `session_id` VARCHAR(36) NOT NULL COMMENT '会话UUID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `status` ENUM('active','archived','deleted') NOT NULL DEFAULT 'active' COMMENT '会话状态',
    `title` VARCHAR(200) NOT NULL DEFAULT '新会话' COMMENT '会话标题',
    `user_name` VARCHAR(100) DEFAULT NULL COMMENT '用户姓名',
    `message_count` INT NOT NULL DEFAULT 0 COMMENT '消息数量',
    `emotion_type` VARCHAR(50) DEFAULT NULL COMMENT '最近情绪',
    `intent_type` VARCHAR(50) DEFAULT NULL COMMENT '最近意图',
    `extra_data` JSON DEFAULT NULL COMMENT '额外元数据',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_session_id` (`session_id`),
    KEY `idx_user_status` (`user_id`, `status`),
    KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服会话表';

-- ============================================================
-- 5. 客服消息表
-- ============================================================
CREATE TABLE IF NOT EXISTS `kefu_messages` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    `conversation_id` BIGINT NOT NULL COMMENT '会话ID',
    `role` VARCHAR(20) NOT NULL COMMENT '发送者: user/agent/system',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `emotion` VARCHAR(50) DEFAULT NULL COMMENT '情绪类型',
    `emotion_intensity` INT DEFAULT NULL COMMENT '情绪强度',
    `intent` VARCHAR(50) DEFAULT NULL COMMENT '意图类型',
    `confidence` INT DEFAULT NULL COMMENT '置信度 0-100',
    `action` VARCHAR(50) DEFAULT NULL COMMENT '路由动作',
    `metadata` JSON DEFAULT NULL COMMENT '额外元数据',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    PRIMARY KEY (`id`),
    KEY `idx_conv_created` (`conversation_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服消息表';