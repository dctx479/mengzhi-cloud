-- ============================================================================
-- 数据库性能优化 - 索引创建脚本
-- 创建日期: 2026-01-24
-- 版本: 1.0
-- 说明: 此脚本创建优化查询性能的复合索引
-- ============================================================================

-- 确保在正确的数据库中执行
-- USE your_database_name;

-- ============================================================================
-- 1. Users 表 - 登录查询优化
-- ============================================================================
-- 用户名登录查询优化
CREATE INDEX IF NOT EXISTS ix_users_username_deleted_v2 ON users(username, deleted_at)
COMMENT '用户名登录查询优化';

-- 邮箱登录查询优化
CREATE INDEX IF NOT EXISTS ix_users_email_deleted_v2 ON users(email, deleted_at)
COMMENT '邮箱登录查询优化';

-- 手机号登录查询优化
CREATE INDEX IF NOT EXISTS ix_users_phone_deleted_v2 ON users(phone, deleted_at)
COMMENT '手机号登录查询优化';

-- ============================================================================
-- 2. Billing Records 表 - 账单查询优化
-- ============================================================================
-- 用户账单日期查询
CREATE INDEX IF NOT EXISTS ix_billing_records_user_date ON billing_records(user_id, billing_date)
COMMENT '用户账单日期查询优化';

-- 用户月度账单查询
CREATE INDEX IF NOT EXISTS ix_billing_records_user_month ON billing_records(user_id, billing_month)
COMMENT '用户月度账单查询优化';

-- ============================================================================
-- 3. Invoices 表 - 发票查询优化
-- ============================================================================
-- 用户发票状态周期查询
CREATE INDEX IF NOT EXISTS ix_invoices_user_status_period ON invoices(user_id, status, billing_period_start)
COMMENT '用户发票查询优化';

-- 支付状态时间查询
CREATE INDEX IF NOT EXISTS ix_invoices_status_paid ON invoices(status, paid_at)
COMMENT '发票支付状态查询优化';

-- ============================================================================
-- 4. Tenant Quotas 表 - 配额查询优化
-- ============================================================================
-- 企业配额周期查询
CREATE INDEX IF NOT EXISTS ix_quotas_enterprise_period ON tenant_quotas(enterprise_id, period_start, period_end)
COMMENT '企业配额周期查询优化';

-- 用户配额周期查询
CREATE INDEX IF NOT EXISTS ix_quotas_user_period ON tenant_quotas(user_id, period_start, period_end)
COMMENT '用户配额周期查询优化';

-- ============================================================================
-- 5. Conversations 表 - 对话列表查询优化
-- ============================================================================
-- 用户对话状态更新时间查询
CREATE INDEX IF NOT EXISTS ix_conversations_user_status_updated ON conversations(user_id, status, updated_at)
COMMENT '用户对话列表查询优化';

-- ============================================================================
-- 6. Messages 表 - 消息查询优化
-- ============================================================================
-- 对话消息查询
CREATE INDEX IF NOT EXISTS ix_messages_conversation_v2 ON messages(conversation_id)
COMMENT '消息对话查询优化';

-- ============================================================================
-- 验证索引创建
-- ============================================================================
-- 执行以下命令验证所有索引已成功创建：

-- 查看 users 表索引
-- SHOW INDEX FROM users WHERE KEY_name LIKE 'ix_users_%';

-- 查看 billing_records 表索引
-- SHOW INDEX FROM billing_records WHERE KEY_name LIKE 'ix_billing_records_%';

-- 查看 invoices 表索引
-- SHOW INDEX FROM invoices WHERE KEY_name LIKE 'ix_invoices_%';

-- 查看 tenant_quotas 表索引
-- SHOW INDEX FROM tenant_quotas WHERE KEY_name LIKE 'ix_quotas_%';

-- 查看 conversations 表索引
-- SHOW INDEX FROM conversations WHERE KEY_name LIKE 'ix_conversations_%';

-- 查看 messages 表索引
-- SHOW INDEX FROM messages WHERE KEY_name LIKE 'ix_messages_%';

-- ============================================================================
-- 查看所有新建的索引
-- ============================================================================
-- SELECT INDEX_NAME, TABLE_NAME, COLUMN_NAME, SEQ_IN_INDEX
-- FROM INFORMATION_SCHEMA.STATISTICS
-- WHERE TABLE_SCHEMA = DATABASE()
-- AND INDEX_NAME LIKE 'ix_%'
-- ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- ============================================================================
-- 性能验证 - EXPLAIN 分析
-- ============================================================================
-- 用户名登录查询
-- EXPLAIN SELECT * FROM users WHERE username = 'test' AND deleted_at IS NULL;
-- 应该显示：Using index 或 Using index condition

-- 用户账单查询
-- EXPLAIN SELECT * FROM billing_records WHERE user_id = 1 AND billing_month = '2026-01';
-- 应该显示：Using index 或 Using index condition

-- 用户发票查询
-- EXPLAIN SELECT * FROM invoices WHERE user_id = 1 AND status = 'paid' ORDER BY billing_period_start DESC LIMIT 10;
-- 应该显示：Using index 或 Using index condition

-- 配额周期查询
-- EXPLAIN SELECT * FROM tenant_quotas WHERE user_id = 1 AND period_start <= NOW() AND period_end >= NOW();
-- 应该显示：Using index 或 Using index condition

-- 对话列表查询
-- EXPLAIN SELECT * FROM conversations WHERE user_id = 1 AND status = 'active' ORDER BY updated_at DESC LIMIT 20;
-- 应该显示：Using index 或 Using index condition

-- 消息查询
-- EXPLAIN SELECT * FROM messages WHERE conversation_id = '123abc' ORDER BY created_at DESC;
-- 应该显示：Using index 或 Using index condition

-- ============================================================================
-- 索引维护命令
-- ============================================================================
-- 分析表统计信息
-- ANALYZE TABLE users, billing_records, invoices, tenant_quotas, conversations, messages;

-- 优化表碎片
-- OPTIMIZE TABLE users, billing_records, invoices, tenant_quotas, conversations, messages;

-- ============================================================================
-- 回滚命令（如果需要删除这些索引）
-- ============================================================================
-- DROP INDEX IF EXISTS ix_users_username_deleted_v2 ON users;
-- DROP INDEX IF EXISTS ix_users_email_deleted_v2 ON users;
-- DROP INDEX IF EXISTS ix_users_phone_deleted_v2 ON users;
-- DROP INDEX IF EXISTS ix_billing_records_user_date ON billing_records;
-- DROP INDEX IF EXISTS ix_billing_records_user_month ON billing_records;
-- DROP INDEX IF EXISTS ix_invoices_user_status_period ON invoices;
-- DROP INDEX IF EXISTS ix_invoices_status_paid ON invoices;
-- DROP INDEX IF EXISTS ix_quotas_enterprise_period ON tenant_quotas;
-- DROP INDEX IF EXISTS ix_quotas_user_period ON tenant_quotas;
-- DROP INDEX IF EXISTS ix_conversations_user_status_updated ON conversations;
-- DROP INDEX IF EXISTS ix_messages_conversation_v2 ON messages;
