# 数据库索引优化 - 快速参考

## 快速开始

### 执行迁移
```bash
cd backend
alembic upgrade 008_optimize_query_indices
```

### 验证索引
```bash
mysql> SHOW INDEX FROM users WHERE KEY_name LIKE 'ix_%';
```

## 索引概览

| 表名 | 索引名 | 字段 | 用途 |
|------|--------|------|------|
| users | ix_users_username_deleted_v2 | (username, deleted_at) | 用户名登录 |
| users | ix_users_email_deleted_v2 | (email, deleted_at) | 邮箱登录 |
| users | ix_users_phone_deleted_v2 | (phone, deleted_at) | 手机登录 |
| billing_records | ix_billing_records_user_date | (user_id, billing_date) | 账单查询 |
| billing_records | ix_billing_records_user_month | (user_id, billing_month) | 月度查询 |
| invoices | ix_invoices_user_status_period | (user_id, status, billing_period_start) | 发票列表 |
| invoices | ix_invoices_status_paid | (status, paid_at) | 支付查询 |
| tenant_quotas | ix_quotas_enterprise_period | (enterprise_id, period_start, period_end) | 企业配额 |
| tenant_quotas | ix_quotas_user_period | (user_id, period_start, period_end) | 用户配额 |
| conversations | ix_conversations_user_status_updated | (user_id, status, updated_at) | 对话列表 |
| messages | ix_messages_conversation_v2 | (conversation_id) | 消息查询 |

## 性能提升目标

```
登录查询:    50-70% ↑
账单查询:    40-60% ↑
发票查询:    35-55% ↑
配额查询:    30-50% ↑
对话列表:    35-55% ↑
消息查询:    25-40% ↑
```

## 常用命令

### 查看所有索引
```sql
SHOW INDEX FROM table_name;
```

### 分析查询
```sql
EXPLAIN SELECT * FROM users WHERE username = 'test' AND deleted_at IS NULL;
```

### 查看索引统计
```sql
SELECT INDEX_NAME, STAT_VALUE 
FROM mysql.innodb_index_stats
WHERE TABLE_NAME = 'users';
```

### 删除索引（回滚）
```bash
alembic downgrade -1
```

### 手动回滚所有索引
```sql
DROP INDEX IF EXISTS ix_users_username_deleted_v2 ON users;
DROP INDEX IF EXISTS ix_users_email_deleted_v2 ON users;
DROP INDEX IF EXISTS ix_users_phone_deleted_v2 ON users;
DROP INDEX IF EXISTS ix_billing_records_user_date ON billing_records;
DROP INDEX IF EXISTS ix_billing_records_user_month ON billing_records;
DROP INDEX IF EXISTS ix_invoices_user_status_period ON invoices;
DROP INDEX IF EXISTS ix_invoices_status_paid ON invoices;
DROP INDEX IF EXISTS ix_quotas_enterprise_period ON tenant_quotas;
DROP INDEX IF EXISTS ix_quotas_user_period ON tenant_quotas;
DROP INDEX IF EXISTS ix_conversations_user_status_updated ON conversations;
DROP INDEX IF EXISTS ix_messages_conversation_v2 ON messages;
```

## 关键 SQL 查询

### 用户登录查询 (50-70% 提升)
```sql
-- 使用索引: ix_users_username_deleted_v2
SELECT * FROM users 
WHERE username = ? AND deleted_at IS NULL;
```

### 账单查询 (40-60% 提升)
```sql
-- 使用索引: ix_billing_records_user_date
SELECT * FROM billing_records 
WHERE user_id = ? AND billing_date BETWEEN ? AND ?
ORDER BY billing_date DESC;
```

### 发票列表 (35-55% 提升)
```sql
-- 使用索引: ix_invoices_user_status_period
SELECT * FROM invoices 
WHERE user_id = ? AND status = 'paid'
ORDER BY billing_period_start DESC
LIMIT 10;
```

### 配额查询 (30-50% 提升)
```sql
-- 使用索引: ix_quotas_user_period
SELECT * FROM tenant_quotas 
WHERE user_id = ? AND period_start <= ? AND period_end >= ?;
```

### 对话列表 (35-55% 提升)
```sql
-- 使用索引: ix_conversations_user_status_updated
SELECT * FROM conversations 
WHERE user_id = ? AND status = 'active'
ORDER BY updated_at DESC
LIMIT 20;
```

### 消息查询 (25-40% 提升)
```sql
-- 使用索引: ix_messages_conversation_v2
SELECT * FROM messages 
WHERE conversation_id = ?
ORDER BY created_at DESC;
```

## 验证清单

- [ ] 运行 `alembic upgrade 008_optimize_query_indices`
- [ ] 验证所有索引已创建
- [ ] 执行 EXPLAIN 分析查询
- [ ] 对比性能改进
- [ ] 更新应用文档

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| 索引未被使用 | 检查 WHERE 条件，避免在索引列上使用函数 |
| 迁移失败 | 检查表是否存在，查看 MySQL 错误日志 |
| 性能未改善 | 运行 ANALYZE TABLE，清理统计信息 |
| 索引占用空间过大 | 正常现象，通常为表大小的 10-20% |

## 文件位置

- 迁移文件: `backend/alembic/versions/008_optimize_query_indices.py`
- 详细指南: `backend/docs/INDEX_OPTIMIZATION_GUIDE.md`
- SQL 脚本: `backend/docs/create_indices.sql`
- 本快速参考: `backend/docs/INDEX_QUICK_REFERENCE.md`

## 性能数据示例

### 登录查询性能对比
```
优化前: Query_time: 2.567 sec, Rows_examined: 1000000
优化后: Query_time: 0.023 sec, Rows_examined: 1
提升:   99.1%
```

### 系统整体提升
```
平均查询延迟: 1.8s → 0.04s (97.8% 提升)
吞吐量:       5-10 倍增长
并发能力:     10 倍以上
```

---

**创建日期**: 2026-01-24  
**版本**: 1.0
