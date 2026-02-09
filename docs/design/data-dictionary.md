# 数据字典 - AI赋能云平台

**项目**: 内蒙古农畜产品品牌营销AI赋能云平台
**版本**: 1.0
**更新日期**: [项目完成日期]
**数据库**: MySQL 8.0+

## 目录

- [数据库架构](#数据库架构)
- [用户相关表](#用户相关表)
- [企业相关表](#企业相关表)
- [产品相关表](#产品相关表)
- [AI对话相关表](#ai对话相关表)
- [内容生成相关表](#内容生成相关表)
- [关系表](#关系表)
- [字段命名规范](#字段命名规范)

---

## 数据库架构

```
┌─────────────────────────────────────────┐
│         用户和企业管理                   │
├─────────────────────────────────────────┤
│ users (用户表)
│ enterprises (企业表)
│ enterprise_users (企业用户关系表)
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│           内容管理                      │
├─────────────────────────────────────────┤
│ products (产品表)
│ product_certifications (产品认证表)
│ product_tags (产品标签表)
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          AI对话和消息                   │
├─────────────────────────────────────────┤
│ ai_conversations (对话会话表)
│ ai_messages (消息表)
│ content_records (内容生成记录表)
│ generation_templates (生成模板表)
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         配额和计费                      │
├─────────────────────────────────────────┤
│ user_quotas (用户配额表)
└─────────────────────────────────────────┘
```

---

## 用户相关表

### users (用户表)

存储系统中所有用户的账户信息。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY AUTO_INCREMENT | - | 用户ID，系统自增主键 |
| user_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 用户UUID，对外暴露的唯一标识 |
| username | VARCHAR(100) | UNIQUE NOT NULL | - | 用户名，唯一 |
| email | VARCHAR(255) | UNIQUE NOT NULL | - | 邮箱，唯一，用于登录和找回密码 |
| password_hash | VARCHAR(255) | NOT NULL | - | 密码哈希（bcrypt）|
| phone | VARCHAR(20) | NULL | - | 手机号，可用于登录 |
| user_type | ENUM | NOT NULL | 'personal' | 用户类型：personal(个人) / enterprise(企业) |
| role | ENUM | NOT NULL | 'user' | 用户角色：admin / enterprise_admin / user |
| status | ENUM | NOT NULL | 'inactive' | 用户状态：active / inactive / banned / pending |
| real_name | VARCHAR(100) | NULL | - | 真实姓名 |
| avatar_url | VARCHAR(512) | NULL | - | 头像URL |
| bio | TEXT | NULL | - | 个人简介 |
| gender | INT | NULL | 0 | 性别：0(未知) / 1(男) / 2(女) |
| birth_date | DATE | NULL | - | 出生日期 |
| company | VARCHAR(255) | NULL | - | 公司名称 |
| position | VARCHAR(100) | NULL | - | 职位 |
| enterprise_id | BIGINT UNSIGNED | FK enterprises | NULL | 关联企业ID（个人用户可不填） |
| login_count | INT | NOT NULL | 0 | 登录次数 |
| last_login_at | TIMESTAMP | NULL | - | 最后登录时间 |
| email_verified | BOOLEAN | NOT NULL | false | 邮箱是否已验证 |
| email_verified_at | TIMESTAMP | NULL | - | 邮箱验证时间 |
| phone_verified | BOOLEAN | NOT NULL | false | 手机是否已验证 |
| phone_verified_at | TIMESTAMP | NULL | - | 手机验证时间 |
| two_factor_enabled | BOOLEAN | NOT NULL | false | 是否启用双因素认证 |
| api_token | VARCHAR(255) | UNIQUE NULL | - | API访问令牌 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted_at | TIMESTAMP | NULL | - | 软删除时间 |

#### 索引

```sql
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);
CREATE UNIQUE INDEX idx_users_user_uuid ON users(user_uuid);
CREATE INDEX idx_users_enterprise_id ON users(enterprise_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### 业务规则

- 邮箱和用户名唯一
- 密码不少于8个字符，需包含大小写字母、数字、特殊字符
- status为'banned'时用户无法登录
- enterprise_id不为空时用户为企业用户

---

### user_quotas (用户配额表)

存储用户的API调用和内容生成配额限制。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 配额ID |
| user_id | BIGINT UNSIGNED | FK users NOT NULL | - | 用户ID |
| plan_type | VARCHAR(50) | NOT NULL | 'free' | 套餐类型：free / basic / pro / enterprise |
| api_calls_monthly | INT | NOT NULL | 1000 | 月度API调用配额 |
| api_calls_used | INT | NOT NULL | 0 | 已使用的API调用次数 |
| content_generations_monthly | INT | NOT NULL | 100 | 月度内容生成配额 |
| content_generations_used | INT | NOT NULL | 0 | 已使用的内容生成次数 |
| storage_gb | INT | NOT NULL | 1 | 存储空间(GB) |
| storage_used_gb | DECIMAL(10, 2) | NOT NULL | 0.00 | 已使用存储(GB) |
| expires_at | TIMESTAMP | NOT NULL | - | 配额过期时间 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 索引

```sql
CREATE INDEX idx_user_quotas_user_id ON user_quotas(user_id);
CREATE INDEX idx_user_quotas_expires_at ON user_quotas(expires_at);
```

#### 配额配置

| 套餐类型 | API调用 | 内容生成 | 存储空间 | 月费用 |
|---------|--------|--------|---------|--------|
| free | 100 | 10 | 100MB | 0元 |
| basic | 1000 | 100 | 1GB | 99元 |
| pro | 10000 | 1000 | 10GB | 399元 |
| enterprise | 无限 | 无限 | 无限 | 定制 |

---

## 企业相关表

### enterprises (企业表)

存储企业信息和认证状态。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 企业ID |
| enterprise_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 企业UUID |
| name | VARCHAR(255) | NOT NULL | - | 企业名称 |
| license_number | VARCHAR(100) | UNIQUE NOT NULL | - | 营业执照号 |
| industry | VARCHAR(100) | NOT NULL | - | 行业类别 |
| scale | ENUM | NOT NULL | 'small' | 企业规模：micro / small / medium / large |
| website | VARCHAR(255) | NULL | - | 企业网站 |
| phone | VARCHAR(20) | NOT NULL | - | 企业电话 |
| address | VARCHAR(512) | NOT NULL | - | 企业地址 |
| province | VARCHAR(50) | NOT NULL | - | 省份 |
| city | VARCHAR(50) | NOT NULL | - | 城市 |
| district | VARCHAR(50) | NULL | - | 区县 |
| latitude | DECIMAL(10, 8) | NULL | - | 纬度 |
| longitude | DECIMAL(11, 8) | NULL | - | 经度 |
| logo_url | VARCHAR(512) | NULL | - | 企业logo |
| description | TEXT | NULL | - | 企业简介 |
| founded_year | INT | NULL | - | 成立年份 |
| employee_count | INT | NULL | - | 员工数 |
| annual_revenue | VARCHAR(50) | NULL | - | 年营收 |
| verify_status | ENUM | NOT NULL | 'pending' | 认证状态：pending / verified / rejected |
| verify_documents | JSON | NULL | - | 认证文件存储位置 |
| verified_at | TIMESTAMP | NULL | - | 认证时间 |
| reject_reason | TEXT | NULL | - | 拒绝原因 |
| subscription_plan | ENUM | NOT NULL | 'free' | 订阅套餐：free / basic / pro / enterprise |
| plan_expires_at | TIMESTAMP | NOT NULL | - | 套餐过期时间 |
| product_count | INT | NOT NULL | 0 | 产品数量 |
| user_count | INT | NOT NULL | 1 | 用户数量 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted_at | TIMESTAMP | NULL | - | 软删除时间 |

#### 索引

```sql
CREATE UNIQUE INDEX idx_enterprises_license ON enterprises(license_number);
CREATE INDEX idx_enterprises_verify_status ON enterprises(verify_status);
CREATE INDEX idx_enterprises_subscription_plan ON enterprises(subscription_plan);
CREATE INDEX idx_enterprises_province ON enterprises(province);
```

---

## 产品相关表

### products (产品表)

存储产品的详细信息。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 产品ID |
| product_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 产品UUID |
| enterprise_id | BIGINT UNSIGNED | FK enterprises NOT NULL | - | 企业ID |
| name | VARCHAR(255) | NOT NULL | - | 产品名称 |
| category | VARCHAR(100) | NOT NULL | - | 产品分类 |
| sub_category | VARCHAR(100) | NULL | - | 子分类 |
| description | TEXT | NOT NULL | - | 产品描述 |
| short_description | VARCHAR(512) | NULL | - | 简短描述（用于列表展示） |
| cover_image_url | VARCHAR(512) | NULL | - | 封面图片 |
| gallery_images | JSON | NULL | - | 图片库URL列表 |
| origin_province | VARCHAR(50) | NOT NULL | - | 产地省份 |
| origin_city | VARCHAR(50) | NOT NULL | - | 产地城市 |
| origin_district | VARCHAR(50) | NULL | - | 产地区县 |
| origin_latitude | DECIMAL(10, 8) | NULL | - | 产地纬度 |
| origin_longitude | DECIMAL(11, 8) | NULL | - | 产地经度 |
| production_year | INT | NULL | - | 生产年份 |
| harvest_season | VARCHAR(50) | NULL | - | 采收季节 |
| cultural_story | TEXT | NULL | - | 文化故事 |
| cultural_tags | JSON | NULL | - | 文化标签 |
| certifications | JSON | NULL | - | 认证信息（地理标志、有机等） |
| price | DECIMAL(10, 2) | NULL | - | 产品价格（如果销售） |
| price_currency | VARCHAR(10) | NULL | 'CNY' | 价格货币 |
| unit | VARCHAR(50) | NULL | - | 计量单位 |
| inventory | INT | NULL | 0 | 库存 |
| status | ENUM | NOT NULL | 'draft' | 状态：draft / pending / published / offline |
| view_count | INT | NOT NULL | 0 | 浏览次数 |
| generation_count | INT | NOT NULL | 0 | AI生成内容次数 |
| favorite_count | INT | NOT NULL | 0 | 收藏次数 |
| rating_average | DECIMAL(3, 2) | NOT NULL | 0.00 | 平均评分 |
| rating_count | INT | NOT NULL | 0 | 评分数量 |
| seo_title | VARCHAR(255) | NULL | - | SEO标题 |
| seo_keywords | VARCHAR(512) | NULL | - | SEO关键词 |
| seo_description | VARCHAR(512) | NULL | - | SEO描述 |
| published_at | TIMESTAMP | NULL | - | 发布时间 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted_at | TIMESTAMP | NULL | - | 软删除时间 |

#### 索引

```sql
CREATE UNIQUE INDEX idx_products_uuid ON products(product_uuid);
CREATE INDEX idx_products_enterprise_id ON products(enterprise_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_origin_province ON products(origin_province);
CREATE INDEX idx_products_created_at ON products(created_at);
```

---

## AI对话相关表

### ai_conversations (对话会话表)

存储AI对话的会话信息。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 对话ID |
| conversation_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 对话UUID |
| user_id | BIGINT UNSIGNED | FK users NOT NULL | - | 用户ID |
| product_id | BIGINT UNSIGNED | FK products NULL | - | 关联的产品ID（可选） |
| title | VARCHAR(255) | NOT NULL | - | 对话标题 |
| agent_type | ENUM | NOT NULL | 'general' | Agent类型：marketing / cultural / data / general |
| context | TEXT | NULL | - | 对话上下文 |
| system_prompt | TEXT | NULL | - | 系统提示词 |
| total_tokens | INT | NOT NULL | 0 | 使用的总token数 |
| cost_usd | DECIMAL(10, 4) | NOT NULL | 0.0000 | 成本（美元） |
| message_count | INT | NOT NULL | 0 | 消息数量 |
| status | ENUM | NOT NULL | 'active' | 状态：active / archived / deleted |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| archived_at | TIMESTAMP | NULL | - | 归档时间 |

#### 索引

```sql
CREATE INDEX idx_conversations_user_id ON ai_conversations(user_id);
CREATE INDEX idx_conversations_product_id ON ai_conversations(product_id);
CREATE INDEX idx_conversations_agent_type ON ai_conversations(agent_type);
CREATE INDEX idx_conversations_created_at ON ai_conversations(created_at);
```

### ai_messages (消息表)

存储AI对话中的单条消息。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 消息ID |
| message_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 消息UUID |
| conversation_id | BIGINT UNSIGNED | FK ai_conversations NOT NULL | - | 对话ID |
| role | VARCHAR(50) | NOT NULL | - | 消息角色：user / assistant / system |
| content | TEXT | NOT NULL | - | 消息内容 |
| content_type | ENUM | NOT NULL | 'text' | 内容类型：text / image / file |
| attachments | JSON | NULL | - | 附件信息 |
| tokens_used | INT | NOT NULL | 0 | 该消息使用的token数 |
| model | VARCHAR(100) | NULL | - | 使用的模型（如deepseek-chat） |
| response_time_ms | INT | NULL | - | 响应耗时（毫秒） |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |

#### 索引

```sql
CREATE INDEX idx_messages_conversation_id ON ai_messages(conversation_id);
CREATE INDEX idx_messages_role ON ai_messages(role);
CREATE INDEX idx_messages_created_at ON ai_messages(created_at);
```

---

## 内容生成相关表

### content_records (内容生成记录表)

记录每一次内容生成操作（文案、脚本等）。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 记录ID |
| record_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 记录UUID |
| user_id | BIGINT UNSIGNED | FK users NOT NULL | - | 用户ID |
| product_id | BIGINT UNSIGNED | FK products NULL | - | 产品ID |
| template_id | BIGINT UNSIGNED | FK generation_templates NULL | - | 模板ID |
| content_type | VARCHAR(100) | NOT NULL | - | 内容类型：文案 / 短视频脚本 / 直播脚本等 |
| input_data | JSON | NOT NULL | - | 输入参数 |
| generated_content | LONGTEXT | NOT NULL | - | 生成的内容 |
| language | VARCHAR(50) | NOT NULL | 'zh-CN' | 语言代码 |
| tone | VARCHAR(50) | NULL | - | 风格：正式 / 活泼 / 专业等 |
| model | VARCHAR(100) | NOT NULL | - | 使用的模型 |
| tokens_used | INT | NOT NULL | 0 | 使用的token数 |
| cost_usd | DECIMAL(10, 4) | NOT NULL | 0.0000 | 成本（美元） |
| quality_score | DECIMAL(3, 2) | NULL | - | 质量评分（0-1） |
| is_approved | BOOLEAN | NOT NULL | false | 是否被用户接受 |
| is_published | BOOLEAN | NOT NULL | false | 是否已发布 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

#### 索引

```sql
CREATE INDEX idx_content_records_user_id ON content_records(user_id);
CREATE INDEX idx_content_records_product_id ON content_records(product_id);
CREATE INDEX idx_content_records_content_type ON content_records(content_type);
CREATE INDEX idx_content_records_created_at ON content_records(created_at);
```

### generation_templates (生成模板表)

存储内容生成模板。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 模板ID |
| template_uuid | VARCHAR(36) | UNIQUE NOT NULL | UUID() | 模板UUID |
| name | VARCHAR(255) | NOT NULL | - | 模板名称 |
| description | TEXT | NULL | - | 模板描述 |
| content_type | VARCHAR(100) | NOT NULL | - | 内容类型 |
| category | VARCHAR(100) | NOT NULL | - | 分类 |
| prompt_template | LONGTEXT | NOT NULL | - | 提示词模板（包含{变量}） |
| parameters | JSON | NOT NULL | - | 参数定义 |
| examples | JSON | NULL | - | 示例 |
| is_active | BOOLEAN | NOT NULL | true | 是否激活 |
| usage_count | INT | NOT NULL | 0 | 使用次数 |
| created_by | BIGINT UNSIGNED | FK users NOT NULL | - | 创建者ID |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

---

## 关系表

### enterprise_users (企业用户关系表)

定义用户与企业的关系。

#### 表结构

| 字段名 | 数据类型 | 约束 | 默认值 | 说明 |
|--------|---------|------|--------|------|
| id | BIGINT UNSIGNED | PRIMARY KEY | - | 关系ID |
| enterprise_id | BIGINT UNSIGNED | FK enterprises NOT NULL | - | 企业ID |
| user_id | BIGINT UNSIGNED | FK users NOT NULL | - | 用户ID |
| role | VARCHAR(50) | NOT NULL | 'member' | 角色：admin / member |
| joined_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 加入时间 |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |

#### 索引和约束

```sql
CREATE UNIQUE INDEX idx_enterprise_users_unique ON enterprise_users(enterprise_id, user_id);
CREATE INDEX idx_enterprise_users_enterprise_id ON enterprise_users(enterprise_id);
CREATE INDEX idx_enterprise_users_user_id ON enterprise_users(user_id);
```

---

## 字段命名规范

### 通用规范

| 规范 | 示例 | 说明 |
|------|------|------|
| 主键 | id | 递增整数主键 |
| UUID标识 | {table}_uuid | 对外暴露的唯一标识 |
| 外键 | {table}_id | 指向其他表的主键 |
| 时间戳 | created_at / updated_at / deleted_at | 使用TIMESTAMP和UTC |
| 计数器 | count / {type}_count | 统计相关字段 |
| 状态 | status / {name}_status | ENUM类型 |
| 布尔值 | is_{adjective} | 布尔值前缀is_ |
| URL | {name}_url | 资源URL |
| JSON | {name}_data / {name}_info | 灵活数据存储 |

### 数据类型选择

| 用途 | 数据类型 | 约束 | 示例 |
|------|---------|------|------|
| 用户ID | BIGINT UNSIGNED | PRIMARY KEY | 自增 |
| UUID | VARCHAR(36) | UNIQUE | UUID() |
| 用户名/邮箱 | VARCHAR(100/255) | UNIQUE NOT NULL | - |
| 密码 | VARCHAR(255) | NOT NULL | bcrypt hash |
| 金额 | DECIMAL(10, 2) | NOT NULL | 99.99 |
| 百分比/评分 | DECIMAL(3, 2) | 0-1 or 0-100 | 3.50 |
| 坐标 | DECIMAL(10/11, 8) | 纬度/经度 | 39.90469, 116.40516 |
| 大文本 | TEXT / LONGTEXT | - | 1000+ 字符 |
| JSON数据 | JSON | - | {"key": "value"} |
| 布尔值 | BOOLEAN / TINYINT(1) | - | true/false |
| 时间戳 | TIMESTAMP | - | CURRENT_TIMESTAMP |

---

## 常用查询示例

### 查询用户及其企业信息

```sql
SELECT u.*, e.name AS enterprise_name
FROM users u
LEFT JOIN enterprises e ON u.enterprise_id = e.id
WHERE u.user_uuid = ?
  AND u.deleted_at IS NULL;
```

### 查询企业的所有产品

```sql
SELECT p.*
FROM products p
WHERE p.enterprise_id = ?
  AND p.status = 'published'
  AND p.deleted_at IS NULL
ORDER BY p.created_at DESC;
```

### 查询用户的对话历史

```sql
SELECT c.*, COUNT(m.id) AS message_count
FROM ai_conversations c
LEFT JOIN ai_messages m ON c.id = m.conversation_id
WHERE c.user_id = ?
  AND c.status != 'deleted'
GROUP BY c.id
ORDER BY c.created_at DESC
LIMIT 20;
```

### 查询内容生成统计

```sql
SELECT
  content_type,
  COUNT(*) AS count,
  SUM(tokens_used) AS total_tokens,
  SUM(cost_usd) AS total_cost
FROM content_records
WHERE user_id = ?
  AND DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY content_type;
```

---

## 数据库迁移

所有表都通过Alembic进行版本管理，迁移文件位置：

```
backend/alembic/versions/
```

执行迁移：

```bash
# 升级到最新版本
alembic upgrade head

# 查看待执行的迁移
alembic current
alembic upgrade --sql head

# 回滚到上一个版本
alembic downgrade -1
```

---

## 备份和恢复

### MySQL备份

```bash
# 完整备份
mysqldump -u root -p ai_platform > backup-full.sql

# 备份特定表
mysqldump -u root -p ai_platform users products > backup-users-products.sql

# 恢复
mysql -u root -p ai_platform < backup-full.sql
```

### 恢复单个表

```bash
# 从备份恢复单个表
mysql -u root -p ai_platform < backup-users-products.sql --tables users
```

---

## 数据安全和合规

- 敏感数据：密码、密钥使用加密存储
- 个人数据：用户邮箱、手机号等支持PII删除
- 软删除：使用deleted_at字段，允许恢复
- 审计：涉及关键操作的字段提供created_at、updated_at
- 时区：所有时间戳使用UTC存储

---

**文档维护**: dctx479
**最后更新**: [项目完成日期]
**下一个更新**: 添加新表时
