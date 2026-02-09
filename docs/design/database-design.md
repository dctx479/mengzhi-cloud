# 数据库详细设计

> **文档版本**: v1.0  
> **更新日期**: [项目完成日期]  
> **适用项目**: 内蒙古农畜产品品牌营销AI赋能云平台

---

## 目录

1. [数据库架构概述](#1-数据库架构概述)
2. [MySQL数据库设计](#2-mysql数据库设计)
3. [Neo4j知识图谱Schema](#3-neo4j知识图谱schema)
4. [Qdrant向量数据库设计](#4-qdrant向量数据库设计)
5. [Redis缓存设计](#5-redis缓存设计)
6. [数据字典](#6-数据字典)

---

## 1. 数据库架构概述

### 1.1 多数据库架构

本系统采用多数据库混合架构：

| 数据库 | 版本 | 用途 | 选型理由 |
|--------|------|------|----------|
| MySQL | 8.0+ | 核心业务数据 | 成熟稳定，事务支持 |
| Neo4j | 5.0+ | 知识图谱存储 | 图查询高效 |
| Qdrant | 1.7+ | 向量语义检索 | 高性能向量搜索 |
| Redis | 7.0+ | 缓存和会话 | 高性能，数据结构丰富 |

---

## 2. MySQL数据库设计

### 2.1 数据库配置

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_marketing_platform
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ai_marketing_platform;

-- 设置时区
SET GLOBAL time_zone = '+08:00';
SET time_zone = '+08:00';
```

### 2.2 核心表结构（8张表）

#### 2.2.1 users - 用户表

```sql
CREATE TABLE users (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID，主键自增',
    user_uuid VARCHAR(36) NOT NULL COMMENT '用户UUID，对外暴露的唯一标识',
    username VARCHAR(50) NOT NULL COMMENT '用户名，唯一',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱地址',
    phone VARCHAR(20) DEFAULT NULL COMMENT '手机号码',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值(bcrypt)',
    
    -- 用户类型与状态
    user_type ENUM('personal', 'enterprise') NOT NULL DEFAULT 'personal' COMMENT '用户类型：personal个人/enterprise企业',
    status ENUM('active', 'inactive', 'banned', 'pending') NOT NULL DEFAULT 'pending' COMMENT '账号状态',
    role VARCHAR(50) NOT NULL DEFAULT 'user' COMMENT '用户角色：admin/enterprise_admin/user',
    
    -- 企业关联
    enterprise_id BIGINT UNSIGNED DEFAULT NULL COMMENT '所属企业ID',
    
    -- 第三方登录
    wechat_openid VARCHAR(100) DEFAULT NULL COMMENT '微信OpenID',
    wechat_unionid VARCHAR(100) DEFAULT NULL COMMENT '微信UnionID',
    douyin_openid VARCHAR(100) DEFAULT NULL COMMENT '抖音OpenID',
    
    -- 用户资料
    nickname VARCHAR(100) DEFAULT NULL COMMENT '昵称',
    avatar_url VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    gender TINYINT UNSIGNED DEFAULT 0 COMMENT '性别：0未知/1男/2女',
    
    -- 安全相关
    login_attempts INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '登录失败次数',
    locked_until TIMESTAMP NULL DEFAULT NULL COMMENT '账号锁定截止时间',
    last_login_at TIMESTAMP NULL DEFAULT NULL COMMENT '最后登录时间',
    last_login_ip VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP',
    password_changed_at TIMESTAMP NULL DEFAULT NULL COMMENT '密码修改时间',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    
    -- 唯一约束
    UNIQUE KEY uk_user_uuid (user_uuid),
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    UNIQUE KEY uk_phone (phone),
    UNIQUE KEY uk_wechat_openid (wechat_openid),
    UNIQUE KEY uk_douyin_openid (douyin_openid),
    
    -- 索引
    INDEX idx_user_type (user_type),
    INDEX idx_status (status),
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_created_at (created_at),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

#### 2.2.2 enterprises - 企业表

```sql
CREATE TABLE enterprises (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '企业ID',
    enterprise_uuid VARCHAR(36) NOT NULL COMMENT '企业UUID',
    
    -- 基本信息
    name VARCHAR(200) NOT NULL COMMENT '企业名称',
    short_name VARCHAR(100) DEFAULT NULL COMMENT '企业简称',
    license_no VARCHAR(50) NOT NULL COMMENT '营业执照号',
    license_image_url VARCHAR(500) DEFAULT NULL COMMENT '营业执照图片URL',
    
    -- 联系信息
    contact_name VARCHAR(50) DEFAULT NULL COMMENT '联系人姓名',
    contact_phone VARCHAR(20) DEFAULT NULL COMMENT '联系人电话',
    contact_email VARCHAR(100) DEFAULT NULL COMMENT '联系人邮箱',
    
    -- 地址信息
    province VARCHAR(50) DEFAULT NULL COMMENT '省份',
    city VARCHAR(50) DEFAULT NULL COMMENT '城市',
    district VARCHAR(50) DEFAULT NULL COMMENT '区县',
    address VARCHAR(500) DEFAULT NULL COMMENT '详细地址',
    
    -- 企业详情
    industry VARCHAR(100) DEFAULT NULL COMMENT '所属行业',
    scale ENUM('micro', 'small', 'medium', 'large') DEFAULT 'small' COMMENT '企业规模',
    description TEXT DEFAULT NULL COMMENT '企业简介',
    logo_url VARCHAR(500) DEFAULT NULL COMMENT '企业Logo URL',
    website VARCHAR(200) DEFAULT NULL COMMENT '企业官网',
    
    -- 认证状态
    verify_status ENUM('pending', 'verified', 'rejected') NOT NULL DEFAULT 'pending' COMMENT '认证状态',
    verified_at TIMESTAMP NULL DEFAULT NULL COMMENT '认证通过时间',
    reject_reason VARCHAR(500) DEFAULT NULL COMMENT '拒绝原因',
    
    -- 套餐信息
    plan_type ENUM('free', 'basic', 'pro', 'enterprise') NOT NULL DEFAULT 'free' COMMENT '套餐类型',
    plan_expires_at TIMESTAMP NULL DEFAULT NULL COMMENT '套餐到期时间',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    
    -- 唯一约束
    UNIQUE KEY uk_enterprise_uuid (enterprise_uuid),
    UNIQUE KEY uk_license_no (license_no),
    
    -- 索引
    INDEX idx_name (name),
    INDEX idx_verify_status (verify_status),
    INDEX idx_plan_type (plan_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业表';
```

#### 2.2.3 products - 产品表

```sql
CREATE TABLE products (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '产品ID',
    product_uuid VARCHAR(36) NOT NULL COMMENT '产品UUID',
    
    -- 基本信息
    name VARCHAR(200) NOT NULL COMMENT '产品名称',
    short_name VARCHAR(100) DEFAULT NULL COMMENT '产品简称',
    category VARCHAR(100) NOT NULL COMMENT '产品类别',
    sub_category VARCHAR(100) DEFAULT NULL COMMENT '产品子类别',
    
    -- 产地信息
    origin_province VARCHAR(50) NOT NULL COMMENT '产地省份',
    origin_city VARCHAR(50) DEFAULT NULL COMMENT '产地城市',
    origin_district VARCHAR(50) DEFAULT NULL COMMENT '产地区县',
    origin_detail VARCHAR(500) DEFAULT NULL COMMENT '产地详情',
    latitude DECIMAL(10, 7) DEFAULT NULL COMMENT '产地纬度',
    longitude DECIMAL(10, 7) DEFAULT NULL COMMENT '产地经度',
    
    -- 产品详情
    description TEXT DEFAULT NULL COMMENT '产品描述',
    features TEXT DEFAULT NULL COMMENT '产品特点(JSON数组)',
    specifications TEXT DEFAULT NULL COMMENT '规格参数(JSON对象)',
    nutrition_facts TEXT DEFAULT NULL COMMENT '营养成分(JSON对象)',
    
    -- 认证信息
    certification_type VARCHAR(100) DEFAULT NULL COMMENT '认证类型：地理标志/绿色食品/有机认证',
    certification_no VARCHAR(100) DEFAULT NULL COMMENT '认证编号',
    certification_date DATE DEFAULT NULL COMMENT '认证日期',
    certification_expires DATE DEFAULT NULL COMMENT '认证有效期',
    
    -- 文化标签
    cultural_tags JSON DEFAULT NULL COMMENT '文化标签数组',
    cultural_story TEXT DEFAULT NULL COMMENT '文化故事',
    historical_origin TEXT DEFAULT NULL COMMENT '历史渊源',
    
    -- 媒体资源
    main_image_url VARCHAR(500) DEFAULT NULL COMMENT '主图URL',
    image_urls JSON DEFAULT NULL COMMENT '图片URL数组',
    video_url VARCHAR(500) DEFAULT NULL COMMENT '视频URL',
    
    -- 状态与统计
    status ENUM('draft', 'pending', 'published', 'offline') NOT NULL DEFAULT 'draft' COMMENT '产品状态',
    view_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览次数',
    generate_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '内容生成次数',
    
    -- 关联
    enterprise_id BIGINT UNSIGNED DEFAULT NULL COMMENT '所属企业ID',
    created_by BIGINT UNSIGNED NOT NULL COMMENT '创建人用户ID',
    
    -- 时间戳
    published_at TIMESTAMP NULL DEFAULT NULL COMMENT '发布时间',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
    
    -- 唯一约束
    UNIQUE KEY uk_product_uuid (product_uuid),
    
    -- 索引
    INDEX idx_name (name),
    INDEX idx_category (category),
    INDEX idx_origin_province (origin_province),
    INDEX idx_origin_city (origin_city),
    INDEX idx_certification_type (certification_type),
    INDEX idx_status (status),
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    
    -- 全文索引
    FULLTEXT INDEX ft_name_description (name, description) WITH PARSER ngram,
    
    -- 外键
    CONSTRAINT fk_products_enterprise FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE SET NULL,
    CONSTRAINT fk_products_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='产品表';
```

#### 2.2.4 content_records - 内容生成记录表

```sql
CREATE TABLE content_records (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',
    record_uuid VARCHAR(36) NOT NULL COMMENT '记录UUID',
    
    -- 关联信息
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    product_id BIGINT UNSIGNED DEFAULT NULL COMMENT '产品ID',
    conversation_id BIGINT UNSIGNED DEFAULT NULL COMMENT '关联对话ID',
    
    -- 生成配置
    content_type ENUM('copy', 'script', 'video_copy', 'slogan', 'story') NOT NULL COMMENT '内容类型',
    platform ENUM('douyin', 'xiaohongshu', 'wechat', 'weibo', 'kuaishou', 'general') NOT NULL DEFAULT 'general' COMMENT '目标平台',
    style ENUM('formal', 'casual', 'humorous', 'emotional', 'professional') DEFAULT 'casual' COMMENT '风格',
    length_type ENUM('short', 'medium', 'long') DEFAULT 'medium' COMMENT '长度类型',
    
    -- 输入参数
    input_params JSON NOT NULL COMMENT '输入参数(JSON)',
    keywords JSON DEFAULT NULL COMMENT '关键词数组',
    
    -- 生成结果
    generated_content TEXT NOT NULL COMMENT '生成的内容',
    edited_content TEXT DEFAULT NULL COMMENT '用户编辑后的内容',
    
    -- AI调用信息
    model_name VARCHAR(100) DEFAULT NULL COMMENT '使用的模型名称',
    prompt_tokens INT UNSIGNED DEFAULT 0 COMMENT 'Prompt Token数',
    completion_tokens INT UNSIGNED DEFAULT 0 COMMENT '生成Token数',
    total_tokens INT UNSIGNED DEFAULT 0 COMMENT '总Token数',
    generation_time_ms INT UNSIGNED DEFAULT NULL COMMENT '生成耗时(毫秒)',
    
    -- 质量评估
    quality_score DECIMAL(3, 2) DEFAULT NULL COMMENT '质量评分(0-5)',
    user_rating TINYINT UNSIGNED DEFAULT NULL COMMENT '用户评分(1-5)',
    user_feedback TEXT DEFAULT NULL COMMENT '用户反馈',
    
    -- 状态
    status ENUM('generating', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'generating' COMMENT '状态',
    error_message TEXT DEFAULT NULL COMMENT '错误信息',
    
    -- 使用统计
    copy_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '复制次数',
    export_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '导出次数',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束
    UNIQUE KEY uk_record_uuid (record_uuid),
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_product_id (product_id),
    INDEX idx_content_type (content_type),
    INDEX idx_platform (platform),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    
    -- 外键
    CONSTRAINT fk_content_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_content_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容生成记录表';
```

#### 2.2.5 ai_conversations - AI对话记录表

```sql
CREATE TABLE ai_conversations (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '对话ID',
    conversation_uuid VARCHAR(36) NOT NULL COMMENT '对话UUID',
    
    -- 关联信息
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    
    -- 对话信息
    title VARCHAR(200) DEFAULT NULL COMMENT '对话标题',
    agent_type ENUM('xiaoshu', 'xiaoshang', 'assistant') NOT NULL DEFAULT 'assistant' COMMENT 'AI代理类型',
    
    -- 上下文
    context_product_id BIGINT UNSIGNED DEFAULT NULL COMMENT '上下文产品ID',
    context_data JSON DEFAULT NULL COMMENT '其他上下文数据',
    
    -- 统计
    message_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '消息数量',
    total_tokens INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '总Token消耗',
    
    -- 状态
    status ENUM('active', 'archived', 'deleted') NOT NULL DEFAULT 'active' COMMENT '对话状态',
    
    -- 时间戳
    last_message_at TIMESTAMP NULL DEFAULT NULL COMMENT '最后消息时间',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束
    UNIQUE KEY uk_conversation_uuid (conversation_uuid),
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_status (status),
    INDEX idx_last_message_at (last_message_at),
    INDEX idx_created_at (created_at),
    
    -- 外键
    CONSTRAINT fk_conversation_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_conversation_product FOREIGN KEY (context_product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话记录表';
```

#### 2.2.6 ai_messages - AI对话消息表

```sql
CREATE TABLE ai_messages (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    message_uuid VARCHAR(36) NOT NULL COMMENT '消息UUID',
    
    -- 关联信息
    conversation_id BIGINT UNSIGNED NOT NULL COMMENT '对话ID',
    
    -- 消息内容
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色：user用户/assistant助手/system系统',
    content TEXT NOT NULL COMMENT '消息内容',
    content_type ENUM('text', 'image', 'audio', 'file') NOT NULL DEFAULT 'text' COMMENT '内容类型',
    
    -- 附件信息
    attachments JSON DEFAULT NULL COMMENT '附件信息数组',
    
    -- Token统计
    prompt_tokens INT UNSIGNED DEFAULT 0 COMMENT 'Prompt Token数',
    completion_tokens INT UNSIGNED DEFAULT 0 COMMENT '生成Token数',
    
    -- 引用的知识
    referenced_knowledge JSON DEFAULT NULL COMMENT 'RAG引用的知识片段',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    -- 唯一约束
    UNIQUE KEY uk_message_uuid (message_uuid),
    
    -- 索引
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_role (role),
    INDEX idx_created_at (created_at),
    
    -- 外键
    CONSTRAINT fk_message_conversation FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话消息表';
```

#### 2.2.7 user_quotas - 用户配额表

```sql
CREATE TABLE user_quotas (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '配额ID',
    
    -- 关联信息
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    
    -- 配额类型
    quota_type ENUM('daily', 'monthly', 'total') NOT NULL DEFAULT 'daily' COMMENT '配额类型',
    
    -- AI对话配额
    chat_limit INT UNSIGNED NOT NULL DEFAULT 50 COMMENT '对话次数限制',
    chat_used INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已使用对话次数',
    
    -- 内容生成配额
    generation_limit INT UNSIGNED NOT NULL DEFAULT 20 COMMENT '生成次数限制',
    generation_used INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已使用生成次数',
    
    -- Token配额
    token_limit INT UNSIGNED NOT NULL DEFAULT 100000 COMMENT 'Token限制',
    token_used INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已使用Token',
    
    -- 存储配额
    storage_limit_mb INT UNSIGNED NOT NULL DEFAULT 100 COMMENT '存储空间限制(MB)',
    storage_used_mb INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已使用存储(MB)',
    
    -- 配额周期
    period_start DATE NOT NULL COMMENT '配额周期开始日期',
    period_end DATE NOT NULL COMMENT '配额周期结束日期',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束（同一用户同一类型同一周期只有一条记录）
    UNIQUE KEY uk_user_quota_period (user_id, quota_type, period_start),
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_quota_type (quota_type),
    INDEX idx_period_end (period_end),
    
    -- 外键
    CONSTRAINT fk_quota_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户配额表';
```

#### 2.2.8 generation_templates - 生成模板表

```sql
CREATE TABLE generation_templates (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '模板ID',
    template_uuid VARCHAR(36) NOT NULL COMMENT '模板UUID',
    
    -- 基本信息
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description TEXT DEFAULT NULL COMMENT '模板描述',
    
    -- 分类
    content_type ENUM('copy', 'script', 'video_copy', 'slogan', 'story') NOT NULL COMMENT '内容类型',
    platform ENUM('douyin', 'xiaohongshu', 'wechat', 'weibo', 'kuaishou', 'general') NOT NULL DEFAULT 'general' COMMENT '适用平台',
    category VARCHAR(100) DEFAULT NULL COMMENT '模板分类',
    
    -- 模板内容
    system_prompt TEXT NOT NULL COMMENT '系统提示词',
    user_prompt_template TEXT NOT NULL COMMENT '用户提示词模板',
    variables JSON NOT NULL COMMENT '变量定义(JSON数组)',
    example_output TEXT DEFAULT NULL COMMENT '示例输出',
    
    -- 配置
    model_config JSON DEFAULT NULL COMMENT '模型配置(temperature等)',
    max_tokens INT UNSIGNED DEFAULT 2000 COMMENT '最大Token数',
    
    -- 状态
    is_system TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否系统模板',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    
    -- 统计
    use_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '使用次数',
    avg_rating DECIMAL(3, 2) DEFAULT NULL COMMENT '平均评分',
    
    -- 创建者
    created_by BIGINT UNSIGNED DEFAULT NULL COMMENT '创建人ID(NULL表示系统)',
    
    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 唯一约束
    UNIQUE KEY uk_template_uuid (template_uuid),
    
    -- 索引
    INDEX idx_content_type (content_type),
    INDEX idx_platform (platform),
    INDEX idx_is_system (is_system),
    INDEX idx_is_active (is_active),
    INDEX idx_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='生成模板表';
```


### 2.3 辅助表

#### 2.3.1 culture_tags - 文化标签表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | BIGINT UNSIGNED | 主键ID |
| name | VARCHAR(50) | 标签名称 |
| category | ENUM | 分类: ethnic/historical/craft/festival/custom/other |
| description | TEXT | 标签描述 |
| parent_id | BIGINT UNSIGNED | 父标签ID |
| level | TINYINT UNSIGNED | 层级 |
| product_count | INT UNSIGNED | 关联产品数 |
| is_active | TINYINT(1) | 是否启用 |

#### 2.3.2 system_configs - 系统配置表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | BIGINT UNSIGNED | 主键ID |
| config_key | VARCHAR(100) | 配置键 |
| config_value | TEXT | 配置值 |
| value_type | ENUM | 值类型: string/number/boolean/json |
| config_group | VARCHAR(50) | 配置分组 |
| is_active | TINYINT(1) | 是否启用 |
| is_public | TINYINT(1) | 是否公开 |

---

## 3. Neo4j知识图谱Schema

### 3.1 节点类型定义

| 节点类型 | 说明 | 主要属性 |
|---------|------|---------|
| Product | 产品节点 | uuid, name, category, description, certification_type, features, cultural_tags |
| Region | 地域节点 | uuid, name, level, code, latitude, longitude, climate |
| Culture | 文化节点 | uuid, name, type, description, origin, period, related_ethnic |
| Ingredient | 原料节点 | uuid, name, type, nutrition, season, origin_regions |
| Craft | 工艺节点 | uuid, name, type, steps, tools, is_intangible_heritage |
| Brand | 品牌节点 | uuid, name, enterprise_uuid, founded_year, slogan |

### 3.2 关系类型定义

| 关系类型 | 说明 | 起点 | 终点 | 属性 |
|---------|------|------|------|------|
| PRODUCED_IN | 产于某地 | Product | Region | since, is_primary, production_scale |
| HAS_CULTURE | 关联文化 | Product | Culture | relevance, aspect, description |
| MADE_FROM | 由原料制成 | Product | Ingredient | proportion, is_main, processing |
| USES_CRAFT | 使用工艺 | Product | Craft | is_core, stage |
| BELONGS_TO | 属于品牌 | Product | Brand | since, is_flagship |
| LOCATED_IN | 位于 | Region | Region | - |
| RELATED_TO | 相关 | Culture | Culture | relation_type, description |
| ORIGINATED_FROM | 起源于 | Craft | Culture | period |


### 3.3 Cypher创建语句示例

**创建约束和索引:**

```cypher
-- 创建约束（确保UUID唯一性）
CREATE CONSTRAINT product_uuid IF NOT EXISTS FOR (p:Product) REQUIRE p.uuid IS UNIQUE;
CREATE CONSTRAINT region_uuid IF NOT EXISTS FOR (r:Region) REQUIRE r.uuid IS UNIQUE;
CREATE CONSTRAINT culture_uuid IF NOT EXISTS FOR (c:Culture) REQUIRE c.uuid IS UNIQUE;
CREATE CONSTRAINT ingredient_uuid IF NOT EXISTS FOR (i:Ingredient) REQUIRE i.uuid IS UNIQUE;
CREATE CONSTRAINT craft_uuid IF NOT EXISTS FOR (cr:Craft) REQUIRE cr.uuid IS UNIQUE;
CREATE CONSTRAINT brand_uuid IF NOT EXISTS FOR (b:Brand) REQUIRE b.uuid IS UNIQUE;

-- 创建索引（加速查询）
CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name);
CREATE INDEX product_category IF NOT EXISTS FOR (p:Product) ON (p.category);
CREATE INDEX region_name IF NOT EXISTS FOR (r:Region) ON (r.name);
CREATE INDEX region_level IF NOT EXISTS FOR (r:Region) ON (r.level);
CREATE INDEX culture_type IF NOT EXISTS FOR (c:Culture) ON (c.type);
CREATE INDEX craft_type IF NOT EXISTS FOR (cr:Craft) ON (cr.type);
```

**创建示例节点:**

```cypher
-- 创建地域节点（省级）
CREATE (nmg:Region {
    uuid: "region_nmg_001",
    name: "内蒙古自治区",
    level: "province",
    code: "150000",
    latitude: 40.8175,
    longitude: 111.7656,
    climate: "温带大陆性气候",
    created_at: datetime()
});

-- 创建地域节点（市级）
CREATE (wlcb:Region {
    uuid: "region_wlcb_001",
    name: "乌兰察布市",
    level: "city",
    code: "150900",
    latitude: 41.0223,
    longitude: 113.1145,
    climate: "温带大陆性季风气候",
    created_at: datetime()
});

-- 创建地域层级关系
CREATE (wlcb)-[:LOCATED_IN]->(nmg);

-- 创建文化节点
CREATE (ngct:Culture {
    uuid: "culture_ngct_001",
    name: "草原农耕传统",
    type: "agricultural",
    description: "内蒙古草原地区独特的农牧结合生产方式",
    origin: "内蒙古自治区",
    period: "近现代",
    related_ethnic: ["蒙古族", "汉族"],
    created_at: datetime()
});

-- 创建产品节点
CREATE (mls:Product {
    uuid: "product_mls_001",
    name: "乌兰察布马铃薯",
    category: "农产品",
    sub_category: "蔬菜",
    description: "乌兰察布市特产马铃薯，口感绵软、淀粉含量高",
    certification_type: "地理标志产品",
    features: ["淀粉含量高", "口感绵软", "绿色无污染"],
    cultural_tags: ["农耕传统", "地域特色"],
    created_at: datetime()
});

-- 创建产品与地域的关系
CREATE (mls)-[:PRODUCED_IN {since: 2006, is_primary: true}]->(wlcb);

-- 创建产品与文化的关系
CREATE (mls)-[:HAS_CULTURE {relevance: 0.8, aspect: "种植历史"}]->(ngct);
```

### 4.4 向量化与插入

```python
import uuid
from datetime import datetime
from typing import List
from openai import OpenAI

openai_client = OpenAI(api_key="your-api-key")

def get_embedding(text: str) -> List[float]:
    """获取文本的向量表示"""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将长文本分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

def insert_product_knowledge(product_uuid, product_name, category, sub_category, content_type, text):
    """插入产品知识向量"""
    chunks = chunk_text(text)
    point_ids = []
    
    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk)
        point_id = str(uuid.uuid4())
        point_ids.append(point_id)
        
        payload = {
            "id": point_id,
            "type": content_type,
            "product_uuid": product_uuid,
            "product_name": product_name,
            "category": category,
            "sub_category": sub_category,
            "chunk_index": i,
            "chunk_total": len(chunks),
            "text": chunk,
            "source": "product_database",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        client.upsert(
            collection_name="product_knowledge",
            points=[{"id": point_id, "vector": vector, "payload": payload}]
        )
    return point_ids
```

### 4.5 向量检索

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

def search_similar_knowledge(query, top_k=5, category_filter=None):
    """语义检索相似知识"""
    query_vector = get_embedding(query)
    
    filter_conditions = []
    if category_filter:
        filter_conditions.append(
            FieldCondition(key="category", match=MatchValue(value=category_filter))
        )
    
    search_filter = Filter(must=filter_conditions) if filter_conditions else None
    
    results = client.search(
        collection_name="product_knowledge",
        query_vector=query_vector,
        query_filter=search_filter,
        limit=top_k,
        with_payload=True,
        score_threshold=0.7
    )
    
    return [{
        "id": hit.id,
        "score": hit.score,
        "text": hit.payload.get("text"),
        "product_name": hit.payload.get("product_name"),
        "category": hit.payload.get("category")
    } for hit in results]
```

---

## 5. Redis缓存设计

### 5.1 Key命名规范

| 业务场景 | Key格式 | 数据类型 | TTL | 说明 |
|---------|---------|----------|-----|------|
| 用户Session | session:{user_id}:{device_id} | Hash | 7天 | 用户会话信息 |
| Token黑名单 | token_blacklist:{jti} | String | Token过期时间 | 已撤销的Token |
| 用户信息缓存 | user:{user_uuid} | Hash | 1小时 | 用户基本信息 |
| 产品信息缓存 | product:{product_uuid} | Hash | 30分钟 | 产品详情 |
| 产品列表缓存 | product_list:{category}:{page} | String(JSON) | 10分钟 | 分页产品列表 |
| 对话上下文 | conversation:{conversation_uuid} | List | 24小时 | AI对话历史 |
| 用户配额 | quota:{user_id}:{date} | Hash | 当日结束 | 每日配额使用 |
| 验证码 | verify_code:{phone}:{type} | String | 5分钟 | 短信验证码 |
| 限流计数 | rate_limit:{user_id}:{api} | String | 1分钟 | API调用限流 |
| 热门产品 | hot_products:{category} | Sorted Set | 1小时 | 热门产品排行 |
| 搜索缓存 | search:{query_hash} | String(JSON) | 15分钟 | 搜索结果缓存 |
| 生成任务状态 | task:{task_id} | Hash | 1小时 | 异步任务状态 |

### 5.2 Python代码实现

```python
import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# 初始化Redis客户端
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True
)

class CacheManager:
    """缓存管理器"""
    
    # ========== 用户Session管理 ==========
    
    @staticmethod
    def set_user_session(user_id: str, device_id: str, session_data: Dict) -> None:
        key = f"session:{user_id}:{device_id}"
        redis_client.hset(key, mapping=session_data)
        redis_client.expire(key, 7 * 24 * 3600)  # 7天
    
    @staticmethod
    def get_user_session(user_id: str, device_id: str) -> Optional[Dict]:
        key = f"session:{user_id}:{device_id}"
        return redis_client.hgetall(key) or None
    
    # ========== Token黑名单管理 ==========
    
    @staticmethod
    def add_token_to_blacklist(jti: str, ttl_seconds: int) -> None:
        key = f"token_blacklist:{jti}"
        redis_client.setex(key, ttl_seconds, "revoked")
    
    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        key = f"token_blacklist:{jti}"
        return redis_client.exists(key) > 0
    
    # ========== 用户信息缓存 ==========
    
    @staticmethod
    def cache_user_info(user_uuid: str, user_data: Dict) -> None:
        key = f"user:{user_uuid}"
        redis_client.hset(key, mapping=user_data)
        redis_client.expire(key, 3600)  # 1小时
    
    @staticmethod
    def get_cached_user_info(user_uuid: str) -> Optional[Dict]:
        key = f"user:{user_uuid}"
        return redis_client.hgetall(key) or None
    
    # ========== 产品信息缓存 ==========
    
    @staticmethod
    def cache_product_info(product_uuid: str, product_data: Dict) -> None:
        key = f"product:{product_uuid}"
        redis_client.hset(key, mapping=product_data)
        redis_client.expire(key, 1800)  # 30分钟
    
    # ========== AI对话上下文 ==========
    
    @staticmethod
    def add_conversation_message(conversation_uuid: str, message: Dict) -> None:
        key = f"conversation:{conversation_uuid}"
        redis_client.rpush(key, json.dumps(message))
        redis_client.expire(key, 24 * 3600)  # 24小时
    
    @staticmethod
    def get_conversation_history(conversation_uuid: str, limit: int = 20) -> List[Dict]:
        key = f"conversation:{conversation_uuid}"
        messages = redis_client.lrange(key, -limit, -1)
        return [json.loads(m) for m in messages]
    
    # ========== 用户配额管理 ==========
    
    @staticmethod
    def increment_quota_usage(user_id: str, quota_type: str, amount: int = 1) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"quota:{user_id}:{today}"
        new_value = redis_client.hincrby(key, quota_type, amount)
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
        ttl = int((tomorrow - datetime.now()).total_seconds())
        redis_client.expire(key, ttl)
        return new_value
    
    # ========== 验证码管理 ==========
    
    @staticmethod
    def set_verification_code(identifier: str, code_type: str, code: str) -> None:
        key = f"verify_code:{identifier}:{code_type}"
        redis_client.setex(key, 300, code)  # 5分钟
    
    @staticmethod
    def verify_code(identifier: str, code_type: str, code: str) -> bool:
        key = f"verify_code:{identifier}:{code_type}"
        stored_code = redis_client.get(key)
        if stored_code and stored_code == code:
            redis_client.delete(key)
            return True
        return False
    
    # ========== 限流管理 ==========
    
    @staticmethod
    def check_rate_limit(user_id: str, api: str, limit: int = 60) -> bool:
        key = f"rate_limit:{user_id}:{api}"
        current = redis_client.incr(key)
        if current == 1:
            redis_client.expire(key, 60)  # 1分钟
        return current <= limit
    
    # ========== 热门产品排行 ==========
    
    @staticmethod
    def increment_product_view(category: str, product_uuid: str) -> None:
        key = f"hot_products:{category}"
        redis_client.zincrby(key, 1, product_uuid)
        redis_client.expire(key, 3600)  # 1小时
    
    @staticmethod
    def get_hot_products(category: str, top_n: int = 10) -> List[str]:
        key = f"hot_products:{category}"
        return redis_client.zrevrange(key, 0, top_n - 1)
```

---

## 6. 数据字典

### 6.1 MySQL表字段详解

#### 6.1.1 users表字段说明

| 字段名 | 类型 | 允许空 | 默认值 | 说明 |
|--------|------|--------|--------|------|
| id | BIGINT UNSIGNED | 否 | AUTO_INCREMENT | 主键ID |
| user_uuid | VARCHAR(36) | 否 | - | 用户UUID，对外唯一标识 |
| username | VARCHAR(50) | 否 | - | 用户名，唯一 |
| email | VARCHAR(100) | 是 | NULL | 邮箱地址 |
| phone | VARCHAR(20) | 是 | NULL | 手机号码 |
| password_hash | VARCHAR(255) | 否 | - | 密码哈希(bcrypt) |
| user_type | ENUM | 否 | personal | 用户类型 |
| status | ENUM | 否 | pending | 账号状态 |
| role | VARCHAR(50) | 否 | user | 用户角色 |
| enterprise_id | BIGINT UNSIGNED | 是 | NULL | 所属企业ID |
| wechat_openid | VARCHAR(100) | 是 | NULL | 微信OpenID |
| wechat_unionid | VARCHAR(100) | 是 | NULL | 微信UnionID |
| douyin_openid | VARCHAR(100) | 是 | NULL | 抖音OpenID |
| nickname | VARCHAR(100) | 是 | NULL | 昵称 |
| avatar_url | VARCHAR(500) | 是 | NULL | 头像URL |
| gender | TINYINT UNSIGNED | 是 | 0 | 性别 |
| login_attempts | INT UNSIGNED | 否 | 0 | 登录失败次数 |
| locked_until | TIMESTAMP | 是 | NULL | 账号锁定截止时间 |
| last_login_at | TIMESTAMP | 是 | NULL | 最后登录时间 |
| last_login_ip | VARCHAR(45) | 是 | NULL | 最后登录IP |
| password_changed_at | TIMESTAMP | 是 | NULL | 密码修改时间 |
| created_at | TIMESTAMP | 否 | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 否 | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 是 | NULL | 软删除时间 |

#### 6.1.2 枚举值说明

**user_type（用户类型）:**
| 值 | 说明 |
|-----|------|
| personal | 个人用户 |
| enterprise | 企业用户 |

**status（账号状态）:**
| 值 | 说明 |
|-----|------|
| active | 正常 |
| inactive | 未激活 |
| banned | 已禁用 |
| pending | 待审核 |

**role（用户角色）:**
| 值 | 说明 |
|-----|------|
| admin | 系统管理员 |
| enterprise_admin | 企业管理员 |
| user | 普通用户 |

**verify_status（认证状态）:**
| 值 | 说明 |
|-----|------|
| pending | 待审核 |
| verified | 已认证 |
| rejected | 已拒绝 |

**plan_type（套餐类型）:**
| 值 | 说明 | 配额 |
|-----|------|------|
| free | 免费版 | 每日50次对话，20次生成 |
| basic | 基础版 | 每日200次对话，100次生成 |
| pro | 专业版 | 每日1000次对话，500次生成 |
| enterprise | 企业版 | 无限制 |

**content_type（内容类型）:**
| 值 | 说明 |
|-----|------|
| copy | 营销文案 |
| script | 直播脚本 |
| video_copy | 短视频文案 |
| slogan | 广告标语 |
| story | 品牌故事 |

**platform（目标平台）:**
| 值 | 说明 |
|-----|------|
| douyin | 抖音 |
| xiaohongshu | 小红书 |
| wechat | 微信公众号 |
| weibo | 微博 |
| kuaishou | 快手 |
| general | 通用 |

**style（内容风格）:**
| 值 | 说明 |
|-----|------|
| formal | 正式 |
| casual | 轻松 |
| humorous | 幽默 |
| emotional | 情感 |
| professional | 专业 |

**agent_type（AI代理类型）:**
| 值 | 说明 |
|-----|------|
| xiaoshu | 小数（数据助手） |
| xiaoshang | 小商（营销助手） |
| assistant | 通用助手 |

