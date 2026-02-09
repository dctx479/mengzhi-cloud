# 支付系统监控告警系统 - 交付总结

## 项目概述

为支付系统配置了完整的监控告警系统，包括 Prometheus 指标采集、Grafana 可视化仪表板、Alertmanager 告警管理，以及完整的 Docker 部署方案。

**交付日期**: 2026-01-23
**项目路径**: `E:\项目\数商\AI赋能云平台\monitoring`

---

## 交付清单

### 1. 后端代码集成

#### 1.1 指标定义 (`backend/app/core/metrics.py`)

**新增支付系统指标** (共 20+ 个指标):

- **支付请求指标**
  - `payment_requests_total`: 总支付请求数
  - `payment_success_total`: 成功支付数
  - `payment_failure_total`: 失败支付数

- **支付金额指标**
  - `payment_amount_total`: 总支付金额
  - `payment_amount_histogram`: 支付金额分布

- **支付响应时间**
  - `payment_duration_seconds`: 支付处理时间
  - `payment_callback_duration_seconds`: 回调处理时间

- **安全指标**
  - `payment_signature_verification_total`: 签名验证次数
  - `payment_signature_verification_failures`: 签名验证失败
  - `payment_amount_mismatch_total`: 金额不匹配次数

- **配额指标**
  - `quota_grant_total`: 配额发放次数
  - `quota_grant_duration_seconds`: 配额发放时间

- **状态指标**
  - `payment_pending_total`: 待支付订单数
  - `payment_processing_total`: 处理中支付数
  - `concurrent_payment_requests`: 并发支付请求数
  - `payment_success_rate`: 支付成功率

**辅助函数** (15个):
- `track_payment_request()`: 记录支付请求
- `track_payment_success()`: 记录支付成功
- `track_payment_failure()`: 记录支付失败
- `track_payment_duration()`: 记录支付处理时间
- `track_payment_callback()`: 记录支付回调
- `track_signature_verification()`: 记录签名验证
- `track_amount_verification()`: 记录金额验证
- `track_quota_grant()`: 记录配额发放
- 等等...

#### 1.2 支付服务集成 (`backend/app/services/payment_service.py`)

**集成点**:
- ✅ `create_payment()`: 支付创建时记录指标
- ✅ `handle_payment_callback()`: 回调处理时记录指标
- ✅ `_grant_quota()`: 配额发放时记录指标
- ✅ 并发支付计数
- ✅ 签名验证记录
- ✅ 金额验证记录

**关键改进**:
- 添加了 `time` 模块导入
- 在关键操作前后记录时间戳
- 使用 `increment_concurrent_payments()` 和 `decrement_concurrent_payments()` 跟踪并发
- 在所有支付状态变更时记录相应指标

#### 1.3 依赖更新 (`backend/requirements.txt`)

新增依赖:
```
prometheus-client==0.19.0        # Prometheus 指标采集
```

---

### 2. Prometheus 配置

#### 2.1 主配置文件 (`monitoring/prometheus/prometheus.yml`)

**配置要点**:
- 全局抓取间隔: 15秒
- 支付系统专用监控: 5秒高频抓取
- 集成 Alertmanager
- 配置多个 Exporter (MySQL, Redis, Node)

**监控目标**:
- `ai-platform-backend`: 应用程序指标
- `payment-system`: 支付系统专用指标
- `mysql`: 数据库指标
- `redis`: 缓存指标
- `node`: 系统资源指标

#### 2.2 告警规则 (`monitoring/prometheus/alerts/payment-alerts.yml`)

**告警分组**:

1. **支付告警** (payment_alerts)
   - HighPaymentFailureRate: 失败率 > 5%
   - CriticalPaymentFailureRate: 失败率 > 10%
   - HighSignatureVerificationFailures: 签名验证失败 > 10次/分钟
   - PaymentAmountMismatch: 金额不匹配
   - SlowPaymentProcessing: P95响应时间 > 5秒
   - PaymentCallbackFailures: 回调处理失败
   - QuotaGrantFailures: 配额发放失败
   - HighConcurrentPayments: 并发请求 > 100
   - PendingPaymentsBacklog: 待支付订单 > 1000
   - NoPaymentActivity: 30分钟无支付活动

2. **系统告警** (system_alerts)
   - HighCPUUsage: CPU > 80%
   - HighMemoryUsage: 内存 > 85%
   - HighDiskUsage: 磁盘 > 90%

3. **数据库告警** (database_alerts)
   - SlowDatabaseQueries: P95查询时间 > 1秒
   - HighDatabaseConnections: 连接数 > 80

**告警级别**:
- `emergency`: 紧急 (立即响应)
- `critical`: 严重 (5分钟内响应)
- `warning`: 警告 (30分钟内响应)
- `info`: 信息 (无需响应)

---

### 3. Grafana 配置

#### 3.1 数据源配置 (`monitoring/grafana/datasources/prometheus.yml`)

- 数据源: Prometheus
- URL: http://prometheus:9090
- 默认数据源: 是
- 查询超时: 60秒

#### 3.2 仪表板配置 (`monitoring/grafana/dashboards/payment-dashboard.json`)

**18个预配置面板**:

| 面板ID | 面板名称 | 类型 | 说明 |
|--------|---------|------|------|
| 1 | 支付成功率 | Graph | 按支付方式显示成功率 |
| 2 | 支付请求量 (QPS) | Graph | 实时请求量 |
| 3 | 支付失败率 | Graph | 按支付方式显示失败率 |
| 4 | 支付失败原因分布 | Pie Chart | 失败原因占比 |
| 5 | 支付响应时间 (P95) | Graph | P95/P99响应时间 |
| 6 | 支付金额分布 | Heatmap | 金额分布热力图 |
| 7 | 签名验证失败次数 | Graph | 实时失败次数 |
| 8 | 金额验证失败次数 | Stat | 1小时内失败总数 |
| 9 | 并发支付请求数 | Gauge | 当前并发数 |
| 10 | 待支付订单数 | Stat | 当前待支付数 |
| 11 | 处理中支付数 | Stat | 当前处理中数 |
| 12 | 配额发放成功率 | Graph | 按配额类型显示 |
| 13 | 配额发放响应时间 | Graph | P95响应时间 |
| 14 | 支付回调成功率 | Graph | 按支付方式显示 |
| 15 | 支付回调响应时间 | Graph | P95响应时间 |
| 16 | 总支付金额 (小时) | Stat | 1小时总金额 |
| 17 | 成功支付数 (小时) | Stat | 1小时成功数 |
| 18 | 失败支付数 (小时) | Stat | 1小时失败数 |

**仪表板特性**:
- 自动刷新: 30秒
- 时间范围: 默认1小时
- 告警阈值线: 自动显示
- 颜色编码: 绿色(正常)、黄色(警告)、红色(严重)

---

### 4. Alertmanager 配置

#### 4.1 主配置文件 (`monitoring/alertmanager/alertmanager.yml`)

**告警路由**:
- 默认接收器: default
- 分组依据: alertname, component, severity
- 分组等待: 30秒
- 分组间隔: 5分钟
- 重复间隔: 4小时

**子路由**:
- emergency: 10秒等待，30分钟重复
- critical: 30秒等待，1小时重复
- payment: 专门的支付团队路由
- security: 安全团队路由
- database: 数据库团队路由
- system: 运维团队路由
- warning: 降低通知频率

**告警接收器**:
- default: Webhook
- emergency-team: Email + Webhook
- critical-team: Email + Webhook
- payment-team: Email + Webhook (支持企业微信)
- security-team: Email + Webhook
- database-team: Email + Webhook
- ops-team: Email + Webhook
- warning-team: Email + Webhook

**抑制规则**:
- emergency 抑制 critical
- critical 抑制 warning
- CriticalPaymentFailureRate 抑制 HighPaymentFailureRate
- 系统资源严重不足时抑制性能告警

---

### 5. Docker 部署配置

#### 5.1 Docker Compose (`monitoring/docker-compose.yml`)

**服务列表**:

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| prometheus | prom/prometheus:v2.45.0 | 9090 | 指标采集和存储 |
| grafana | grafana/grafana:10.0.0 | 3000 | 可视化仪表板 |
| alertmanager | prom/alertmanager:v0.26.0 | 9093 | 告警管理 |
| node-exporter | prom/node-exporter:v1.6.0 | 9100 | 系统指标 |
| mysql-exporter | prom/mysqld-exporter:v0.15.0 | 9104 | MySQL指标 |
| redis-exporter | oliver006/redis_exporter:v1.52.0 | 9121 | Redis指标 |
| mysql | mysql:8.0 | 3306 | 数据库 (测试) |
| redis | redis:7-alpine | 6379 | 缓存 (测试) |
| backend | 自定义 | 8000 | 应用后端 |

**数据卷**:
- prometheus-data: Prometheus 数据持久化
- grafana-data: Grafana 数据持久化
- alertmanager-data: Alertmanager 数据持久化
- mysql-data: MySQL 数据持久化
- redis-data: Redis 数据持久化

**网络配置**:
- 网络名称: monitoring
- 子网: 172.20.0.0/16

#### 5.2 快速启动脚本

**Windows** (`monitoring/start.bat`):
- 检查 Docker 环境
- 创建数据目录
- 启动所有服务
- 显示访问地址

**Linux/Mac** (`monitoring/start.sh`):
- 检查 Docker 环境
- 创建数据目录并设置权限
- 启动所有服务
- 显示访问地址

---

### 6. 文档

#### 6.1 完整文档 (`monitoring/README.md`)

**章节**:
1. 系统架构
2. 功能特性
3. 快速开始
4. 配置说明
5. 监控指标
6. 告警规则
7. 仪表板
8. 故障排查
9. 最佳实践
10. 维护和升级

**内容亮点**:
- 详细的安装步骤
- 完整的指标列表和说明
- 告警规则详解和处理建议
- 常见问题排查指南
- 性能优化建议
- 最佳实践总结

---

## 文件清单

```
monitoring/
├── README.md                                    # 完整文档
├── docker-compose.yml                           # Docker Compose 配置
├── start.bat                                    # Windows 启动脚本
├── start.sh                                     # Linux/Mac 启动脚本
├── prometheus/
│   ├── prometheus.yml                          # Prometheus 主配置
│   └── alerts/
│       └── payment-alerts.yml                  # 告警规则
├── grafana/
│   ├── datasources/
│   │   └── prometheus.yml                      # 数据源配置
│   └── dashboards/
│       ├── dashboard-provider.yml              # 仪表板提供者
│       └── payment-dashboard.json              # 支付系统仪表板
└── alertmanager/
    └── alertmanager.yml                        # Alertmanager 配置

backend/
├── app/
│   ├── core/
│   │   └── metrics.py                          # 指标定义 (已更新)
│   └── services/
│       └── payment_service.py                  # 支付服务 (已集成指标)
└── requirements.txt                             # 依赖 (已添加 prometheus-client)
```

---

## 使用指南

### 快速启动

#### Windows:
```bash
cd E:\项目\数商\AI赋能云平台\monitoring
start.bat
```

#### Linux/Mac:
```bash
cd /path/to/monitoring
chmod +x start.sh
./start.sh
```

### 访问地址

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

### 验证安装

1. **检查 Prometheus 目标**
   - 访问 http://localhost:9090/targets
   - 确保所有目标状态为 `UP`

2. **查看 Grafana 仪表板**
   - 登录 Grafana
   - 进入 Dashboards → Browse
   - 打开 "支付系统监控仪表板"

3. **测试告警**
   ```bash
   curl -X POST http://localhost:9093/api/v1/alerts \
     -H 'Content-Type: application/json' \
     -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"测试告警"}}]'
   ```

---

## 关键指标说明

### 支付成功率

```promql
(sum(rate(payment_success_total[5m])) by (payment_method)
 / sum(rate(payment_requests_total[5m])) by (payment_method)) * 100
```

**正常范围**: > 95%
**告警阈值**: < 95% (warning), < 90% (critical)

### 支付响应时间 (P95)

```promql
histogram_quantile(0.95,
  sum(rate(payment_duration_seconds_bucket{operation="create_payment"}[5m]))
  by (payment_method, le)
)
```

**正常范围**: < 2秒
**告警阈值**: > 5秒 (warning), > 10秒 (critical)

### 签名验证失败率

```promql
sum(rate(payment_signature_verification_failures[1m])) by (payment_method)
```

**正常范围**: 0次/分钟
**告警阈值**: > 10次/分钟 (critical)

---

## 告警处理流程

### 1. 支付失败率过高

**告警**: HighPaymentFailureRate

**处理步骤**:
1. 查看 Grafana 仪表板确认失败率
2. 检查失败原因分布
3. 查看后端日志: `docker-compose logs backend | grep payment`
4. 验证第三方支付接口状态
5. 检查数据库和网络连接
6. 如需要，切换到备用支付方式

### 2. 签名验证失败

**告警**: HighSignatureVerificationFailures

**处理步骤**:
1. 立即检查是否存在安全攻击
2. 验证签名密钥配置
3. 检查回调数据格式
4. 查看 Alertmanager 日志
5. 联系安全团队

### 3. 金额不匹配

**告警**: PaymentAmountMismatch

**处理步骤**:
1. **立即暂停相关支付方式**
2. 检查订单和支付记录
3. 验证金额计算逻辑
4. 联系安全团队调查
5. 生成事故报告

---

## 性能优化建议

### 1. Prometheus 存储优化

```yaml
# 减少数据保留时间
--storage.tsdb.retention.time=15d

# 限制存储大小
--storage.tsdb.retention.size=50GB
```

### 2. 使用 Recording Rules

```yaml
# 预计算常用查询
groups:
  - name: payment_recording_rules
    interval: 30s
    rules:
      - record: payment:success_rate:5m
        expr: |
          (sum(rate(payment_success_total[5m])) by (payment_method)
           / sum(rate(payment_requests_total[5m])) by (payment_method)) * 100
```

### 3. 调整抓取频率

```yaml
# 对非关键指标降低频率
scrape_configs:
  - job_name: 'system-metrics'
    scrape_interval: 60s  # 从15s增加到60s
```

---

## 安全配置

### 1. 修改默认密码

```yaml
# Grafana
GF_SECURITY_ADMIN_PASSWORD: your_secure_password

# MySQL
MYSQL_ROOT_PASSWORD: your_secure_password

# Redis
REDIS_PASSWORD: your_secure_password
```

### 2. 配置邮件通知

```yaml
# alertmanager.yml
global:
  smtp_from: 'your-email@example.com'
  smtp_smarthost: 'smtp.example.com:587'
  smtp_auth_username: 'your-email@example.com'
  smtp_auth_password: 'your-password'
```

### 3. 启用 HTTPS

生产环境建议配置 HTTPS 和访问控制。

---

## 维护计划

### 日常维护

- ✅ 每日检查告警状态
- ✅ 每周审查仪表板数据
- ✅ 每月检查磁盘空间
- ✅ 每季度更新组件版本

### 备份策略

```bash
# 备份 Prometheus 数据
docker-compose exec prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus

# 备份 Grafana 数据
docker-compose exec grafana tar czf /tmp/grafana-backup.tar.gz /var/lib/grafana

# 备份配置文件
tar czf monitoring-config-backup.tar.gz prometheus/ grafana/ alertmanager/
```

---

## 技术栈

- **Prometheus**: v2.45.0 - 指标采集和存储
- **Grafana**: v10.0.0 - 可视化仪表板
- **Alertmanager**: v0.26.0 - 告警管理
- **Node Exporter**: v1.6.0 - 系统指标
- **MySQL Exporter**: v0.15.0 - MySQL指标
- **Redis Exporter**: v1.52.0 - Redis指标
- **prometheus-client**: v0.19.0 - Python客户端

---

## 下一步建议

### 短期 (1-2周)

1. ✅ 部署到测试环境
2. ✅ 验证所有告警规则
3. ✅ 调整告警阈值
4. ✅ 配置邮件通知
5. ✅ 培训运维团队

### 中期 (1个月)

1. ⏳ 添加更多业务指标
2. ⏳ 优化仪表板布局
3. ⏳ 集成企业微信/钉钉通知
4. ⏳ 建立告警响应流程
5. ⏳ 编写运维手册

### 长期 (3个月)

1. ⏳ 实现自动化告警处理
2. ⏳ 集成日志分析系统
3. ⏳ 建立性能基线
4. ⏳ 实现预测性告警
5. ⏳ 优化成本和性能

---

## 联系方式

如有问题或建议，请联系：
- **技术支持**: ops@example.com
- **紧急联系**: emergency@example.com
- **文档反馈**: docs@example.com

---

**交付状态**: ✅ 完成
**交付日期**: 2026-01-23
**版本**: 1.0
**维护者**: 运维团队
