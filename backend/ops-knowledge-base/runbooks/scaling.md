# 服务扩容操作手册 (Scaling Runbook)

## 概述

本手册描述了服务的水平扩容、垂直扩容、缩容的标准流程和注意事项。

---

## 扩容决策

### 何时需要扩容?

**水平扩容** (增加实例数):
- QPS超过单实例处理能力 (>1000 QPS)
- CPU使用率持续 > 70%
- 响应时间持续 > 500ms
- 流量预计持续增长

**垂直扩容** (增加资源):
- 内存使用率持续 > 80%
- 单实例性能瓶颈
- 数据集过大,需要更多内存

### 扩容容量规划

```bash
# 当前容量
当前QPS: 800
单实例容量: 1000 QPS
当前实例数: 1

# 扩容目标
预计峰值QPS: 5000
安全系数: 1.5
所需实例数 = 5000 * 1.5 / 1000 = 8
```

---

## 水平扩容 (Scale Out)

### Docker Compose 扩容

```bash
# 1. 扩容到3个实例
docker-compose up -d --scale backend=3 --no-recreate

# 2. 验证所有实例正常
docker ps | grep backend

# 3. 检查健康状态
for port in 8000 8001 8002; do
    curl -f http://localhost:$port/health || echo "Port $port failed"
done

# 4. 配置负载均衡 (Nginx)
# nginx.conf
upstream backend {
    least_conn;  # 最少连接数算法
    server backend_1:8000 weight=1;
    server backend_2:8000 weight=1;
    server backend_3:8000 weight=1;
}

# 5. 重载Nginx配置
docker exec nginx nginx -s reload

# 6. 验证负载均衡
for i in {1..10}; do
    curl -s http://localhost/api/v1/health | jq -r '.instance_id'
done
```

### Kubernetes 扩容

```bash
# 1. 扩容 Deployment
kubectl scale deployment backend --replicas=3

# 2. 查看扩容进度
kubectl rollout status deployment/backend

# 3. 验证Pod状态
kubectl get pods -l app=backend

# 4. 验证Service负载均衡
kubectl get endpoints backend
```

### 自动扩容 (HPA)

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

# 应用配置
kubectl apply -f hpa.yaml

# 查看自动扩容状态
kubectl get hpa
```

---

## 垂直扩容 (Scale Up)

### 增加容器资源限制

```yaml
# docker-compose.yml

# 修改前
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

# 修改后
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G

# 应用变更
docker-compose up -d backend
```

### 数据库垂直扩容

```yaml
# 增加PostgreSQL资源
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
    shm_size: 1g  # 增加共享内存

# 优化PostgreSQL配置
# postgresql.conf
shared_buffers = 2GB       # 内存的25%
effective_cache_size = 6GB # 内存的75%
work_mem = 16MB
maintenance_work_mem = 512MB
max_connections = 200
```

---

## 缩容 (Scale Down)

### 何时缩容?

- 流量高峰过去
- 资源利用率持续 < 30%
- 成本优化需求

### 安全缩容步骤

```bash
# 1. 观察流量趋势 (确保不是临时下降)
curl 'http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[5m])&start='$(date -d '24 hours ago' +%s)'&end='$(date +%s)'&step=300'

# 2. 逐步缩容 (不要一次性缩容)
docker-compose up -d --scale backend=2

# 3. 观察性能指标 (5-10分钟)
# - CPU使用率 < 70%
# - 内存使用率 < 80%
# - 响应时间 < 500ms

# 4. 确认无问题后继续缩容
docker-compose up -d --scale backend=1

# 5. 持续监控 (30分钟)
```

---

## 数据库扩容

### 读写分离

```yaml
# docker-compose.yml
services:
  postgres-master:
    image: postgres:15
    environment:
      - POSTGRES_USER=ai_platform
      - POSTGRES_PASSWORD=secret
    volumes:
      - ./postgres/master.conf:/etc/postgresql/postgresql.conf

  postgres-replica:
    image: postgres:15
    environment:
      - POSTGRES_USER=ai_platform
      - POSTGRES_PASSWORD=secret
    volumes:
      - ./postgres/replica.conf:/etc/postgresql/postgresql.conf
    depends_on:
      - postgres-master

# 应用配置 (读写分离)
# app/core/database.py
from sqlalchemy import create_engine

# 写库
engine_write = create_engine(MASTER_DATABASE_URL)

# 读库
engine_read = create_engine(REPLICA_DATABASE_URL)
```

### 数据库连接池扩容

```python
# app/core/database.py

# 修改前
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=0
)

# 修改后 (根据并发量调整)
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # 基础连接池
    max_overflow=10,     # 溢出连接
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

---

## 扩容验证

### 性能测试

```bash
# 使用 wrk 进行压测
wrk -t12 -c400 -d30s --latency http://localhost/api/v1/users

# 输出示例:
# Running 30s test @ http://localhost/api/v1/users
#   12 threads and 400 connections
#   Thread Stats   Avg      Stdev     Max   +/- Stdev
#     Latency   150.23ms   75.12ms   2.00s    87.23%
#     Req/Sec   220.45     50.23   350.00     65.45%
#   79234 requests in 30.00s, 12.34MB read
# Requests/sec: 2641.13
# Transfer/sec: 420.45KB

# 判断标准:
# - P95 延迟 < 500ms ✅
# - 错误率 < 1% ✅
# - QPS达到预期 ✅
```

### 监控指标验证

```bash
# 1. CPU使用率 (应该下降)
curl 'http://localhost:9090/api/v1/query?query=avg(rate(container_cpu_usage_seconds_total{container="backend"}[5m]))'

# 2. 内存使用率 (应该保持稳定)
curl 'http://localhost:9090/api/v1/query?query=avg(container_memory_usage_bytes{container="backend"})'

# 3. 响应时间 (应该下降)
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, http_request_duration_seconds_bucket)'

# 4. QPS (应该能承载更多)
curl 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])'
```

---

## 扩容最佳实践

### 1. 渐进式扩容
- 不要一次性扩容太多
- 每次扩容后观察5-10分钟
- 确认稳定后再继续

### 2. 监控指标
- 扩容前记录基线指标
- 扩容后对比指标变化
- 验证扩容效果

### 3. 成本优化
- 使用自动扩缩容 (HPA)
- 在非高峰期缩容
- 定期审查资源利用率

### 4. 容量规划
- 提前规划,不要等到告警才扩容
- 预留30%冗余
- 定期进行容量评估

---

## 扩容检查清单

### 扩容前
- [ ] 确认扩容必要性 (资源使用率、QPS)
- [ ] 制定扩容方案 (水平/垂直、目标规模)
- [ ] 备份当前配置
- [ ] 通知相关人员

### 扩容中
- [ ] 执行扩容操作
- [ ] 验证新实例健康
- [ ] 配置负载均衡
- [ ] 观察监控指标

### 扩容后
- [ ] 性能测试验证
- [ ] 持续监控 (30分钟)
- [ ] 更新配置文档
- [ ] 记录扩容日志

---

## 常见问题

### Q1: 扩容后性能没有提升?

**可能原因**:
- 瓶颈在数据库,而不是应用
- 负载均衡配置错误
- 单个实例已达性能上限

**排查方法**:
```bash
# 检查负载均衡是否生效
for i in {1..20}; do
    curl -s http://localhost/api/v1/health | jq -r '.instance_id'
done | sort | uniq -c

# 检查数据库负载
docker exec postgres psql -U ai_platform -c "SELECT * FROM pg_stat_activity;"

# 检查是否有慢查询
docker exec postgres psql -U ai_platform -c "
SELECT query, mean_exec_time FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;
"
```

### Q2: 扩容后内存使用不均衡?

**可能原因**:
- 负载均衡算法不合适
- 某些实例处理更复杂请求
- 缓存未共享

**解决方案**:
```yaml
# 使用 least_conn 算法
upstream backend {
    least_conn;
    server backend_1:8000;
    server backend_2:8000;
}

# 共享缓存 (使用Redis)
# 不要使用进程内缓存
```

---

## 相关文档

- [部署操作手册](./deployment.md)
- [性能优化指南](./performance-tuning.md)
- [监控指标说明](../../docs/MONITORING.md)
