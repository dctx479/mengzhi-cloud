-- 蒙智云数据库完整Schema
-- Database Schema v1.1
-- 创建日期: 2026-06-12
-- PostgreSQL 15

-- ============================================
-- 扩展与配置
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 模糊搜索

-- ============================================
-- 一、用户与认证
-- ============================================

-- 企业表（需要先创建，因为users表有外键）
CREATE TABLE enterprises (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  api_key_encrypted TEXT,  -- AES-256加密
  quota_limit INT DEFAULT 1000,
  industry VARCHAR(100),
  contact_person VARCHAR(100),
  contact_phone VARCHAR(20),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户表
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  user_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(100) UNIQUE,
  phone VARCHAR(20) UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  user_type VARCHAR(20) DEFAULT 'individual',
  role VARCHAR(20) DEFAULT 'user',
  enterprise_id BIGINT,
  avatar_url VARCHAR(500),
  status VARCHAR(20) DEFAULT 'active',
  last_login_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (enterprise_id) REFERENCES enterprises(id)
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_enterprise ON users(enterprise_id);
CREATE INDEX idx_users_status ON users(status);

-- JWT刷新令牌表
CREATE TABLE refresh_tokens (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  jti VARCHAR(64) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX idx_refresh_tokens_jti ON refresh_tokens(jti);

-- ============================================
-- 二、产品管理
-- ============================================

-- 品类表
CREATE TABLE categories (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_id BIGINT,
  level INT DEFAULT 1,
  sort_order INT DEFAULT 0,
  icon_url VARCHAR(500),
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (parent_id) REFERENCES categories(id)
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_level ON categories(level);

-- 产地表
CREATE TABLE origins (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  region VARCHAR(100),
  description TEXT,
  latitude DECIMAL(10,7),
  longitude DECIMAL(10,7),
  cover_image VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_origins_region ON origins(region);

-- 产品表
CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  category_id BIGINT,
  origin_id BIGINT,
  description TEXT,
  images JSONB,
  selling_points JSONB,
  cultural_tags JSONB,
  price DECIMAL(10,2),
  stock INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'active',
  view_count INT DEFAULT 0,
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (category_id) REFERENCES categories(id),
  FOREIGN KEY (origin_id) REFERENCES origins(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_origin ON products(origin_id);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_created ON products(created_at DESC);
CREATE INDEX idx_products_cultural_tags ON products USING GIN (cultural_tags);
CREATE INDEX idx_products_list ON products(category_id, status, created_at DESC);

-- ============================================
-- 三、知识图谱
-- ============================================

-- 文化元素表
CREATE TABLE cultural_elements (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  type VARCHAR(50) NOT NULL,
  story TEXT NOT NULL,
  origin_region VARCHAR(100),
  hot_score INT DEFAULT 50,
  metadata JSONB,
  view_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cultural_elements_type ON cultural_elements(type);
CREATE INDEX idx_cultural_elements_hot_score ON cultural_elements(hot_score DESC);
CREATE INDEX idx_cultural_elements_region ON cultural_elements(origin_region);

-- 产品-文化关联表
CREATE TABLE product_culture_links (
  product_id BIGINT NOT NULL,
  culture_id BIGINT NOT NULL,
  relevance_score DECIMAL(3,2) DEFAULT 0.50,
  link_type VARCHAR(50) DEFAULT 'manual',
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (product_id, culture_id),
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (culture_id) REFERENCES cultural_elements(id)
);

CREATE INDEX idx_product_culture_product ON product_culture_links(product_id);
CREATE INDEX idx_product_culture_culture ON product_culture_links(culture_id);
CREATE INDEX idx_product_culture_relevance ON product_culture_links(relevance_score DESC);

-- 产地-文化关联表
CREATE TABLE origin_culture_links (
  origin_id BIGINT NOT NULL,
  culture_id BIGINT NOT NULL,
  strength DECIMAL(3,2) DEFAULT 1.00,
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (origin_id, culture_id),
  FOREIGN KEY (origin_id) REFERENCES origins(id),
  FOREIGN KEY (culture_id) REFERENCES cultural_elements(id)
);

-- ============================================
-- 四、IP对话与FAQ
-- ============================================

-- IP会话表
CREATE TABLE ip_sessions (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) UNIQUE NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20),
  message_count INT DEFAULT 0,
  total_tokens INT DEFAULT 0,
  started_at TIMESTAMP DEFAULT NOW(),
  last_active_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_ip_sessions_session ON ip_sessions(session_id);
CREATE INDEX idx_ip_sessions_user ON ip_sessions(user_id);

-- IP对话消息表
CREATE TABLE ip_conversations (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20) NOT NULL,
  role VARCHAR(20) NOT NULL,
  user_message TEXT,
  ai_response TEXT,
  intent_type VARCHAR(50),
  emotion_type VARCHAR(20),
  cultural_elements_mentioned JSONB,
  suggestions JSONB,
  input_tokens INT,
  output_tokens INT,
  tokens_used INT,
  latency_ms INT,
  cached BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_ip_conversations_session ON ip_conversations(session_id);
CREATE INDEX idx_ip_conversations_user ON ip_conversations(user_id);
CREATE INDEX idx_ip_conversations_ip_type ON ip_conversations(ip_type);
CREATE INDEX idx_ip_conversations_created ON ip_conversations(created_at DESC);
CREATE INDEX idx_ip_conversations_history ON ip_conversations(user_id, session_id, created_at DESC);

-- 对话日志完整存储
CREATE TABLE conversation_logs (
  id BIGSERIAL PRIMARY KEY,
  session_id VARCHAR(64) NOT NULL,
  user_id BIGINT,
  ip_type VARCHAR(20),
  messages JSONB NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_conversation_logs_session ON conversation_logs(session_id);
CREATE INDEX idx_conversation_logs_user ON conversation_logs(user_id);
CREATE INDEX idx_conversation_logs_created ON conversation_logs(created_at DESC);

-- FAQ知识库
CREATE TABLE faq_knowledge_base (
  id BIGSERIAL PRIMARY KEY,
  question_text TEXT NOT NULL,
  question_variants JSONB,
  answer_text TEXT NOT NULL,
  source_type VARCHAR(20) DEFAULT 'auto',
  source_sessions JSONB,
  category VARCHAR(50),
  ip_type VARCHAR(20),
  confidence_score DECIMAL(3,2) DEFAULT 0.0,
  usage_count INT DEFAULT 0,
  last_matched_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_faq_category ON faq_knowledge_base(category);
CREATE INDEX idx_faq_confidence ON faq_knowledge_base(confidence_score DESC);
CREATE INDEX idx_faq_question_gin ON faq_knowledge_base USING gin(question_text gin_trgm_ops);

-- ============================================
-- 五、营销内容
-- ============================================

-- 品牌故事表
CREATE TABLE brand_stories (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL,
  story_title VARCHAR(200),
  story_content TEXT NOT NULL,
  story_theme VARCHAR(100),
  cultural_elements JSONB,
  word_count INT,
  quality_score DECIMAL(3,2),
  usage_count INT DEFAULT 0,
  status VARCHAR(20) DEFAULT 'draft',
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_brand_stories_product ON brand_stories(product_id);
CREATE INDEX idx_brand_stories_status ON brand_stories(status);
CREATE INDEX idx_brand_stories_quality ON brand_stories(quality_score DESC);

-- 直播脚本表
CREATE TABLE live_scripts (
  id BIGSERIAL PRIMARY KEY,
  product_id BIGINT NOT NULL,
  platform VARCHAR(50) NOT NULL,
  duration INT NOT NULL,
  style VARCHAR(50),
  script_content JSONB NOT NULL,
  bgm_suggestions JSONB,
  shooting_tips JSONB,
  usage_count INT DEFAULT 0,
  created_by BIGINT,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (product_id) REFERENCES products(id),
  FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_live_scripts_product ON live_scripts(product_id);
CREATE INDEX idx_live_scripts_platform ON live_scripts(platform);

-- ============================================
-- 六、AI服务商配置
-- ============================================

-- AI服务商配置表
CREATE TABLE ai_provider_configs (
  id BIGSERIAL PRIMARY KEY,
  provider VARCHAR(50) NOT NULL UNIQUE,
  provider_type VARCHAR(20) NOT NULL,
  api_key_encrypted TEXT NOT NULL,
  api_endpoint VARCHAR(500),
  model_name VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  priority INT DEFAULT 1,
  config_json JSONB,
  daily_quota INT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_provider_configs_provider ON ai_provider_configs(provider);
CREATE INDEX idx_ai_provider_configs_active_priority ON ai_provider_configs(is_active, priority);
CREATE INDEX idx_ai_provider_configs_type ON ai_provider_configs(provider_type);

-- AI服务商统计表
CREATE TABLE ai_provider_stats (
  id BIGSERIAL PRIMARY KEY,
  provider VARCHAR(50) NOT NULL,
  date DATE NOT NULL,
  total_calls INT DEFAULT 0,
  success_calls INT DEFAULT 0,
  failed_calls INT DEFAULT 0,
  total_cost_cny DECIMAL(10,2) DEFAULT 0,
  avg_latency_ms INT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (provider, date)
);

CREATE INDEX idx_ai_provider_stats_date ON ai_provider_stats(date DESC);

-- ============================================
-- 七、配额与计费
-- ============================================

-- 配额使用表
CREATE TABLE quota_usage (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  resource_type VARCHAR(50) NOT NULL,
  used_count INT DEFAULT 0,
  limit_count INT DEFAULT 100,
  reset_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (user_id, resource_type),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_quota_usage_user ON quota_usage(user_id);
CREATE INDEX idx_quota_usage_resource ON quota_usage(resource_type);

-- LLM Token日志表
CREATE TABLE llm_token_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  session_id VARCHAR(64),
  provider VARCHAR(50),
  model VARCHAR(100),
  operation VARCHAR(50),
  input_tokens INT,
  output_tokens INT,
  total_tokens INT,
  cost_cny DECIMAL(10,6),
  cached BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_llm_token_logs_user ON llm_token_logs(user_id);
CREATE INDEX idx_llm_token_logs_created ON llm_token_logs(created_at DESC);
CREATE INDEX idx_llm_token_logs_operation ON llm_token_logs(operation);
CREATE INDEX idx_llm_token_logs_provider ON llm_token_logs(provider);
CREATE INDEX idx_llm_token_logs_cost ON llm_token_logs(user_id, created_at DESC);

-- 媒体生成日志表
CREATE TABLE media_generation_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  media_type VARCHAR(20) NOT NULL,
  provider VARCHAR(50) DEFAULT 'volcengine',
  prompt TEXT NOT NULL,
  enhanced_prompt TEXT,
  media_url VARCHAR(500),
  resolution VARCHAR(20),
  duration INT,
  cost_cny DECIMAL(10,2),
  status VARCHAR(20) DEFAULT 'pending',
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_media_generation_logs_user ON media_generation_logs(user_id);
CREATE INDEX idx_media_generation_logs_type ON media_generation_logs(media_type);
CREATE INDEX idx_media_generation_logs_status ON media_generation_logs(status);
CREATE INDEX idx_media_generation_logs_created ON media_generation_logs(created_at DESC);

-- 每日成本汇总表
CREATE TABLE daily_cost_summary (
  id BIGSERIAL PRIMARY KEY,
  date DATE NOT NULL,
  user_id BIGINT,
  total_tokens BIGINT,
  total_cost_cny DECIMAL(10,2),
  cache_hit_rate DECIMAL(5,2),
  operation_breakdown JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (date, user_id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_daily_cost_summary_date ON daily_cost_summary(date DESC);

-- ============================================
-- 八、订单与支付
-- ============================================

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
  paid_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_order_no ON orders(order_no);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- ============================================
-- 九、数据初始化
-- ============================================

-- 插入默认管理员
INSERT INTO users (username, email, password_hash, role, status)
VALUES ('admin', 'admin@mengzhi.cloud', 'CHANGE_ME', 'admin', 'active');

-- 插入默认品类
INSERT INTO categories (name, level) VALUES
  ('牛羊肉', 1),
  ('乳制品', 1),
  ('杂粮', 1);

-- 插入默认产地
INSERT INTO origins (name, region) VALUES
  ('呼伦贝尔', '内蒙古东北部'),
  ('锡林郭勒', '内蒙古中部'),
  ('鄂尔多斯', '内蒙古西南部');

-- 插入AI服务商配置（示例，需替换真实API Key）
INSERT INTO ai_provider_configs (provider, provider_type, api_key_encrypted, api_endpoint, model_name, priority)
VALUES
  ('deepseek', 'llm', 'ENCRYPTED_KEY_PLACEHOLDER', 'https://api.deepseek.com', 'deepseek-v4-flash', 1),
  ('volcengine', 'image', 'ENCRYPTED_KEY_PLACEHOLDER', 'https://visual.volcengineapi.com', 'jimeng_t2i_v31', 1),
  ('volcengine_video', 'video', 'ENCRYPTED_KEY_PLACEHOLDER', 'https://visual.volcengineapi.com', 'jimeng_ti2v_v30_pro', 1);
