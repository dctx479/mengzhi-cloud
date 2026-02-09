# 性能优化快速参考卡片

## 🎯 核心问题TOP 10

| 排名 | 问题 | 位置 | 影响 | 修复时间 | 收益 |
|------|------|------|------|---------|------|
| 1 | 数据库连接池配置 | database.py L40 | 高并发 | 1h | ↑60-80% |
| 2 | 缺少数据库索引 | 多处 | 所有查询 | 2h | ↑5-10x |
| 3 | Chat N+1查询 | chat_service.py L215 | 对话操作 | 2h | ↑97% |
| 4 | 认证无缓存 | auth_service.py L312 | 每个请求 | 2h | ↑80-90% |
| 5 | 配额系统性能差 | quota_service.py L41 | 聊天/API | 3h | ↑50-100x |
| 6 | Product N+1查询 | product_service.py L189 | 产品列表 | 1h | ↑50-70% |
| 7 | 依赖注入创建会话 | chat.py L43 | 所有API | 2h | ↑30-40% |
| 8 | 支付并发控制差 | payment_service.py L86 | 支付操作 | 3h | 改善 |
| 9 | bcrypt密码验证慢 | auth_service.py L54 | 登录 | 1h | ↑50% |
| 10 | 同步I/O阻塞异步 | chat_service.py L23 | 异步API | 3h | ↑5-10x |

---

## 📋 P0问题修复清单

### 1️⃣ 连接池配置 (1小时)
```python
# database.py L40-53
pool_size = 50 if ENVIRONMENT == 'production' else 20
max_overflow = 100 if ENVIRONMENT == 'production' else 40
pool_timeout = 60 if ENVIRONMENT == 'production' else 30
```

### 2️⃣ 添加索引 (2小时)
```bash
# 创建迁移文件
alembic revision -m "Add performance indexes"

# 生成以下索引:
# - users: (username, deleted_at), (email, deleted_at), (phone, deleted_at)
# - payments: (user_id, status, created_at), (order_id, status)
# - quotas: (user_id, period_start, period_end)
# - conversations: (user_id, status, updated_at)
```

### 3️⃣ 修复N+1查询 (4小时)

**Chat Service**:
```python
# chat_service.py
from sqlalchemy.orm import joinedload

# get_conversation_detail() - 添加 joinedload
conv = self.db.query(Conversation).options(
    joinedload(Conversation.messages)
).filter(...).first()
```

**Product Service**:
```python
# product_service.py
# get_product_by_id(), get_product_by_name() 都添加 joinedload
query = query.options(joinedload(Product.creator))
```

### 4️⃣ 认证缓存 (3小时)
```python
# auth_service.py - 新增方法
def get_user_by_id_cached(self, user_id: str):
    cache_key = f"user:{user_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached  # 直接返回，无DB查询

    user = self._get_user_by_id(user_id)
    if user:
        cache.set(cache_key, user.to_dict(), 3600)  # 1小时
    return user

# chat.py - 修改 get_user_id()
user = auth_service.get_user_by_id_cached(user_id)  # ✅ 使用缓存版本
```

### 5️⃣ 配额Redis优化 (4小时)
```python
# quota_service.py - 新增方法
def check_quota_redis(self, resource_type: str, required_amount: int, user_id: int):
    """使用Redis配额检查（1-5ms vs 200-500ms）"""
    cache_key = f"quota:{user_id}:{resource_type}:{date.today()}"
    used = int(cache.get(cache_key) or 0)
    limit = quota_limits[resource_type]
    return used + required_amount <= limit

def deduct_quota_redis(self, resource_type: str, amount: int, user_id: int):
    """使用Lua脚本的原子扣减"""
    # 脚本见性能分析报告中的完整代码
```

---

## ✅ 验证方式

### 1. SQL查询计数
```python
# 启用SQL日志
engine = create_engine(..., echo=True)

# 对话详情查询
# 优化前: ~100 queries
# 优化后: ~3 queries
```

### 2. 性能基准测试
```bash
python scripts/perf_benchmark.py

# 预期输出
# GET /api/chat/conversations
#   平均: 150ms (优化前: 500ms) ↑70%
# POST /api/chat/message
#   平均: 800ms (优化前: 2000ms) ↑60%
```

### 3. 缓存命中率
```bash
redis-cli INFO stats | grep keyspace_hits
# 预期: hits增加, 命中率 > 50%
```

---

## 📊 性能提升预期

| 操作 | 优化前 | 优化后 | 提升倍数 |
|------|--------|--------|---------|
| 数据库查询 | 100+ | 1-3 | **30-50x** |
| 认证检查 | 100ms | 10-20ms | **5-10x** |
| 配额检查 | 500ms | 5-10ms | **50-100x** |
| 对话加载 | 2-5s | 200-300ms | **5-10x** |
| 登录时间 | 2-5s | 0.5-1s | **2-5x** |
| 高并发吞吐 | 100 req/s | 500-1000 req/s | **5-10x** |

---

## 🚀 优先级执行计划

### 第1天 (基础优化)
- [ ] 09:00 - 数据库连接池配置更改
- [ ] 10:00 - 验证连接池生效
- [ ] 11:00 - 创建数据库迁移脚本
- [ ] 14:00 - 执行迁移创建索引
- [ ] 15:00 - 验证索引

**预期收益**: ↑30-50%

### 第2-3天 (查询优化)
- [ ] 修复Chat N+1查询 (使用joinedload)
- [ ] 修复Product N+1查询
- [ ] 验证查询数减少

**预期收益**: ↑50-70%

### 第4-5天 (缓存优化)
- [ ] 实现认证缓存
- [ ] 修改依赖注入使用scoped_session
- [ ] 验证缓存命中

**预期收益**: ↑60-80%

### 第6-7天 (高级优化)
- [ ] 使用Redis重构配额系统
- [ ] 优化支付并发控制
- [ ] 负载测试验证

**预期收益**: ↑80-95%

---

## 🔍 关键代码位置

```
backend/app/
├── core/
│   ├── database.py          ← 连接池配置 (L40)
│   └── cache_manager.py     ← 缓存管理 (L60)
├── services/
│   ├── auth_service.py      ← 认证 (L312, 335, 357, 371)
│   ├── chat_service.py      ← 对话 (L200, 215, 326)
│   ├── payment_service.py   ← 支付 (L86)
│   ├── product_service.py   ← 产品 (L189)
│   └── quota_service.py     ← 配额 (L41, 116)
├── api/
│   └── chat.py              ← API路由 (L43, 54)
└── models/
    ├── conversation.py
    ├── message.py
    └── payment.py
```

---

## 🛠️ 常用命令

```bash
# 启用SQL日志（调试用）
export SQLALCHEMY_ECHO=1

# 运行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看数据库索引
mysql -u root -p -e "SHOW INDEX FROM users\G" agri_platform

# Redis键统计
redis-cli DBSIZE
redis-cli --stat

# 性能基准测试
python scripts/perf_benchmark.py

# 负载测试（需要locust）
locust -f tests/load_test.py -u 1000 -r 100
```

---

## 📈 监控关键指标

在生产环境部署后，重点监控：

```python
# 1. 响应时间分布
response_time_p50   # 中位数
response_time_p95   # 95分位
response_time_p99   # 99分位

# 2. 缓存效率
cache_hit_rate      # > 50% 为目标
redis_memory_used   # 不超过配额

# 3. 数据库
db_connections      # 不超过 pool_size + max_overflow
db_slow_queries     # 监控 > 1000ms 的查询
db_qps              # 查询/秒

# 4. 业务指标
login_success_rate  # > 99.5%
payment_success_rate # > 99.9%
chat_completion_rate # > 98%
```

---

## 💾 回滚方案

如果发现问题，立即执行:

```bash
# 1. 代码回滚
git revert <commit-hash>

# 2. 数据库回滚
alembic downgrade -1

# 3. 缓存清空
redis-cli FLUSHDB

# 4. 重启应用
docker restart app

# 5. 验证
curl http://localhost:8000/api/health
```

---

## 📞 常见问题

**Q: 修改连接池会影响现有连接吗?**
A: 不会。新的配置在应用重启后生效，现有连接会正常完成。

**Q: Redis不可用时会发生什么?**
A: 系统有降级处理，会回退到数据库查询，但性能会下降。

**Q: N+1查询修复会改变API响应格式吗?**
A: 不会。只是优化查询方式，响应格式完全相同。

**Q: 缓存数据不一致怎么办?**
A: 实施了缓存失效机制，用户修改后立即清除缓存。

---

## 📚 详细文档

完整细节见：
- `/PERFORMANCE_ANALYSIS.md` - 完整问题分析
- `/PERFORMANCE_OPTIMIZATION_GUIDE.md` - 详细实施指南

---

**最后更新**: 2026-02-10
**维护者**: Performance Monitor
**状态**: 准备实施
