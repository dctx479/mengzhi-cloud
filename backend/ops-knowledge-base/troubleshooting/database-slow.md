# 数据库性能问题排查手册

## 概述

### 问题描述
数据库查询响应缓慢,导致API请求延迟增加,用户体验下降,严重时可能引发连接池耗尽、服务不可用。

### 影响范围
- **影响级别**: Warning/Critical
- **影响用户**: 部分或全部用户
- **业务影响**: 响应延迟、超时、数据操作失败
- **系统影响**: 连接池耗尽、CPU/IO飙升
- **优先级**: 高优先级

---

## 症状识别

### 监控告警
```
AlertName: SlowDatabaseQuery
Severity: Warning
Description: P95 query latency > 1s
Current Value: 2.5s

AlertName: DatabaseConnectionPoolExhausted
Severity: Critical
Description: All database connections in use
Active Connections: 100/100
```

### Grafana 表现
- "Database Query Duration P95" 持续高位
- "Database Connections Active" 接近最大值
- "Slow Query Count" 显著增加
- "API Response Time" 相应增加

---

## 快速诊断

### Step 1: 查看慢查询

```sql
-- 连接数据库
docker exec -it postgres psql -U ai_platform

-- 查看慢查询 (需要 pg_stat_statements 扩展)
SELECT
    query,
    calls,
    total_exec_time / 1000 AS total_time_sec,
    mean_exec_time / 1000 AS mean_time_sec,
    max_exec_time / 1000 AS max_time_sec,
    stddev_exec_time / 1000 AS stddev_time_sec
FROM pg_stat_statements
WHERE mean_exec_time > 100  -- 平均耗时 > 100ms
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 查看当前正在执行的慢查询
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
  AND state != 'idle'
ORDER BY duration DESC;
```

### Step 2: 分析查询计划

```sql
-- 分析慢查询的执行计划
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM posts WHERE user_id = 123 ORDER BY created_at DESC LIMIT 20;

-- 查看是否使用了索引
EXPLAIN
SELECT * FROM posts WHERE user_id = 123;
-- 输出:
-- Seq Scan on posts  ❌ 全表扫描
-- Index Scan using idx_posts_user_id  ✅ 使用索引
```

### Step 3: 检查索引使用情况

```sql
-- 查看未使用的索引
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 查看缺失索引的表 (根据顺序扫描次数判断)
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan AS avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_scan DESC
LIMIT 20;
```

### Step 4: 检查表和索引膨胀

```sql
-- 查看表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;

-- 检查表膨胀 (dead tuples)
SELECT
    schemaname,
    tablename,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 10;
```

---

## 常见问题和修复

### 问题1: 缺少索引

**症状**: 全表扫描,查询缓慢

**诊断**:
```sql
EXPLAIN SELECT * FROM posts WHERE status = 'published';
-- Seq Scan on posts (cost=0.00..18472.00 rows=100000 width=256)
```

**修复**:
```sql
-- 创建单列索引
CREATE INDEX idx_posts_status ON posts(status);

-- 创建复合索引 (根据查询条件)
CREATE INDEX idx_posts_status_created ON posts(status, created_at DESC);

-- 验证索引生效
EXPLAIN SELECT * FROM posts WHERE status = 'published';
-- Index Scan using idx_posts_status (cost=0.43..823.44 rows=100000 width=256)
```

### 问题2: N+1查询

**症状**: 大量重复查询,数据库连接数飙升

**问题代码**:
```python
# ❌ N+1查询
@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).limit(100).all()  # 1次查询
    for user in users:
        user.posts_count = db.query(Post).filter(Post.user_id == user.id).count()  # 100次查询
    return users
```

**修复**:
```python
# ✅ JOIN查询或子查询
from sqlalchemy import func

@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(
        User,
        func.count(Post.id).label('posts_count')
    ).outerjoin(Post).group_by(User.id).limit(100).all()
    return users
```

### 问题3: 锁竞争

**症状**: 查询长时间等待,数据库CPU不高但响应慢

**诊断**:
```sql
-- 查看锁等待
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement,
    blocked_activity.application_name AS blocked_app
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

**修复**:
```python
# 使用乐观锁代替悲观锁
from sqlalchemy import Column, Integer
from sqlalchemy.orm import Session

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    version = Column(Integer, default=0, nullable=False)  # 版本号

# 乐观锁更新
@router.put("/posts/{post_id}")
async def update_post(post_id: int, data: dict, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    old_version = post.version

    # 更新数据
    for key, value in data.items():
        setattr(post, key, value)
    post.version += 1

    # 提交时检查版本
    rows_updated = db.query(Post).filter(
        Post.id == post_id,
        Post.version == old_version
    ).update({"version": post.version})

    if rows_updated == 0:
        raise HTTPException(status_code=409, detail="Conflict: Post was modified")

    db.commit()
    return post
```

### 问题4: 连接池耗尽

**症状**: `Database connection pool exhausted`

**诊断**:
```python
# 检查连接池状态
from app.core.database import engine
print(engine.pool.status())
# Pool size: 20  Connections in pool: 0  Current Overflow: 10  Current Checked out connections: 30
```

**修复**:
```python
# app/core/database.py

from sqlalchemy import create_engine

# 修改前
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=0
)

# 修改后
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 增加连接池大小
    max_overflow=10,       # 允许溢出连接
    pool_timeout=30,       # 连接超时
    pool_recycle=3600,     # 1小时回收连接 (防止MySQL连接超时)
    pool_pre_ping=True     # 连接前检查是否有效
)
```

---

## 性能优化建议

### 1. 查询优化

```sql
-- 使用部分索引
CREATE INDEX idx_posts_published ON posts(created_at) WHERE status = 'published';

-- 使用表达式索引
CREATE INDEX idx_users_lower_email ON users(lower(email));

-- 使用GIN索引 (全文搜索)
CREATE INDEX idx_posts_search ON posts USING gin(to_tsvector('english', title || ' ' || content));
```

### 2. 批量操作

```python
# 批量插入
from sqlalchemy import insert

# ❌ 逐条插入
for data in items:
    db.add(Post(**data))
    db.commit()

# ✅ 批量插入
db.bulk_insert_mappings(Post, items)
db.commit()

# 或使用 Core API (更快)
stmt = insert(Post)
db.execute(stmt, items)
db.commit()
```

### 3. 查询缓存

```python
from functools import lru_cache
from app.core.redis import redis_client
import json

# Redis缓存装饰器
def cache_query(key_prefix: str, ttl: int = 3600):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{':'.join(map(str, args))}"

            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行查询
            result = await func(*args, **kwargs)

            # 写入缓存
            redis_client.setex(cache_key, ttl, json.dumps(result, default=str))

            return result
        return wrapper
    return decorator

# 使用示例
@cache_query("user:profile", ttl=1800)
async def get_user_profile(user_id: int, db: Session):
    return db.query(User).filter(User.id == user_id).first()
```

---

## 相关告警

| 告警名称 | 级别 | 说明 |
|----------|------|------|
| SlowDatabaseQuery | Warning | 查询延迟 > 1s |
| DatabaseConnectionPoolExhausted | Critical | 连接池耗尽 |
| DatabaseHighLoad | Warning | 数据库负载过高 |

---

## 历史案例

### 案例: 缺少索引导致慢查询 (2026-01-12)

**现象**: 用户列表页加载缓慢,耗时3-5秒

**诊断**:
```sql
EXPLAIN ANALYZE SELECT * FROM posts WHERE status = 'published' ORDER BY created_at DESC LIMIT 20;
-- Seq Scan on posts (actual time=2341.234..2341.456 rows=20)
```

**根因**: 500万条数据,无索引,全表扫描

**修复**:
```sql
CREATE INDEX idx_posts_status_created ON posts(status, created_at DESC);
```

**效果**: 查询时间从3s降低到5ms

---

## 相关文档

- [服务不可用排查](./service-down.md)
- [高CPU使用率排查](./high-cpu.md)
- [数据库运维手册](../runbooks/database-maintenance.md)
