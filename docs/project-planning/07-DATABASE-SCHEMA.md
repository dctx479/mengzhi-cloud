# 数据库设计
## Database Schema v1.0

**文档版本**: 1.0  
**创建日期**: 2026-06-11  
**数据库版本**: PostgreSQL 15 + Redis 7

---

## 一、数据库选型

### 1.1 主数据库: PostgreSQL 15

**选型理由**:
- JSONB支持（存储文化标签/卖点/配置）
- 全文搜索能力（GIN索引）
- 地理位置数据类型（产地经纬度）
- 成熟稳定，社区活跃
- 支持复杂事务

### 1.2 缓存数据库: Redis 7

**用途**:
- LLM响应缓存（TTL 1小时）
- Session存储（JWT Refresh Token）
- 速率限制计数器（滑动窗口）
- 实时排行榜（文化元素热度）

---

## 二、核心表设计

### 2.1 用户与认证

```sql
-- 用户表
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  user_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE,
  phone VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,  -- bcrypt
  user_type VARCHAR(20) DEFAULT 'individual',  -- individual/enterprise
  role VARCHAR(20) DEFAULT 'user',  -- user/admin
  enterprise_id BIGINT,
  avatar_url VARCHAR(500),
  status VARCHAR(20) DEFAULT 'active',  -- active/disabled/deleted
  last_login_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (enterprise_id) REFERENCES enterprises(id),
  INDEX idx_username (username),
  INDEX idx_email (email),
  INDEX idx_enterprise (enterprise_id),
  INDEX idx_status (status)
);

-- 企业表
CREATE TABLE enterprises (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  api_key VARCHAR(64) UNIQUE,  -- 企业API密钥（加密存储）
  api_key_encrypted TEXT,  -- AES-256加密
  quota_limit INT DEFAULT 1000,  -- 月配额
  industry VARCHAR(100),  -- 行业
  contact_person VARCHAR(100),
  contact_phone VARCHAR(20),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- JWT刷新令牌表
CREATE TABLE refresh_tokens (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  token_hash VARCHAR(255) NOT NULL UNIQUE,  -- SHA256哈希
  jti VARCHAR(64) NOT NULL UNIQUE,  -- JWT ID
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_user (user_id),
  INDEX idx_expires (expires_at),
  INDEX idx_jti (jti)
);
```

### 2.2 产品管理

```sql
-- 品类表
CREATE TABLE categories (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_id BIGINT,
  level INT DEFAULT 1,  -- 1=一级, 2=二级
  sort_order INT DEFAULT 0,
  icon_url VARCHAR(500),
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (parent_id) REFERENCES categories(id),
  INDEX idx_parent (parent_id),
  INDEX idx_level (level)
);

-- 产地表
CREATE TABLE origins (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  region VARCHAR(100),  -- 呼伦贝尔/锡林郭勒/鄂尔多斯等
  description TEXT,
  latitude DECIMAL(10,7),
  longitude DECIMAL(10,7),
  cover_image VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_region (region)
);

-- 产品表
CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id BIGINT,
  origin_id BIGINT,
  description TEXT,
  images JSONB,  -- ['url1', 'url2', 'url3']
  selling_points JSONB,  -- ['草原散养', '肉质紧实', '无膻味']
  cultural_tags JSONB,  -- ['那达慕', '手把肉']
  price DECIMAL(10,2),
  stock INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active',  -- active/disabled/out_of_stock
  view_count INT DEFAULT 0,
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (category_id) REFERENCES categories(id),
  FOREIGN KEY (origin_id) REFERENCES origins(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_category (category_id),
  INDEX idx_origin (origin_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at DESC)
);

-- JSONB索引（加速cultural_tags查询）
CREATE INDEX idx_products_cultural_tags ON products USING GIN (cultural_tags);
```

### 2.3 知识图谱

```sql
-- 文化元素表
CREATE TABLE cultural_elements (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  type VARCHAR(50) NOT NULL,  -- festival/skill/food/story/custom/craft
  story TEXT NOT NULL,
  origin_region VARCHAR(100),
  hot_score INT DEFAULT 50,  -- 0-100热度分
  metadata JSONB,  -- {time: '农历六月初四', status: '活态传承'}
  view_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_type (type),
  INDEX idx_hot_score (hot_score DESC),
  INDEX idx_origin_region (origin_region)
);

-- 产品-文化关联表
CREATE TABLE product_culture_links (
  product_id BIGINT NOT NULL,
  culture_id BIGINT NOT NULL,
  relevance_score DECIMAL(3,2) DEFAULT 0.50,  -- 0.00-1.00
  link_type VARCHAR(50) DEFAULT 'manual',  -- manual/auto
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (product_id, culture_id),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (culture_id) REFERENCES cultural_elements(id),
  INDEX idx_product (product_id),
  INDEX idx_culture (culture_id),
  INDEX idx_relevance (relevance_score DESC)
);

-- 产地-文化关联表
CREATE TABLE origin_culture_links (
  origin_id BIGINT NOT NULL,
  culture_id BIGINT NOT NULL,
  strength DECIMAL(3,2) DEFAULT 1.00,  -- 关联强度
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (origin_id, culture_id),
  FOREIGN KEY (origin_id) REFERENCES origins(id),
  FOREIGN KEY (culture_id) REFERENCES cultural_elements(id)
);
```

### 2.4 IP对话记录

```sql
-- IP对话会话表
CREATE TABLE ip_sessions (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) UNIQUE NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20),  -- xiaoshu/xiaoshang
  message_count INT DEFAULT 0,
  total_tokens INT DEFAULT 0,
  started_at TIMESTAMP DEFAULT NOW(),
  last_active_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_session (session_id),
  INDEX idx_user (user_id)
);

-- IP对话消息表
CREATE TABLE ip_conversations (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20) NOT NULL,  -- xiaoshu/xiaoshang
  role VARCHAR(20) NOT NULL,  -- user/assistant
  user_message TEXT,
  ai_response TEXT,
  intent_type VARCHAR(50),  -- product_inquiry/brand_story/live_script
  emotion_type VARCHAR(20),  -- positive/neutral/confused/anxious
  cultural_elements_mentioned JSONB,  -- ['那达慕', '手把肉']
  suggestions JSONB,  -- ['追问1', '追问2']
  input_tokens INT,
  output_tokens INT,
  tokens_used INT,
  latency_ms INT,
  cached BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_session (session_id),
  INDEX idx_user (user_id),
  INDEX idx_ip_type (ip_type),
  INDEX idx_created (created_at DESC)
);
```

-- FAQ知识库（基于历史对话自动提取）
CREATE TABLE faq_knowledge_base (
  id BIGSERIAL PRIMARY KEY,
  question_text TEXT NOT NULL,  -- 标准化问题
  question_variants JSONB,  -- 问题变体 ['如何挑选羊肉', '怎么选羊肉']
  answer_text TEXT NOT NULL,  -- 标准答案
  source_type VARCHAR(20) DEFAULT 'auto',  -- auto(自动提取)/manual(人工编辑)
  source_sessions JSONB,  -- 来源会话ID数组
  category VARCHAR(50),  -- product/culture/cooking/gift
  ip_type VARCHAR(20),  -- xiaoshu/xiaoshang
  confidence_score DECIMAL(3,2) DEFAULT 0.0,  -- 答案置信度(0-1)
  usage_count INT DEFAULT 0,  -- 被匹配次数
  last_matched_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_category (category),
  INDEX idx_confidence (confidence_score DESC),
  FULLTEXT INDEX idx_question_search (question_text, answer_text)
);

-- 对话日志本地存储（完整记录）
CREATE TABLE conversation_logs (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20),
  messages JSONB NOT NULL,  -- [{role, content, timestamp}]
  metadata JSONB,  -- {user_agent, ip_address, product_context}
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_session (session_id),
  INDEX idx_user (user_id),
  INDEX idx_created (created_at DESC)
);

### 2.5 营销内容

```sql
-- 品牌故事表
CREATE TABLE brand_stories (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL,
  story_title VARCHAR(200),
  story_content TEXT NOT NULL,
  story_theme VARCHAR(100),  -- 文化传承/工匠精神/自然馈赠
  cultural_elements JSONB,  -- ['那达慕', '手把肉']
  word_count INT,
  quality_score DECIMAL(3,2),  -- 人工评分 0.00-5.00
  usage_count INT DEFAULT 0,  -- 使用次数
  status VARCHAR(20) DEFAULT 'draft',  -- draft/published/archived
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_product (product_id),
  INDEX idx_status (status),
  INDEX idx_quality (quality_score DESC)
);

-- 直播脚本表
CREATE TABLE live_scripts (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL,
  platform VARCHAR(50) NOT NULL,  -- douyin/xiaohongshu/shipinhao
  duration INT NOT NULL,  -- 分钟数
  style VARCHAR(50),  -- 热情/专业/亲和
  script_content JSONB NOT NULL,  
  -- [{phase: '开场', start: '0:00', end: '0:30', scene: '...', script: '...'}]
  bgm_suggestions JSONB,  -- ['草原歌曲', '欢快背景音乐']
  shooting_tips JSONB,  -- ['航拍草原镜头', '多角度产品展示']
  usage_count INT DEFAULT 0,
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (created_by) REFERENCES users(id),
  INDEX idx_product (product_id),
  INDEX idx_platform (platform)
);
```

### 2.6 配额与计费

```sql
-- 配额使用表
CREATE TABLE quota_usage (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  resource_type VARCHAR(50) NOT NULL,  -- chat/brand_story/live_script/image/video
  used_count INT DEFAULT 0,
  limit_count INT DEFAULT 100,
  reset_at TIMESTAMP NOT NULL,  -- 配额重置时间
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (user_id, resource_type),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_user (user_id),
  INDEX idx_resource (resource_type)
);

-- LLM Token日志表
CREATE TABLE llm_token_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  session_id VARCHAR(64),
  provider VARCHAR(50),  -- deepseek/claude
  model VARCHAR(100),  -- deepseek-chat/claude-sonnet-4
  operation VARCHAR(50),  -- chat/brand_story/live_script
  input_tokens INT,
  output_tokens INT,
  total_tokens INT,
  cost_cny DECIMAL(10,6),  -- 成本（人民币）
  cached BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_user (user_id),
  INDEX idx_created (created_at DESC),
  INDEX idx_operation (operation),
  INDEX idx_provider (provider)
);

-- 媒体生成日志表
CREATE TABLE media_generation_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  media_type VARCHAR(20) NOT NULL,  -- image/video
  provider VARCHAR(50) DEFAULT 'volcengine',
  prompt TEXT NOT NULL,
  enhanced_prompt TEXT,  -- AI增强后的Prompt
  media_url VARCHAR(500),
  resolution VARCHAR(20),  -- 1024x1024/1080p/4k
  duration INT,  -- 视频时长（秒）
  cost_cny DECIMAL(10,2),
  status VARCHAR(20) DEFAULT 'pending',  -- pending/completed/failed
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_user (user_id),
  INDEX idx_type (media_type),
  INDEX idx_status (status),
  INDEX idx_created (created_at DESC)
);

-- 成本统计表（每日汇总）
CREATE TABLE daily_cost_summary (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  user_id BIGINT,
  total_tokens BIGINT,
  total_cost_cny DECIMAL(10,2),
  cache_hit_rate DECIMAL(5,2),  -- 缓存命中率
  operation_breakdown JSONB,  
  -- {chat: {tokens: 100K, cost: 200}, image: {count: 50, cost: 5}, video: {count: 2, cost: 4}}
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (date, user_id),
  FOREIGN KEY (user_id) REFERENCES users(id),
  INDEX idx_date (date DESC)
);
```

### 2.7 订单与支付

```sql
-- 订单表
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  order_no VARCHAR(32) UNIQUE NOT NULL,
  user_id BIGINT NOT NULL,
  product_id BIGINT,
  product_name VARCHAR(200),
  quantity INT DEFAULT 1,
  unit_price DECIMAL(10,2),
  total_amount DECIMAL(10,2),
  status VARCHAR(20) DEFAULT 'pending',  
  -- pending/paid/shipping/completed/cancelled/refunded
  paid_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  INDEX idx_user (user_id),
  INDEX idx_order_no (order_no),
  INDEX idx_status (status),
  INDEX idx_created (created_at DESC)
);
```

---

## 三、索引策略

### 3.1 核心索引

| 表 | 索引字段 | 类型 | 原因 |
|---|---------|------|------|
| products | origin_id, category_id | B-Tree | 高频JOIN |
| products | cultural_tags | GIN | JSONB查询 |
| ip_conversations | session_id, user_id | B-Tree | 对话历史查询 |
| ip_conversations | created_at | B-Tree | 时间范围查询 |
| cultural_elements | type, hot_score | B-Tree | 分类+排序 |
| llm_token_logs | user_id, created_at | B-Tree | 成本统计 |
| orders | user_id, status | B-Tree | 订单列表查询 |

### 3.2 复合索引

```sql
-- 产品列表查询优化（按分类+状态+时间）
CREATE INDEX idx_products_list 
ON products(category_id, status, created_at DESC);

-- 对话历史查询优化（按用户+会话+时间）
CREATE INDEX idx_conversations_history 
ON ip_conversations(user_id, session_id, created_at DESC);

-- 成本统计优化（按用户+日期）
CREATE INDEX idx_token_logs_cost 
ON llm_token_logs(user_id, created_at DESC);
```

### 3.3 全文搜索索引

```sql
-- 产品全文搜索（名称+描述）
ALTER TABLE products ADD COLUMN search_vector tsvector;

CREATE INDEX idx_products_search 
ON products USING GIN(search_vector);

-- 自动更新搜索向量
CREATE TRIGGER products_search_vector_update 
BEFORE INSERT OR UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(
  search_vector, 'pg_catalog.simple', name, description
);
```

---

## 四、数据迁移方案

### 4.1 Alembic配置

```python
# backend/alembic.ini
[alembic]
sqlalchemy.url = postgresql://user:pass@localhost:5432/mengzhi

# backend/alembic/env.py
from app.models import Base

target_metadata = Base.metadata
```

### 4.2 迁移脚本管理

```bash
# 创建迁移
alembic revision --autogenerate -m "Initial schema"

# 查看迁移历史
alembic history

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>
```

### 4.3 数据初始化脚本

```python
# backend/scripts/init_data.py

async def init_database():
    """初始化数据库"""
    # 1. 创建默认分类
    categories = [
        {"name": "牛羊肉", "level": 1},
        {"name": "乳制品", "level": 1},
        {"name": "杂粮", "level": 1},
    ]
    
    # 2. 创建产地
    origins = [
        {"name": "呼伦贝尔", "region": "内蒙古东北部"},
        {"name": "锡林郭勒", "region": "内蒙古中部"},
        {"name": "鄂尔多斯", "region": "内蒙古西南部"},
    ]
    
    # 3. 导入15个文化元素
    from scripts.init_cultural_elements import CULTURAL_DATA
    
    # 4. 创建测试用户
    test_user = {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": bcrypt_hash("Test123456")
    }
```

---

## 五、数据备份策略

### 5.1 备份方案

**全量备份**:
```bash
# 每日凌晨2点全量备份
0 2 * * * pg_dump -U postgres mengzhi | gzip > /backup/mengzhi_$(date +\%Y\%m\%d).sql.gz
```

**增量备份**:
```bash
# 开启WAL归档
archive_mode = on
archive_command = 'cp %p /backup/wal_archive/%f'
```

**保留策略**:
- 全量备份: 保留30天
- WAL归档: 保留7天

### 5.2 恢复演练

```bash
# 恢复到指定时间点
pg_restore -d mengzhi_recovery /backup/mengzhi_20260610.sql.gz
psql -d mengzhi_recovery -c "SELECT pg_wal_replay_resume();"
```

---

## 六、性能优化

### 6.1 查询优化

**慢查询日志**:
```sql
-- postgresql.conf
log_min_duration_statement = 1000  -- 记录>1s的查询
```

**EXPLAIN分析**:
```sql
EXPLAIN ANALYZE
SELECT * FROM products WHERE origin_id = 1;
```

### 6.2 连接池配置

```python
# backend/app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  -- 最小连接数
    max_overflow=20,  -- 最大溢出连接数
    pool_timeout=30,  -- 获取连接超时
    pool_recycle=3600  -- 连接回收时间
)
```

### 2.8 AI服务商配置表

```sql
-- AI服务商配置表
CREATE TABLE ai_provider_configs (
  id BIGSERIAL PRIMARY KEY,
  provider VARCHAR(50) NOT NULL UNIQUE,  -- deepseek/volcengine/claude
  provider_type VARCHAR(20) NOT NULL,  -- llm/image/video
  api_key_encrypted TEXT NOT NULL,  -- AES-256加密
  api_endpoint VARCHAR(500),
  model_name VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  priority INT DEFAULT 1,  -- 优先级（数字越小优先级越高，用于降级）
  config_json JSONB,  
  -- {temperature: 0.7, max_tokens: 2000, timeout: 30, region: "cn-north-1"}
  daily_quota INT,  -- 每日调用配额限制
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_provider (provider),
  INDEX idx_active_priority (is_active, priority),
  INDEX idx_type (provider_type)
);

-- AI服务商调用统计表
CREATE TABLE ai_provider_stats (
  id BIGSERIAL PRIMARY KEY,
  provider VARCHAR(50) NOT NULL,
  date DATE NOT NULL,
  total_calls INT DEFAULT 0,
  success_calls INT DEFAULT 0,
  failed_calls INT DEFAULT 0,
  total_cost_cny DECIMAL(10,2) DEFAULT 0,
  avg_latency_ms INT,  -- 平均延迟
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (provider, date),
  FOREIGN KEY (provider) REFERENCES ai_provider_configs(provider),
  INDEX idx_provider_date (provider, date DESC)
);
```

---

## 七、Redis数据结构

### 7.1 LLM缓存

```
KEY: llm:cache:{md5_hash}
TYPE: String
TTL: 3600秒
VALUE: LLM响应文本
```

### 7.2 Session存储

```
KEY: session:{session_id}:history
TYPE: List
TTL: 7200秒
VALUE: JSON消息列表
```

### 7.3 速率限制

```
KEY: rate_limit:{user_id}:{resource_type}:{date}
TYPE: String
TTL: 86400秒
VALUE: 使用次数
```

### 7.4 热度排行

```
KEY: cultural_elements:hot_rank
TYPE: Sorted Set
SCORE: hot_score
MEMBER: culture_id
```

---

## 八、数据字典

完整数据字典见附件: `DATABASE-DICTIONARY.xlsx`

包含:
- 表名/字段名/数据类型/长度/必填/默认值/说明
- 外键关系图
- 索引列表

---

**文档结束**

> 数据库设计应遵循第三范式，避免数据冗余。JSONB字段用于灵活存储，但不应滥用。
