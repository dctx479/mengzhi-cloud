# 支付系统监控告警系统

完整的支付系统监控和告警解决方案，基于 Prometheus、Grafana 和 Alertmanager。

## 目录

- [系统架构](#系统架构)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [监控指标](#监控指标)
- [告警规则](#告警规则)
- [仪表板](#仪表板)
- [故障排查](#故障排查)
- [最佳实践](#最佳实践)

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      监控告警系统架构                        │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Backend    │────▶│  Prometheus  │────▶│   Grafana    │
│  (Metrics)   │     │  (采集/存储)  │     │  (可视化)    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Alertmanager │
                     │   (告警)     │
                     └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌────────┐         ┌────────┐         ┌────────┐
   │ Email  │         │Webhook │         │ Slack  │
   └────────┘         └────────┘         └────────┘
```

## 功能特性

### 核心功能

- ✅ **实时监控**: 15秒间隔采集支付系统指标
- ✅ **多维度指标**: 支付成功率、失败率、响应时间、金额分布等
- ✅ **智能告警**: 多级告警规则，自动抑制告警风暴
- ✅ **可视化仪表板**: 18个预配置面板，全面展示支付系统状态
- ✅ **安全监控**: 签名验证失败、金额不匹配等安全指标
- ✅ **多渠道通知**: Email、Webhook、Slack、企业微信等

### 监控范围

- 支付请求和响应
- 支付成功率和失败率
- 支付方式分布
- 签名验证
- 金额验证
- 配额发放
- 并发支付
- 系统资源
- 数据库性能

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 可用内存
- 至少 10GB 可用磁盘空间

### 安装步骤

#### 1. 克隆项目

```bash
cd E:\项目\数商\AI赋能云平台\monitoring
```

#### 2. 配置环境变量

编辑 `docker-compose.yml`，修改以下配置：

```yaml
# MySQL 配置
MYSQL_ROOT_PASSWORD: your_secure_password
MYSQL_PASSWORD: your_app_password

# Redis 配置
REDIS_PASSWORD: your_redis_password

# Grafana 配置
GF_SECURITY_ADMIN_PASSWORD: your_grafana_password
```

#### 3. 配置告警通知

编辑 `alertmanager/alertmanager.yml`，配置邮件服务器：

```yaml
global:
  smtp_from: 'your-email@example.com'
  smtp_smarthost: 'smtp.example.com:587'
  smtp_auth_username: 'your-email@example.com'
  smtp_auth_password: 'your-password'
```

#### 4. 启动监控系统

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 5. 访问监控界面

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

### 验证安装

#### 1. 检查 Prometheus 目标

访问 http://localhost:9090/targets，确保所有目标状态为 `UP`。

#### 2. 检查 Grafana 数据源

1. 登录 Grafana
2. 进入 Configuration → Data Sources
3. 确认 Prometheus 数据源连接正常

#### 3. 查看仪表板

1. 进入 Dashboards → Browse
2. 打开 "支付系统监控仪表板"
3. 确认数据正常显示

#### 4. 测试告警

```bash
# 触发测试告警
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "测试告警"
    }
  }]'
```

## 配置说明

### Prometheus 配置

文件位置: `prometheus/prometheus.yml`

#### 主要配置项

```yaml
global:
  scrape_interval: 15s  # 全局抓取间隔
  evaluation_interval: 15s  # 告警规则评估间隔

scrape_configs:
  - job_name: 'payment-system'
    scrape_interval: 5s  # 支付系统使用更高频率
    static_configs:
      - targets: ['backend:8000']
```

#### 热重载配置

```bash
# 方法1: 使用 API
curl -X POST http://localhost:9090/-/reload

# 方法2: 发送信号
docker-compose kill -s SIGHUP prometheus
```

### Grafana 配置

#### 数据源配置

文件位置: `grafana/datasources/prometheus.yml`

```yaml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
```

#### 仪表板配置

文件位置: `grafana/dashboards/payment-dashboard.json`

包含 18 个预配置面板：
- 支付成功率
- 支付请求量 (QPS)
- 支付失败率
- 支付响应时间
- 签名验证失败
- 金额验证失败
- 配额发放成功率
- 等等...

### Alertmanager 配置

文件位置: `alertmanager/alertmanager.yml`

#### 告警路由

```yaml
route:
  receiver: 'default'
  group_by: ['alertname', 'component', 'severity']
  routes:
    - match:
        severity: emergency
      receiver: 'emergency-team'
      group_wait: 10s
```

#### 告警接收器

支持多种通知方式：
- Email
- Webhook
- Slack
- 企业微信
- 钉钉

## 监控指标

### 支付核心指标

#### 1. 支付请求指标

| 指标名称 | 类型 | 说明 | 标签 |
|---------|------|------|------|
| `payment_requests_total` | Counter | 总支付请求数 | payment_method, status |
| `payment_success_total` | Counter | 成功支付数 | payment_method |
| `payment_failure_total` | Counter | 失败支付数 | payment_method, failure_reason |

#### 2. 支付金额指标

| 指标名称 | 类型 | 说明 | 标签 |
|---------|------|------|------|
| `payment_amount_total` | Counter | 总支付金额(元) | payment_method |
| `payment_amount_histogram` | Histogram | 支付金额分布 | payment_method |

#### 3. 支付响应时间

| 指标名称 | 类型 | 说明 | 标签 |
|---------|------|------|------|
| `payment_duration_seconds` | Histogram | 支付处理时间 | payment_method, operation |
| `payment_callback_duration_seconds` | Histogram | 回调处理时间 | payment_method |

#### 4. 安全指标

| 指标名称 | 类型 | 说明 | 标签 |
|---------|------|------|------|
| `payment_signature_verification_total` | Counter | 签名验证次数 | payment_method, result |
| `payment_signature_verification_failures` | Counter | 签名验证失败 | payment_method |
| `payment_amount_mismatch_total` | Counter | 金额不匹配次数 | payment_method |

#### 5. 配额指标

| 指标名称 | 类型 | 说明 | 标签 |
|---------|------|------|------|
| `quota_grant_total` | Counter | 配额发放次数 | quota_type, status |
| `quota_grant_duration_seconds` | Histogram | 配额发放时间 | quota_type |

#### 6. 状态指标

| 指标名称 | 类型 | 说明 |
|---------|------|------|
| `payment_pending_total` | Gauge | 待支付订单数 |
| `payment_processing_total` | Gauge | 处理中支付数 |
| `concurrent_payment_requests` | Gauge | 并发支付请求数 |
| `payment_success_rate` | Gauge | 支付成功率(%) |

### 查询示例

#### 计算支付成功率

```promql
(
  sum(rate(payment_success_total[5m])) by (payment_method)
  /
  sum(rate(payment_requests_total[5m])) by (payment_method)
) * 100
```

#### 计算 P95 响应时间

```promql
histogram_quantile(0.95,
  sum(rate(payment_duration_seconds_bucket{operation="create_payment"}[5m]))
  by (payment_method, le)
)
```

#### 计算每小时支付金额

```promql
sum(increase(payment_amount_total[1h])) by (payment_method)
```

## 告警规则

### 告警级别

| 级别 | 说明 | 响应时间 | 通知方式 |
|------|------|----------|----------|
| **emergency** | 紧急 | 立即 | Email + Webhook + 电话 |
| **critical** | 严重 | 5分钟内 | Email + Webhook |
| **warning** | 警告 | 30分钟内 | Email |
| **info** | 信息 | 无需响应 | 记录日志 |

### 关键告警规则

#### 1. 支付失败率过高

```yaml
- alert: HighPaymentFailureRate
  expr: |
    (sum(rate(payment_failure_total[5m])) by (payment_method)
     / sum(rate(payment_requests_total[5m])) by (payment_method)) * 100 > 5
  for: 2m
  labels:
    severity: critical
```

**触发条件**: 5分钟内失败率 > 5%
**持续时间**: 2分钟
**处理建议**:
1. 检查支付服务日志
2. 验证第三方支付接口状态
3. 检查网络连接
4. 查看数据库性能

#### 2. 签名验证失败过多

```yaml
- alert: HighSignatureVerificationFailures
  expr: |
    sum(rate(payment_signature_verification_failures[1m])) by (payment_method) > 10
  for: 2m
  labels:
    severity: critical
    security: true
```

**触发条件**: 1分钟内失败 > 10次
**持续时间**: 2分钟
**处理建议**:
1. 检查签名密钥配置
2. 验证回调数据格式
3. 检查是否存在攻击行为
4. 联系安全团队

#### 3. 支付金额不匹配

```yaml
- alert: PaymentAmountMismatch
  expr: |
    sum(rate(payment_amount_mismatch_total[5m])) by (payment_method) > 0
  for: 1m
  labels:
    severity: critical
    security: true
```

**触发条件**: 检测到任何金额不匹配
**持续时间**: 1分钟
**处理建议**:
1. 立即暂停相关支付方式
2. 检查订单和支付记录
3. 验证金额计算逻辑
4. 联系安全团队调查

#### 4. 支付处理缓慢

```yaml
- alert: SlowPaymentProcessing
  expr: |
    histogram_quantile(0.95,
      sum(rate(payment_duration_seconds_bucket{operation="create_payment"}[5m]))
      by (payment_method, le)
    ) > 5
  for: 5m
  labels:
    severity: warning
```

**触发条件**: P95 响应时间 > 5秒
**持续时间**: 5分钟
**处理建议**:
1. 检查数据库性能
2. 查看系统资源使用
3. 检查第三方接口响应时间
4. 考虑扩容

### 告警抑制规则

避免告警风暴，配置了智能抑制：

```yaml
inhibit_rules:
  # 紧急告警抑制严重告警
  - source_match:
      severity: 'emergency'
    target_match:
      severity: 'critical'
    equal: ['alertname', 'component']

  # 严重告警抑制警告告警
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'component']
```

## 仪表板

### 支付系统监控仪表板

#### 面板布局

```
┌─────────────────────────────────────────────────────────────┐
│  Row 1: 核心指标                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  支付成功率          │  │  支付请求量 (QPS)    │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Row 2: 失败分析                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  支付失败率          │  │  失败原因分布        │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Row 3: 性能指标                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  响应时间 (P95/P99)  │  │  支付金额分布        │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Row 4: 安全监控                                             │
│  ┌──────────────────────┐  ┌─────────┐  ┌─────────┐        │
│  │  签名验证失败        │  │金额不匹配│  │并发请求 │        │
│  └──────────────────────┘  └─────────┘  └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Row 5: 配额管理                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  配额发放成功率      │  │  配额发放响应时间    │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Row 6: 回调监控                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │  回调成功率          │  │  回调响应时间        │        │
│  └──────────────────────┘  └──────────────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Row 7: 业务统计                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │总支付额 │  │成功支付数│  │失败支付数│                     │
│  └─────────┘  └─────────┘  └─────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

#### 使用技巧

1. **时间范围选择**: 右上角可选择时间范围（默认1小时）
2. **自动刷新**: 设置为30秒自动刷新
3. **变量过滤**: 可按支付方式、时间段等过滤
4. **告警标记**: 面板上会显示告警阈值线
5. **数据导出**: 可导出为 CSV、JSON 等格式

## 故障排查

### 常见问题

#### 1. Prometheus 无法抓取指标

**症状**: Targets 页面显示 `DOWN` 状态

**排查步骤**:

```bash
# 1. 检查后端服务是否运行
docker-compose ps backend

# 2. 检查 /metrics 端点
curl http://localhost:8000/metrics

# 3. 检查网络连接
docker-compose exec prometheus ping backend

# 4. 查看 Prometheus 日志
docker-compose logs prometheus
```

**解决方案**:
- 确保后端服务正常运行
- 检查防火墙规则
- 验证 prometheus.yml 配置

#### 2. Grafana 无法连接 Prometheus

**症状**: 仪表板显示 "No Data"

**排查步骤**:

```bash
# 1. 测试数据源连接
# Grafana UI: Configuration → Data Sources → Test

# 2. 检查 Prometheus 是否正常
curl http://localhost:9090/api/v1/query?query=up

# 3. 查看 Grafana 日志
docker-compose logs grafana
```

**解决方案**:
- 重新配置数据源
- 检查 Prometheus URL
- 重启 Grafana 服务

#### 3. 告警未触发

**症状**: 满足告警条件但未收到通知

**排查步骤**:

```bash
# 1. 检查告警规则状态
# Prometheus UI: Alerts

# 2. 检查 Alertmanager 状态
curl http://localhost:9093/api/v1/status

# 3. 查看 Alertmanager 日志
docker-compose logs alertmanager

# 4. 测试告警规则
# Prometheus UI: Graph → 输入告警表达式
```

**解决方案**:
- 验证告警规则语法
- 检查 Alertmanager 配置
- 测试邮件服务器连接

#### 4. 指标数据不准确

**症状**: 仪表板显示异常数据

**排查步骤**:

```bash
# 1. 检查后端日志
docker-compose logs backend | grep metrics

# 2. 直接查询 Prometheus
curl 'http://localhost:9090/api/v1/query?query=payment_requests_total'

# 3. 检查时间同步
docker-compose exec backend date
docker-compose exec prometheus date
```

**解决方案**:
- 确保系统时间同步
- 检查指标采集代码
- 验证标签配置

### 性能优化

#### 1. 减少存储空间

```yaml
# prometheus.yml
command:
  - '--storage.tsdb.retention.time=15d'  # 减少到15天
  - '--storage.tsdb.retention.size=50GB'  # 限制大小
```

#### 2. 优化查询性能

```yaml
# 使用 recording rules 预计算
groups:
  - name: payment_recording_rules
    interval: 30s
    rules:
      - record: payment:success_rate:5m
        expr: |
          (sum(rate(payment_success_total[5m])) by (payment_method)
           / sum(rate(payment_requests_total[5m])) by (payment_method)) * 100
```

#### 3. 调整抓取频率

```yaml
# 对于非关键指标，降低抓取频率
scrape_configs:
  - job_name: 'system-metrics'
    scrape_interval: 60s  # 从15s增加到60s
```

## 最佳实践

### 1. 告警配置

- ✅ 设置合理的阈值，避免误报
- ✅ 使用多级告警（warning → critical → emergency）
- ✅ 配置告警抑制规则，避免告警风暴
- ✅ 定期审查和调整告警规则
- ✅ 为每个告警提供 runbook 链接

### 2. 仪表板设计

- ✅ 按业务逻辑组织面板
- ✅ 使用颜色编码表示状态（绿色=正常，黄色=警告，红色=严重）
- ✅ 添加阈值线帮助识别问题
- ✅ 提供多个时间范围选项
- ✅ 使用变量实现动态过滤

### 3. 指标命名

- ✅ 使用统一的命名规范
- ✅ 包含业务含义的标签
- ✅ 避免高基数标签（如用户ID）
- ✅ 使用合适的指标类型（Counter/Gauge/Histogram）

### 4. 安全配置

- ✅ 修改默认密码
- ✅ 启用 HTTPS
- ✅ 配置访问控制
- ✅ 定期备份配置和数据
- ✅ 监控系统本身的健康状态

### 5. 运维建议

- ✅ 定期检查磁盘空间
- ✅ 监控 Prometheus 性能
- ✅ 定期更新组件版本
- ✅ 建立告警响应流程
- ✅ 进行定期演练

## 维护和升级

### 备份

```bash
# 备份 Prometheus 数据
docker-compose exec prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus
docker cp prometheus:/tmp/prometheus-backup.tar.gz ./backups/

# 备份 Grafana 数据
docker-compose exec grafana tar czf /tmp/grafana-backup.tar.gz /var/lib/grafana
docker cp grafana:/tmp/grafana-backup.tar.gz ./backups/

# 备份配置文件
tar czf monitoring-config-backup.tar.gz prometheus/ grafana/ alertmanager/
```

### 升级

```bash
# 1. 备份当前数据
./backup.sh

# 2. 拉取最新镜像
docker-compose pull

# 3. 停止服务
docker-compose down

# 4. 启动新版本
docker-compose up -d

# 5. 验证升级
docker-compose ps
docker-compose logs -f
```

### 清理

```bash
# 清理旧数据
docker-compose exec prometheus \
  promtool tsdb delete --start=0 --end=$(date -d '30 days ago' +%s)000

# 清理 Docker 资源
docker system prune -a --volumes
```

## 支持和反馈

### 文档

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [Alertmanager 官方文档](https://prometheus.io/docs/alerting/latest/alertmanager/)

### 问题反馈

如有问题或建议，请联系：
- Email: ops@example.com
- 内部工单系统: https://tickets.example.com

## 附录

### A. 指标完整列表

参见: [metrics-reference.md](./docs/metrics-reference.md)

### B. 告警规则完整列表

参见: [alerts-reference.md](./docs/alerts-reference.md)

### C. API 文档

参见: [api-reference.md](./docs/api-reference.md)

### D. 故障排查手册

参见: [troubleshooting-guide.md](./docs/troubleshooting-guide.md)

---

**版本**: 1.0
**最后更新**: 2026-01-23
**维护者**: 运维团队
