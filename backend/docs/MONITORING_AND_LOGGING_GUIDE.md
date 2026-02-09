# 监控和日志系统使用指南

本文档提供完整的监控和日志系统部署、配置和使用指南。

## 目录
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [日志收集 (ELK Stack)](#日志收集-elk-stack)
- [监控告警 (Prometheus + Grafana)](#监控告警-prometheus--grafana)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                         监控和日志系统                        │
└──────────────────────────────────────────────────────────────┘

日志流 (ELK Stack):
  Application Logs → Filebeat → Logstash → Elasticsearch → Kibana
       ↓
  Docker Logs   → Filebeat → Logstash → Elasticsearch → Kibana

监控流 (Prometheus + Grafana):
  System Metrics → Node Exporter → Prometheus → Grafana
  Container Metrics → cAdvisor → Prometheus → Grafana
  App Metrics → FastAPI → Prometheus → Grafana
       ↓
  Prometheus → Alertmanager → Webhooks/Email/Slack
```

---

## 快速开始

### 1. 启动监控和日志服务

```bash
# 进入backend目录
cd backend

# 启动所有监控和日志服务
docker-compose -f docker-compose.monitoring.yml up -d

# 查看服务状态
docker-compose -f docker-compose.monitoring.yml ps

# 查看日志
docker-compose -f docker-compose.monitoring.yml logs -f
```

### 2. 访问Web界面

| 服务 | URL | 默认账号 | 说明 |
|-----|-----|---------|-----|
| Kibana | http://localhost:5601 | - | 日志查询和可视化 |
| Grafana | http://localhost:3000 | admin/admin123 | 监控仪表盘 |
| Prometheus | http://localhost:9090 | - | 监控指标查询 |
| Alertmanager | http://localhost:9093 | - | 告警管理 |
| Elasticsearch | http://localhost:9200 | - | 日志存储 |

### 3. 停止服务

```bash
# 停止服务
docker-compose -f docker-compose.monitoring.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.monitoring.yml down -v
```

---

## 日志收集 (ELK Stack)

### 架构组件

1. **Filebeat** - 日志采集器
   - 采集应用日志 (`./logs/*.log`)
   - 采集Docker容器日志
   - 自动添加元数据

2. **Logstash** - 日志处理器
   - 解析JSON格式日志
   - 提取日志级别
   - 丰富日志字段

3. **Elasticsearch** - 日志存储
   - 索引日志数据
   - 提供全文搜索
   - 数据持久化

4. **Kibana** - 日志可视化
   - 日志查询界面
   - 创建仪表盘
   - 告警配置

### 配置日志格式

应用程序需要使用JSON格式输出日志以获得最佳体验：

```python
# Python日志配置示例
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# 配置日志处理器
handler = logging.FileHandler("logs/app.log")
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)
```

### Kibana使用指南

#### 创建索引模式

1. 打开 Kibana (http://localhost:5601)
2. 导航到 "Management" → "Stack Management" → "Index Patterns"
3. 点击 "Create index pattern"
4. 输入索引模式: `ai-platform-*`
5. 选择时间字段: `@timestamp`
6. 点击 "Create index pattern"

#### 查询日志

1. 导航到 "Discover"
2. 选择索引模式: `ai-platform-*`
3. 使用KQL (Kibana Query Language) 查询：
   ```
   # 查询错误日志
   log_level: "ERROR"

   # 查询特定模块日志
   module: "billing_engine"

   # 组合查询
   log_level: "ERROR" AND module: "risk_control"

   # 时间范围查询
   @timestamp >= "now-1h"
   ```

#### 创建可视化

1. 导航到 "Visualize"
2. 点击 "Create visualization"
3. 选择图表类型（折线图、柱状图、饼图等）
4. 选择索引模式
5. 配置指标和分组
6. 保存可视化

#### 创建仪表盘

1. 导航到 "Dashboard"
2. 点击 "Create dashboard"
3. 添加已创建的可视化
4. 调整布局
5. 保存仪表盘

### 常用日志查询示例

```kql
# 查询过去1小时的错误日志
log_level: "ERROR" AND @timestamp >= "now-1h"

# 查询特定用户的操作日志
user_id: "12345"

# 查询慢请求（响应时间>2秒）
response_time > 2000

# 查询特定API端点的日志
path: "/api/v1/billing/*"

# 查询包含异常的日志
exception: *

# 查询特定容器的日志
container.name: "ai-platform-backend"
```

---

## 监控告警 (Prometheus + Grafana)

### 架构组件

1. **Prometheus** - 监控数据收集
   - 定期抓取指标
   - 存储时间序列数据
   - 评估告警规则

2. **Node Exporter** - 系统指标
   - CPU使用率
   - 内存使用率
   - 磁盘IO
   - 网络流量

3. **cAdvisor** - 容器指标
   - 容器CPU使用率
   - 容器内存使用率
   - 容器网络流量
   - 容器文件系统

4. **Grafana** - 监控可视化
   - 创建仪表盘
   - 图表展示
   - 告警通知

5. **Alertmanager** - 告警管理
   - 告警路由
   - 告警分组
   - 告警通知（邮件、Webhook、Slack）

### 应用程序集成Prometheus

在FastAPI应用中添加Prometheus客户端：

```python
# requirements.txt
prometheus-client==0.19.0

# app/main.py
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from fastapi import FastAPI

app = FastAPI()

# 定义指标
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

# 添加中间件记录指标
@app.middleware("http")
async def prometheus_middleware(request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response

# 添加/metrics端点
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

### Grafana使用指南

#### 登录Grafana

1. 打开 Grafana (http://localhost:3000)
2. 使用默认账号登录: `admin/admin123`
3. 首次登录建议修改密码

#### 配置数据源

数据源已经通过配置文件自动添加（Prometheus），无需手动配置。

#### 导入预制仪表盘

1. 导航到 "Dashboards" → "Import"
2. 输入仪表盘ID或上传JSON文件
3. 推荐的仪表盘：
   - Node Exporter Full (ID: 1860)
   - Docker and System Monitoring (ID: 893)
   - FastAPI Observability (ID: 16110)

#### 创建自定义仪表盘

1. 导航到 "Dashboards" → "New Dashboard"
2. 点击 "Add new panel"
3. 编写PromQL查询：
   ```promql
   # CPU使用率
   100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

   # 内存使用率
   (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

   # HTTP请求速率
   rate(http_requests_total[5m])

   # HTTP错误率
   rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

   # P95响应时间
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```
4. 选择可视化类型（时间序列、仪表盘、表格等）
5. 配置阈值和告警
6. 保存面板

### 告警配置

#### Prometheus告警规则

告警规则已配置在 `monitoring/prometheus/rules/alerts.yml`，包括：

- **系统告警**:
  - CPU使用率过高 (>80%)
  - 内存使用率过高 (>85%)
  - 磁盘空间不足 (<15%)

- **容器告警**:
  - 容器频繁重启
  - 容器CPU使用率过高
  - 容器内存使用率过高

- **应用告警**:
  - 应用响应时间过长 (>2秒)
  - 错误率过高 (>5%)
  - 服务不可用

#### 配置告警通知

编辑 `monitoring/alertmanager/config.yml` 配置通知方式：

```yaml
# 邮件通知
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'

# Slack通知
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

# Webhook通知
  - name: 'webhook'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/webhooks/alerts'
        send_resolved: true
```

#### Grafana告警

1. 编辑仪表盘面板
2. 切换到 "Alert" 标签
3. 点击 "Create alert"
4. 配置告警条件：
   ```
   WHEN avg() OF query(A, 5m, now) IS ABOVE 80
   ```
5. 配置通知渠道
6. 保存告警

### 常用PromQL查询

```promql
# 系统监控
# CPU使用率
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# 磁盘使用率
(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100

# 网络流量
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# 容器监控
# 容器CPU使用率
sum(rate(container_cpu_usage_seconds_total{name=~".+"}[5m])) by (name) * 100

# 容器内存使用率
(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100

# 容器网络流量
rate(container_network_receive_bytes_total[5m])
rate(container_network_transmit_bytes_total[5m])

# 应用监控
# QPS (每秒请求数)
rate(http_requests_total[1m])

# 错误率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# P50/P90/P95/P99响应时间
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.90, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# 平均响应时间
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

---

## 常见问题

### Q1: Elasticsearch启动失败，提示内存不足

**A:** 调整Elasticsearch的JVM堆内存：

```yaml
# docker-compose.monitoring.yml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms256m -Xmx256m"  # 降低内存使用
```

### Q2: Filebeat无法连接到Logstash

**A:** 检查网络配置和服务状态：

```bash
# 检查Logstash是否运行
docker ps | grep logstash

# 检查Filebeat日志
docker logs ai-platform-filebeat

# 测试Logstash端口
nc -zv localhost 5044
```

### Q3: Prometheus无法抓取应用指标

**A:** 确保应用已集成Prometheus客户端并暴露/metrics端点：

```bash
# 测试metrics端点
curl http://localhost:8001/metrics

# 检查Prometheus targets
# 访问 http://localhost:9090/targets
```

### Q4: Grafana仪表盘显示"No Data"

**A:** 检查数据源配置和PromQL查询：

1. 验证Prometheus数据源: Grafana → Configuration → Data Sources
2. 测试查询: Grafana → Explore → 输入PromQL查询
3. 检查时间范围是否正确

### Q5: 告警没有发送通知

**A:** 检查Alertmanager配置和通知渠道：

```bash
# 查看Alertmanager日志
docker logs ai-platform-alertmanager

# 测试告警规则
# 访问 http://localhost:9093/#/alerts

# 检查通知配置
cat monitoring/alertmanager/config.yml
```

---

## 最佳实践

### 日志管理

1. **日志格式标准化**
   - 使用JSON格式
   - 包含时间戳、级别、模块、消息
   - 添加请求ID用于追踪

2. **日志级别使用**
   - DEBUG: 开发调试信息
   - INFO: 正常业务操作
   - WARNING: 警告信息但不影响业务
   - ERROR: 错误信息需要关注
   - CRITICAL: 严重错误需要立即处理

3. **日志轮转**
   - 每天轮转日志文件
   - 保留最近30天的日志
   - 压缩历史日志

4. **敏感信息处理**
   - 不记录密码、token等敏感信息
   - 对敏感字段进行脱敏处理

### 监控指标

1. **关键指标 (RED Method)**
   - **R**ate: 请求速率
   - **E**rrors: 错误率
   - **D**uration: 响应时间

2. **资源指标 (USE Method)**
   - **U**tilization: 利用率
   - **S**aturation: 饱和度
   - **E**rrors: 错误

3. **业务指标**
   - 活跃用户数
   - 交易金额
   - 转化率
   - 关键业务流程耗时

### 告警策略

1. **告警分级**
   - Critical: 立即处理（如服务宕机）
   - Warning: 需要关注（如CPU使用率高）
   - Info: 信息通知

2. **告警降噪**
   - 设置合理的告警阈值
   - 配置告警抑制规则
   - 避免告警风暴

3. **告警响应**
   - 定义清晰的告警处理流程
   - 记录告警处理结果
   - 定期回顾和优化告警规则

### 性能优化

1. **Elasticsearch优化**
   - 定期清理旧索引
   - 优化索引mapping
   - 配置合适的分片数

2. **Prometheus优化**
   - 调整抓取间隔
   - 设置合理的保留时间
   - 使用recording rules预计算

3. **Grafana优化**
   - 使用变量简化查询
   - 设置合理的刷新间隔
   - 缓存仪表盘数据

---

## 附录

### 端口列表

| 服务 | 端口 | 说明 |
|-----|------|-----|
| Elasticsearch | 9200, 9300 | 日志存储 |
| Logstash | 5044, 9600 | 日志处理 |
| Kibana | 5601 | 日志可视化 |
| Prometheus | 9090 | 监控数据收集 |
| Grafana | 3000 | 监控可视化 |
| Alertmanager | 9093 | 告警管理 |
| Node Exporter | 9100 | 系统指标 |
| cAdvisor | 8080 | 容器指标 |

### 数据持久化

所有数据都存储在Docker volumes中：

```bash
# 查看数据卷
docker volume ls | grep ai-platform

# 备份数据卷
docker run --rm -v backend_elasticsearch_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/elasticsearch_backup.tar.gz -C /data .

# 恢复数据卷
docker run --rm -v backend_elasticsearch_data:/data -v $(pwd)/backup:/backup alpine sh -c "cd /data && tar xzf /backup/elasticsearch_backup.tar.gz"
```

### 相关资源

- [Elasticsearch官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash官方文档](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana官方文档](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Prometheus官方文档](https://prometheus.io/docs/introduction/overview/)
- [Grafana官方文档](https://grafana.com/docs/grafana/latest/)
- [PromQL教程](https://prometheus.io/docs/prometheus/latest/querying/basics/)
