# 性能优化实施指南

**项目**: AI赋能云平台
**日期**: 2026-02-10
**版本**: 1.0

---

## 快速参考

### 关键数据
- **总问题数**: 19个
- **P0严重问题**: 7个（立即处理）
- **P1重要问题**: 6个（本周处理）
- **P2一般问题**: 6个（可选）
- **预期性能提升**: 3-5倍（P0问题实施）/ 5-10倍（全部实施）

### 优先实施顺序
1. 数据库连接池配置 (1小时)
2. 添加数据库索引 (2小时)
3. 修复N+1查询 (4小时)
4. 实现认证缓存 (3小时)
5. 优化配额系统 (4小时)

---

## 一、P0问题快速修复

### 1.1 数据库连接池优化 (1小时)

**文件**: `backend/app/core/database.py`

**变更**:
```python
# 行40-53: 修改连接池配置

# 原始配置
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    echo=False,
    connect_args={
        "charset": "utf8mb4",
        "isolation_level": "READ COMMITTED",
    }
)

# 优化后配置
import os
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=50 if ENVIRONMENT == "production" else 20,
    max_overflow=100 if ENVIRONMENT == "production" else 40,
    pool_pre_ping=True,
    pool_recycle=1800 if ENVIRONMENT == "production" else 3600,
    pool_timeout=60 if ENVIRONMENT == "production" else 30,
    echo=False,
    connect_args={
        "charset": "utf8mb4",
        "isolation_level": "READ COMMITTED",
        "max_allowed_packet": 16777216,
        "connect_timeout": 30,
    },
    # 添加以下参数
    pool_pre_ping=True,  # 发送"SELECT 1"测试连接
    echo_pool=False,  # 不打印连接池日志
)
```

**验证**:
```bash
# 测试连接
python -c "from app.database import engine; engine.connect()"
```

**预期效果**: 高并发场景下连接获取延迟 ↓60-80%

---

### 1.2 添加数据库索引 (2小时)

**数据库迁移脚本**: `backend/alembic/versions/XXX_add_performance_indexes.py`

```python
"""Add performance indexes

Revision ID: XXX
Revises:
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa

revision = 'XXX'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """创建索引"""

    # 用户表索引 (认证)
    op.create_index(
        'idx_username_deleted',
        'users',
        ['username', 'deleted_at'],
        if_not_exists=True
    )

    op.create_index(
        'idx_email_deleted',
        'users',
        ['email', 'deleted_at'],
        if_not_exists=True
    )

    op.create_index(
        'idx_phone_deleted',
        'users',
        ['phone', 'deleted_at'],
        if_not_exists=True
    )

    # 支付表索引
    op.create_index(
        'idx_payment_user_status_created',
        'payments',
        ['user_id', 'status', 'created_at'],
        if_not_exists=True
    )

    op.create_index(
        'idx_payment_order_status',
        'payments',
        ['order_id', 'status'],
        if_not_exists=True
    )

    # 配额表索引
    op.create_index(
        'idx_quota_user_period',
        'tenant_quotas',
        ['user_id', 'period_start', 'period_end'],
        if_not_exists=True
    )

    op.create_index(
        'idx_quota_enterprise_period',
        'tenant_quotas',
        ['enterprise_id', 'period_start', 'period_end'],
        if_not_exists=True
    )

    # 对话表索引
    op.create_index(
        'idx_conversation_user_status_updated',
        'ai_conversations',
        ['user_id', 'status', 'updated_at'],
        if_not_exists=True
    )

    print("✓ 性能索引创建完成")

def downgrade():
    """删除索引"""
    op.drop_index('idx_username_deleted', table_name='users')
    op.drop_index('idx_email_deleted', table_name='users')
    op.drop_index('idx_phone_deleted', table_name='users')
    op.drop_index('idx_payment_user_status_created', table_name='payments')
    op.drop_index('idx_payment_order_status', table_name='payments')
    op.drop_index('idx_quota_user_period', table_name='tenant_quotas')
    op.drop_index('idx_quota_enterprise_period', table_name='tenant_quotas')
    op.drop_index('idx_conversation_user_status_updated', table_name='ai_conversations')
```

**执行**:
```bash
# 在低负载时段执行
alembic upgrade head

# 验证索引创建
mysql> SHOW INDEX FROM users\G
```

**预期效果**: 查询性能 ↑5-10倍

---

### 1.3 修复Chat N+1查询 (4小时)

**文件**: `backend/app/services/chat_service.py`

**问题代码** (行200-216):
```python
def get_conversation_detail(self, conversation_id: str, user_id: str):
    """获取对话详情"""
    conv = self.db.query(Conversation).filter(
        Conversation.conversation_uuid == conversation_id,
        Conversation.user_id == int(user_id)
    ).first()

    if not conv:
        raise BusinessException("对话不存在")

    result = conv.to_dict()
    result["messages"] = [msg.to_dict() for msg in conv.messages]  # ❌ N+1
    return result
```

**优化代码**:
```python
from sqlalchemy.orm import joinedload

def get_conversation_detail(self, conversation_id: str, user_id: str):
    """获取对话详情 - 优化版本"""
    # 使用joinedload预加载所有关联对象
    conv = self.db.query(Conversation).options(
        joinedload(Conversation.messages)
    ).filter(
        Conversation.conversation_uuid == conversation_id,
        Conversation.user_id == int(user_id)
    ).first()

    if not conv:
        raise BusinessException("对话不存在")

    result = conv.to_dict()
    # messages已在内存中，不会触发额外查询
    result["messages"] = [msg.to_dict() for msg in conv.messages]
    return result
```

**验证** (添加SQL日志记录):
```python
# 在database.py中启用SQL日志
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 临时启用以验证
    ...
)

# 测试
curl http://localhost:8000/api/chat/conversations/xxx
# 观察SQL语句数量，应该从101下降到3
```

**预期效果**: 对话详情查询时间 ↓90%

---

### 1.4 认证缓存实现 (3小时)

**文件**: `backend/app/services/auth_service.py`

**添加新方法**:
```python
from app.core.cache_manager import cache

class AuthService:
    # ... 现有代码 ...

    def get_user_by_id_cached(self, user_id: str):
        """使用缓存的用户查询"""
        cache_key = f"user:{user_id}"

        # 尝试从缓存获取
        cached_user = cache.get(cache_key)
        if cached_user is not None:
            # 从缓存构造用户对象（简化版）
            from app.models.user import User
            user = type('User', (), cached_user)()
            return user

        # 从数据库获取
        user = self._get_user_by_id(user_id)

        if user:
            # 缓存用户信息（1小时）
            cache.set(cache_key, {
                'id': user.id,
                'user_uuid': user.user_uuid,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'status': user.status,
                'role': user.role,
                'enterprise_id': user.enterprise_id,
                'locked_until': str(user.locked_until) if user.locked_until else None,
                'login_attempts': user.login_attempts,
            }, 3600)

        return user

    def invalidate_user_cache(self, user_id: str):
        """使缓存失效（用户修改后调用）"""
        cache_key = f"user:{user_id}"
        cache.delete(cache_key)
```

**修改认证路由** (chat.py):
```python
async def get_user_id(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> str:
    """从认证头获取用户ID"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]

    try:
        from app.services.auth_service import AuthService
        auth_service = AuthService(db)
        payload = auth_service.decode_token(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # ✅ 使用缓存版本
        user = auth_service.get_user_by_id_cached(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

**预期效果**: 认证检查响应时间 ↓80-90%

---

### 1.5 配额系统优化 (4小时)

**文件**: `backend/app/services/quota_service.py`

**新增方法** - 使用Redis实现高性能配额检查:
```python
from app.core.cache_manager import cache
from datetime import date

class QuotaService:
    # ... 现有代码 ...

    def check_quota_redis(self, resource_type: str, required_amount: int = 1,
                         user_id: int = None) -> bool:
        """使用Redis的高性能配额检查"""

        if not user_id:
            return True  # 无用户时不检查

        # 生成Redis键
        today = date.today().isoformat()
        cache_key = f"quota:{user_id}:{resource_type}:{today}"

        # 配额限制配置
        quota_limits = {
            'CHAT_COUNT': 100,
            'API_CALLS': 1000,
            'TOKEN_COUNT': 100000,
        }

        limit = quota_limits.get(resource_type, 0)
        if limit <= 0:
            return True  # 无限制

        # 从Redis获取已使用量
        client = cache.get_client()
        if not client:
            return True  # Redis不可用时不限制

        used = int(client.get(cache_key) or 0)

        if used + required_amount > limit:
            remaining = max(0, limit - used)
            logger.warning(
                f"配额不足: user_id={user_id}, "
                f"resource_type={resource_type}, "
                f"used={used}, limit={limit}, required={required_amount}"
            )
            return False

        return True

    def deduct_quota_redis(self, resource_type: str, amount: int,
                          user_id: int) -> bool:
        """使用Redis的高性能配额扣减"""

        today = date.today().isoformat()
        cache_key = f"quota:{user_id}:{resource_type}:{today}"

        client = cache.get_client()
        if not client:
            logger.warning("Redis不可用，配额扣减失败")
            return False

        # 使用Lua脚本保证原子性
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local amount = tonumber(ARGV[2])

        local used = tonumber(redis.call('GET', key) or 0)

        if used + amount > limit then
            return 0  -- 配额不足
        end

        redis.call('INCRBY', key, amount)
        redis.call('EXPIRE', key, 86400)
        return 1  -- 成功
        """

        quota_limits = {
            'CHAT_COUNT': 100,
            'API_CALLS': 1000,
            'TOKEN_COUNT': 100000,
        }

        limit = quota_limits.get(resource_type, 0)
        if limit <= 0:
            return True  # 无限制

        result = client.eval(lua_script, 1, cache_key, limit, amount)

        if result == 1:
            # 异步同步到数据库（不阻塞）
            import asyncio
            asyncio.create_task(
                self._sync_quota_to_db_async(user_id, resource_type, amount)
            )
            return True
        else:
            logger.warning(f"配额扣减失败: {cache_key}")
            return False

    async def _sync_quota_to_db_async(self, user_id: int, resource_type: str, amount: int):
        """异步同步配额到数据库"""
        try:
            # 这个操作可以延迟，不影响主流程
            from app.models.quota_log import QuotaLog
            log = QuotaLog(
                user_id=user_id,
                resource_type=resource_type,
                amount=amount,
                operation='DEDUCT',
                synced_at=datetime.utcnow()
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.error(f"同步配额失败: {e}")
```

**修改Chat服务使用新配额系统** (chat_service.py):
```python
async def send_message(self, user_id: str, content: str, ...):
    """发送消息 - 使用Redis配额系统"""

    # ✅ 使用Redis配额检查（1-5ms）
    quota_service = QuotaService(self.db)
    if not quota_service.check_quota_redis('CHAT_COUNT', 1, int(user_id)):
        raise BusinessException("对话次数已用完")

    # ... 后续逻辑 ...

    # ✅ 使用Redis配额扣减（1-5ms）
    if not quota_service.deduct_quota_redis('TOKEN_COUNT', total_tokens, int(user_id)):
        raise BusinessException("Token配额不足")

    # ... 保存消息 ...
```

**预期效果**: 配额检查+扣减性能 ↑50-100倍 (从500ms降至5-10ms)

---

## 二、P1问题实施

### 2.1 Product N+1查询修复 (2小时)

**文件**: `backend/app/services/product_service.py`

检查所有查询方法是否使用了`joinedload`:

```python
# 检查清单
- get_product_by_id() - 添加 joinedload(Product.creator)
- get_product_by_name() - 添加 joinedload(Product.creator)
- list_products() - 已有，验证是否在搜索路径也有
- search_products() - 添加 joinedload
```

---

### 2.2 异步I/O优化 (8小时 - 高级)

使用`run_in_executor`改进chat_service:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

db_executor = ThreadPoolExecutor(max_workers=10)

class ChatService:
    async def send_message_optimized(self, user_id: str, content: str, ...):
        """优化的异步消息发送"""

        loop = asyncio.get_event_loop()

        # 异步执行数据库查询
        quota = await loop.run_in_executor(
            db_executor,
            lambda: self._get_or_create_quota(int(user_id))
        )

        if not quota.can_chat():
            raise BusinessException("对话次数已用完")

        # 并行执行
        conv, _ = await asyncio.gather(
            loop.run_in_executor(
                db_executor,
                lambda: self._get_or_create_conversation(int(user_id), ...)
            ),
            loop.run_in_executor(
                db_executor,
                lambda: self._save_user_message(...)
            )
        )

        # 调用AI
        client = await get_deepseek_client()
        response = await client.chat_completion(...)

        # 异步保存
        await loop.run_in_executor(
            db_executor,
            lambda: self._save_assistant_message(response)
        )

        return response
```

---

## 三、测试和验证

### 性能基准测试脚本

**文件**: `scripts/perf_benchmark.py`

```python
#!/usr/bin/env python3
"""性能基准测试"""

import requests
import time
import statistics
from typing import List, Tuple

BASE_URL = "http://localhost:8000"
TOKEN = "your-test-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def measure_endpoint(method: str, endpoint: str, data: dict = None,
                    iterations: int = 100) -> Tuple[float, float, float]:
    """测试单个端点的性能"""

    times = []

    for _ in range(iterations):
        start = time.time()

        if method == "GET":
            requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
        elif method == "POST":
            requests.post(f"{BASE_URL}{endpoint}", json=data, headers=HEADERS)

        elapsed = time.time() - start
        times.append(elapsed * 1000)  # 转换为毫秒

    avg = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)

    return avg, min_time, max_time

def run_benchmarks():
    """运行所有基准测试"""

    print("=" * 60)
    print("性能基准测试")
    print("=" * 60)

    endpoints = [
        ("GET", "/api/chat/conversations", None),
        ("GET", "/api/products", None),
        ("POST", "/api/chat/message", {"content": "test"}),
        ("GET", "/api/users/profile", None),
    ]

    for method, endpoint, data in endpoints:
        print(f"\n测试: {method} {endpoint}")
        avg, min_t, max_t = measure_endpoint(method, endpoint, data)

        print(f"  平均: {avg:.2f}ms")
        print(f"  最小: {min_t:.2f}ms")
        print(f"  最大: {max_t:.2f}ms")

if __name__ == "__main__":
    run_benchmarks()
```

**执行**:
```bash
python scripts/perf_benchmark.py
```

---

### 数据库查询计数验证

在conftest.py中添加:

```python
@pytest.fixture
def count_queries(db: Session):
    """计数数据库查询"""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    count = 0

    @event.listens_for(Engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
        nonlocal count
        count += 1

    yield lambda: count

    @event.listens_for(Engine, "before_cursor_execute", remove=True)
    def remove_listener(*args, **kwargs):
        pass
```

**测试**:
```python
def test_conversation_detail_query_count(db: Session, count_queries):
    """验证对话详情查询数"""

    service = ChatService(db)
    conversation_id = "test-conv-123"

    initial_count = count_queries()
    result = service.get_conversation_detail(conversation_id, "user-123")
    final_count = count_queries()

    query_count = final_count - initial_count

    # 优化前: 100+
    # 优化后: 2-3
    assert query_count <= 3, f"期望 <= 3 queries, 实际 {query_count}"

    print(f"✓ 查询数: {query_count} (期望 <= 3)")
```

---

## 四、部署清单

### 发布前检查

- [ ] 所有P0问题已修复
- [ ] 数据库迁移脚本已验证
- [ ] 索引已在测试环境创建
- [ ] 缓存预热逻辑已添加
- [ ] 性能基准测试通过（↑50%以上）
- [ ] Redis连接正常
- [ ] 错误日志无异常
- [ ] 负载测试通过（1000+并发）

### 灰度发布计划

1. **5%流量** (第1天) - 监控错误率
2. **25%流量** (第2天) - 验证性能提升
3. **50%流量** (第3天) - 观察生产数据
4. **100%流量** (第4天) - 全量发布

---

## 五、回滚方案

如果性能优化导致问题，可以快速回滚：

```bash
# 数据库回滚
alembic downgrade -1

# 代码回滚
git revert <commit-hash>

# 缓存清空
redis-cli FLUSHDB

# 重启应用
docker restart app-container
```

---

## 总结

按照此指南执行P0问题修复，预期可在**1周内**实现**3-5倍**的性能提升。

关键改进点：
- 数据库连接池优化
- 添加缺失索引
- 解决N+1查询
- 实现认证缓存
- 使用Redis配额系统

首先在测试环境验证，然后灰度发布到生产环境。
