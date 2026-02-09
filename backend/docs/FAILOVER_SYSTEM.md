# AI服务商故障转移机制

## 概述

本系统实现了完整的AI服务商故障转移机制，确保在单个Provider出现故障时能够自动切换到备用Provider，保证服务的高可用性。

## 核心功能

### 1. 故障检测
- **定期健康检查**：每60秒自动检查所有Provider的健康状态
- **响应时间监控**：实时监控API响应时间
- **错误率统计**：跟踪每个Provider的错误率
- **熔断器模式**：连续失败达到阈值时自动开启熔断器

### 2. 故障转移策略
支持多种故障转移策略：

#### 主备模式（Primary-Backup）
- 优先使用优先级最高的Provider
- 主Provider故障时自动切换到备用Provider
- 适用场景：有明确的主备关系

#### 轮询模式（Round-Robin）
- 在所有健康的Provider之间轮询
- 平均分配负载
- 适用场景：多个Provider性能相近

#### 加权轮询（Weighted Round-Robin）
- 根据优先级权重进行轮询
- 高优先级Provider获得更多请求
- 适用场景：Provider性能差异较大

#### 最少连接（Least Connections）
- 选择当前请求数最少的Provider
- 动态负载均衡
- 适用场景：请求处理时间差异大

#### 基于优先级（Priority-Based，推荐）
- 综合考虑优先级、健康状态、响应时间、错误率
- 智能选择最优Provider
- 适用场景：大多数生产环境

### 3. 监控和告警
- **实时监控**：监控所有Provider的健康状态和性能指标
- **多渠道告警**：支持邮件、Webhook、短信告警
- **告警级别**：INFO、WARNING、ERROR、CRITICAL
- **告警频率限制**：避免告警风暴

### 4. 配置管理
- **优先级配置**：设置Provider优先级（0-100）
- **启用/禁用**：动态启用或禁用Provider
- **统计重置**：重置Provider统计信息
- **推荐配置**：基于性能指标自动推荐优先级

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     AIProviderFactory                        │
│  - 创建Provider实例                                          │
│  - 集成故障转移逻辑                                          │
│  - 自动重试和切换                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│HealthChecker │ │FailoverMgr   │ │  Monitor     │
│ - 健康检查   │ │ - 策略选择   │ │ - 实时监控   │
│ - 熔断器     │ │ - 故障转移   │ │ - 告警通知   │
└──────────────┘ └──────────────┘ └──────────────┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │   TenantAIConfig       │
        │  - 配置信息            │
        │  - 健康状态            │
        │  - 统计数据            │
        └────────────────────────┘
```

## 数据库设计

### 新增字段（tenant_ai_configs表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| priority | INT | 优先级（0-100） |
| health_status | VARCHAR(20) | 健康状态：healthy/degraded/unhealthy |
| last_check_time | DATETIME | 最后健康检查时间 |
| error_count | INT | 连续错误计数 |
| total_requests | BIGINT | 总请求数 |
| failed_requests | BIGINT | 失败请求数 |
| avg_response_time | FLOAT | 平均响应时间（毫秒） |
| last_error_message | TEXT | 最后错误信息 |
| last_error_time | DATETIME | 最后错误时间 |
| circuit_breaker_open_until | DATETIME | 熔断器开启截止时间 |

## 使用指南

### 1. 基本使用

```python
from sqlalchemy.orm import Session
from app.services.ai.factory import AIProviderFactory
from app.services.ai.base_provider import ChatCompletionRequest, ChatMessage
from app.services.ai.failover import FailoverStrategy

# 带故障转移的对话请求
async def chat_with_ai(db: Session, enterprise_id: int, user_message: str):
    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=user_message)],
        temperature=0.7,
        max_tokens=2000
    )

    # 自动故障转移和重试
    response, config = await AIProviderFactory.chat_with_failover(
        db=db,
        enterprise_id=enterprise_id,
        request=request,
        strategy=FailoverStrategy.PRIORITY_BASED,
        max_retries=3
    )

    return response.content
```

### 2. 流式对话

```python
# 带故障转移的流式对话
async def chat_stream_with_ai(db: Session, enterprise_id: int, user_message: str):
    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=user_message)],
        temperature=0.7,
        max_tokens=2000,
        stream=True
    )

    async for chunk in AIProviderFactory.chat_stream_with_failover(
        db=db,
        enterprise_id=enterprise_id,
        request=request,
        strategy=FailoverStrategy.PRIORITY_BASED,
        max_retries=3
    ):
        yield chunk
```

### 3. 健康检查

```python
from app.services.ai.health_checker import HealthChecker

# 启动定期健康检查
async def start_health_check(db: Session):
    checker = HealthChecker(db)
    await checker.start_periodic_check()

# 手动检查单个Provider
async def check_provider(db: Session, config_id: int):
    checker = HealthChecker(db)
    config = db.query(TenantAIConfig).filter(TenantAIConfig.id == config_id).first()
    api_key = config.api_key_encrypted  # TODO: 解密
    is_healthy = await checker.check_provider_health(config, api_key)
    return is_healthy
```

### 4. 监控和告警

```python
from app.services.ai.monitor import Monitor

# 启动定期监控
async def start_monitoring(db: Session):
    monitor = Monitor(db)
    await monitor.start_periodic_monitoring(interval=60)

# 获取监控摘要
def get_monitoring_summary(db: Session, enterprise_id: int):
    monitor = Monitor(db)
    return monitor.get_monitoring_summary(enterprise_id)
```

### 5. 配置管理

```python
from app.services.ai.config_manager import ConfigManager

# 设置Provider优先级
def set_priority(db: Session, config_id: int, priority: int):
    manager = ConfigManager(db)
    return manager.set_provider_priority(config_id, priority)

# 应用推荐的优先级配置
def apply_recommended_priorities(db: Session, enterprise_id: int):
    manager = ConfigManager(db)
    return manager.apply_recommended_priorities(enterprise_id)

# 重置Provider统计
def reset_statistics(db: Session, config_id: int):
    manager = ConfigManager(db)
    return manager.reset_provider_statistics(config_id)
```

## 配置参数

### 健康检查配置

```python
class HealthCheckConfig:
    CHECK_INTERVAL = 60  # 检查间隔（秒）
    TIMEOUT = 10  # 超时时间（秒）
    RESPONSE_TIME_THRESHOLD = 5000  # 响应时间阈值（毫秒）
    ERROR_RATE_THRESHOLD = 20  # 错误率阈值（百分比）
    CONSECUTIVE_ERROR_THRESHOLD = 3  # 连续错误阈值
    CIRCUIT_BREAKER_DURATION = 300  # 熔断器开启时长（秒）
```

### 监控配置

```python
class MonitorConfig:
    ERROR_RATE_WARNING_THRESHOLD = 10  # 错误率警告阈值（百分比）
    ERROR_RATE_CRITICAL_THRESHOLD = 30  # 错误率严重阈值（百分比）
    RESPONSE_TIME_WARNING_THRESHOLD = 3000  # 响应时间警告阈值（毫秒）
    RESPONSE_TIME_CRITICAL_THRESHOLD = 5000  # 响应时间严重阈值（毫秒）
    ALERT_COOLDOWN = 300  # 告警冷却时间（秒）
```

## 最佳实践

### 1. Provider配置建议

- **至少配置2个Provider**：确保有备用Provider
- **设置合理的优先级**：主Provider优先级80-100，备用Provider 50-70
- **定期检查配置**：确保API密钥有效

### 2. 监控建议

- **启用定期健康检查**：建议60秒间隔
- **配置告警通知**：及时发现和处理故障
- **定期查看监控摘要**：了解系统整体健康状况

### 3. 故障处理流程

1. **自动检测**：健康检查发现Provider故障
2. **自动切换**：故障转移到备用Provider
3. **发送告警**：通知管理员
4. **自动恢复**：熔断器过期后尝试恢复
5. **人工介入**：如果自动恢复失败，需要人工处理

### 4. 性能优化

- **使用推荐的优先级配置**：基于实际性能数据优化
- **定期重置统计**：避免历史数据影响决策
- **合理设置重试次数**：平衡可用性和响应时间

## 故障场景处理

### 场景1：单个Provider故障

```
1. 健康检查发现Provider A响应超时
2. 错误计数增加，健康状态变为DEGRADED
3. 连续失败3次后，健康状态变为UNHEALTHY
4. 连续失败5次后，开启熔断器
5. 后续请求自动切换到Provider B
6. 发送告警通知管理员
7. 5分钟后熔断器过期，尝试恢复
8. 如果恢复成功，关闭熔断器；否则延长熔断时间
```

### 场景2：所有Provider故障

```
1. 健康检查发现所有Provider都不可用
2. 请求失败，返回错误信息
3. 发送严重告警
4. 系统持续尝试恢复
5. 需要人工介入检查网络、API密钥等
```

### 场景3：Provider性能下降

```
1. 监控发现Provider A响应时间增加
2. 健康状态变为DEGRADED
3. 发送警告告警
4. 故障转移策略自动降低其权重
5. 更多请求分配到其他Provider
6. 如果性能恢复，自动恢复权重
```

## 数据库迁移

```bash
# 运行迁移
cd backend
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 监控指标

### Provider级别指标

- **健康状态**：healthy/degraded/unhealthy
- **总请求数**：total_requests
- **失败请求数**：failed_requests
- **错误率**：failed_requests / total_requests * 100
- **平均响应时间**：avg_response_time（毫秒）
- **连续错误数**：error_count
- **熔断器状态**：is_circuit_breaker_open

### 企业级别指标

- **总Provider数**：total_providers
- **活跃Provider数**：active_providers
- **健康Provider数**：healthy_providers
- **降级Provider数**：degraded_providers
- **不健康Provider数**：unhealthy_providers
- **总体错误率**：overall_error_rate
- **总体平均响应时间**：overall_avg_response_time

## 文件清单

### 核心文件

1. **数据库迁移**
   - `backend/alembic/versions/005_add_failover_support.py`

2. **模型**
   - `backend/app/models/tenant_ai_config.py`（已更新）

3. **服务**
   - `backend/app/services/ai/health_checker.py` - 健康检查服务
   - `backend/app/services/ai/failover.py` - 故障转移策略
   - `backend/app/services/ai/monitor.py` - 监控和告警
   - `backend/app/services/ai/config_manager.py` - 配置管理
   - `backend/app/services/ai/factory.py`（已更新）- Provider工厂

## 注意事项

1. **API密钥加密**：当前代码中API密钥解密部分标记为TODO，需要实现加密服务
2. **Webhook配置**：告警Webhook URL需要从企业配置中获取
3. **邮件/短信服务**：需要配置邮件和短信服务提供商
4. **定期任务**：需要在应用启动时启动健康检查和监控任务
5. **数据库连接**：确保数据库会话正确管理，避免连接泄漏

## 后续优化

1. **实现API密钥加密/解密服务**
2. **集成邮件和短信服务**
3. **添加Web界面管理配置**
4. **实现更多故障转移策略**
5. **添加性能分析和报表功能**
6. **支持自定义告警规则**
7. **实现Provider自动发现和注册**

## 技术支持

如有问题，请联系技术团队或查看详细文档。
