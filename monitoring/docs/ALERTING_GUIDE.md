# 告警系统配置和测试指南

## 版本信息
- **版本**: v1.0
- **创建日期**: 2026-01-24
- **状态**: Phase 2 完成

## 一、告警系统概述

### 1.1 系统架构

```
Prometheus (监控指标采集)
    ↓
Alert Rules (告警规则评估)
    ↓
Alertmanager (告警聚合和路由)
    ↓
Receivers (通知接收器)
    ├─ Webhook → Backend API
    ├─ Email → 运维团队
    └─ 企业微信/钉钉 → 移动端
```

### 1.2 告警规则统计

当前系统共配置 **45+ 条告警规则**，覆盖以下领域：

| 类别 | 规则数 | 示例 |
|------|--------|------|
| **支付系统** | 15 | 支付失败率、签名验证、金额验证 |
| **系统资源** | 3 | CPU、内存、磁盘使用率 |
| **数据库** | 5 | 慢查询、连接池、数据库宕机 |
| **Redis** | 6 | 内存使用、连接数、键驱逐率 |
| **容器** | 4 | 容器重启、CPU/内存/健康检查 |
| **API** | 3 | 响应时间、错误率、服务可用性 |
| **磁盘** | 3 | 磁盘使用率、磁盘IO |

### 1.3 告警分级

```yaml
P0 (Emergency):
  - 影响: 全部用户，服务完全不可用
  - 响应: 立即 (0-5分钟)
  - 通知: 电话 + 短信 + 邮件 + Webhook
  - 示例: 数据库宕机、支付系统崩溃

P1 (Critical):
  - 影响: 部分用户，核心功能受损
  - 响应: 15分钟内
  - 通知: 邮件 + Webhook + 值班寻呼
  - 示例: 支付失败率 >10%、容器频繁重启

P2 (Warning):
  - 影响: 性能下降，可能影响用户体验
  - 响应: 1小时内
  - 通知: 邮件 + Webhook
  - 示例: CPU使用率 >80%、慢查询

P3 (Info):
  - 影响: 潜在风险，无直接影响
  - 响应: 下一个工作日
  - 通知: Webhook（记录日志）
  - 示例: 配置变更、异常大额支付
```

## 二、告警配置详解

### 2.1 Alertmanager 配置

**文件位置**: `monitoring/alertmanager/alertmanager.yml`

#### 2.1.1 告警路由 (Route)

```yaml
route:
  group_by: ['alertname', 'component', 'severity']
  group_wait: 30s       # 首次告警等待30秒，收集同组告警
  group_interval: 5m    # 同组新告警间隔5分钟才发送
  repeat_interval: 4h   # 未解决的告警每4小时重复提醒

  routes:
    # Emergency 告警: 立即通知
    - match:
        severity: emergency
      receiver: 'emergency-team'
      group_wait: 10s
      repeat_interval: 30m
      continue: true

    # Critical 告警: 快速通知 + 值班寻呼
    - match:
        severity: critical
      receiver: 'oncall-pager'
      group_wait: 10s
      repeat_interval: 30m
      continue: true

    # 支付系统告警: 专门团队
    - match:
        component: payment
      receiver: 'payment-team'
      group_wait: 30s
      repeat_interval: 2h
```

**关键配置说明**:

- **group_by**: 告警分组依据，相同 `alertname + component + severity` 的告警会聚合
- **group_wait**: 首次告警等待时间，避免告警风暴
- **group_interval**: 同组新告警的发送间隔，避免频繁通知
- **repeat_interval**: 重复告警间隔，持续提醒未解决的问题
- **continue: true**: 继续匹配后续路由，实现多接收器通知

#### 2.1.2 告警抑制 (Inhibit Rules)

**核心理念**: 避免告警风暴，抑制冗余告警

```yaml
inhibit_rules:
  # 规则1: 严重告警抑制同类低级别告警
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'component']

  # 规则2: 上游服务故障抑制下游告警
  - source_match:
      alertname: 'DatabaseDown'
    target_match_re:
      alertname: '(SlowDatabaseQueries|HighDatabaseConnections)'
    equal: ['instance']

  # 规则3: 资源告警抑制应用告警
  - source_match:
      alertname: 'HighCPUUsage'
      severity: 'critical'
    target_match:
      alertname: 'SlowPaymentProcessing'
    equal: ['instance']

  # 规则4: 容器告警抑制容器资源告警
  - source_match:
      alertname: 'ContainerRestarting'
    target_match_re:
      alertname: '(ContainerHighCPU|ContainerHighMemory)'
    equal: ['container_name']
```

**抑制规则逻辑**:

1. **同类抑制**: Critical 抑制 Warning（同告警名称和组件）
2. **上下游抑制**: 数据库宕机 → 抑制慢查询和连接数告警
3. **根因抑制**: CPU过高 → 抑制API响应慢告警（因为根因是CPU）
4. **级联抑制**: 容器重启 → 抑制容器资源告警（重启期间的资源波动）

#### 2.1.3 告警接收器 (Receivers)

```yaml
receivers:
  # 默认接收器 - Webhook
  - name: 'default'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
        send_resolved: true

  # 值班团队 - 寻呼机/短信
  - name: 'oncall-pager'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
    # 可以配置短信网关
    # webhook_configs:
    #   - url: 'https://sms-gateway.example.com/send'

  # 紧急团队 - 多渠道
  - name: 'emergency-team'
    email_configs:
      - to: 'emergency@example.com'
        subject: '🚨 [紧急] {{ .GroupLabels.alertname }}'
    webhook_configs:
      - url: 'http://backend:8000/api/v1/alerts/webhook'
```

### 2.2 告警规则配置

**文件位置**: `monitoring/prometheus/alerts/payment-alerts.yml`

#### 2.2.1 规则结构

```yaml
groups:
  - name: payment_alerts
    interval: 30s  # 评估间隔
    rules:
      - alert: HighPaymentFailureRate
        expr: |
          (
            sum(rate(payment_failure_total[5m])) by (payment_method)
            /
            sum(rate(payment_requests_total[5m])) by (payment_method)
          ) * 100 > 5
        for: 2m  # 持续2分钟才触发
        labels:
          severity: critical
          component: payment
        annotations:
          summary: "支付失败率过高 ({{ $labels.payment_method }})"
          description: "{{ $labels.payment_method }} 支付失败率为 {{ $value | humanize }}%，超过5%阈值。"
          runbook_url: "https://docs.example.com/runbooks/payment-failure-rate"
```

**关键字段**:

- **expr**: PromQL 查询表达式
- **for**: 持续时间阈值，避免短暂波动触发告警
- **labels**: 告警标签，用于路由和抑制
- **annotations**: 告警描述信息

#### 2.2.2 核心告警规则

**1. 数据库连接池告警**

```yaml
- alert: DatabaseConnectionPoolExhausted
  expr: |
    (db_active_connections / db_max_connections) * 100 > 90
  for: 2m
  labels:
    severity: critical
    component: database
  annotations:
    summary: "数据库连接池即将耗尽"
    description: "连接池使用率为 {{ $value | humanize }}%，超过90%阈值。"
```

**修复策略**:
- 自动: 重启应用，释放空闲连接
- 手动: 增加连接池大小，优化慢查询

**2. Redis 内存告警**

```yaml
- alert: RedisMemoryHigh
  expr: |
    (redis_memory_used_bytes / redis_memory_max_bytes) * 100 > 90
  for: 5m
  labels:
    severity: warning
    component: redis
  annotations:
    summary: "Redis内存使用率过高"
    description: "Redis内存使用率为 {{ $value | humanize }}%。"
```

**修复策略**:
- 自动: 清理过期键，设置 TTL
- 手动: 扩容 Redis，优化缓存策略

**3. 容器重启告警**

```yaml
- alert: ContainerRestarting
  expr: |
    rate(container_restarts_total[15m]) > 3
  for: 5m
  labels:
    severity: critical
    component: container
  annotations:
    summary: "容器频繁重启 ({{ $labels.container_name }})"
    description: "容器在过去15分钟内重启超过3次。"
```

**修复策略**:
- 自动: 回滚到上一稳定版本
- 手动: 分析容器日志，修复代码问题

**4. API 响应时间告警**

```yaml
- alert: HighResponseTime
  expr: |
    histogram_quantile(0.95,
      sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
    ) > 3
  for: 5m
  labels:
    severity: warning
    component: api
  annotations:
    summary: "API响应时间过长 ({{ $labels.endpoint }})"
    description: "P95响应时间为 {{ $value | humanize }}秒，超过3秒。"
```

**修复策略**:
- 自动: 水平扩容
- 手动: 优化慢接口，添加缓存

**5. 磁盘使用率告警**

```yaml
- alert: HighDiskUsage
  expr: |
    (node_filesystem_size_bytes - node_filesystem_free_bytes)
    / node_filesystem_size_bytes * 100 > 85
  for: 5m
  labels:
    severity: warning
    component: system
  annotations:
    summary: "磁盘使用率过高 ({{ $labels.mountpoint }})"
    description: "磁盘使用率为 {{ $value | humanize }}%。"
```

**修复策略**:
- 自动: 清理日志文件、Docker镜像
- 手动: 扩容磁盘，清理无用数据

## 三、测试工具使用

### 3.1 测试告警脚本

**文件位置**: `monitoring/scripts/test-alerts.sh`

#### 3.1.1 快速测试

```bash
# 检查服务状态
./test-alerts.sh

# 测试特定告警
./test-alerts.sh cpu        # CPU 告警
./test-alerts.sh memory     # 内存告警
./test-alerts.sh db         # 数据库告警
./test-alerts.sh payment    # 支付告警

# 运行所有测试
./test-alerts.sh all

# 测试告警抑制
./test-alerts.sh inhibit
```

#### 3.1.2 交互式菜单

```bash
# 启动交互式菜单
./test-alerts.sh

# 选择测试项目
1) 测试 HighCPUUsage 告警
2) 测试 HighMemoryUsage 告警
3) 测试 HighDiskUsage 告警
...
10) 查看当前活跃告警
11) 运行所有测试
```

#### 3.1.3 自定义测试

编辑脚本添加自定义测试:

```bash
test_custom_alert() {
    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[{
            "labels": {
                "alertname": "CustomAlert",
                "severity": "warning"
            },
            "annotations": {
                "summary": "自定义测试告警"
            }
        }]'
}
```

### 3.2 告警统计脚本

**文件位置**: `monitoring/scripts/alert-stats.sh`

#### 3.2.1 快速查询

```bash
# 查看当前活跃告警
./alert-stats.sh 24h active

# 告警频率统计
./alert-stats.sh 24h frequency

# 告警趋势分析
./alert-stats.sh 24h trends

# 系统健康评分
./alert-stats.sh 24h health

# 完整分析
./alert-stats.sh 24h full
```

#### 3.2.2 生成报告

```bash
# 生成告警报告
./alert-stats.sh 24h report

# 输出示例: alert-report-20260124-143052.txt
```

#### 3.2.3 健康评分算法

```
健康评分 (100分制):
- 基准分: 100
- Critical 告警: 每个 -20 分
- Warning 告警: 每个 -5 分
- 最低分: 0 分

评级:
- 90-100: 优秀 (Excellent)
- 70-89:  良好 (Good)
- 50-69:  一般 (Fair)
- 0-49:   差 (Poor)
```

## 四、告警处理流程

### 4.1 告警响应流程

```
收到告警通知
    ↓
确认告警信息 (Alertmanager UI)
    ↓
查看告警详情 (Prometheus)
    ↓
根据 Runbook 排查
    ↓
执行修复操作
    ↓
验证告警解除
    ↓
记录事后总结
```

### 4.2 告警处理 SLA

| 告警级别 | 响应时间 | 解决时间 | 升级条件 |
|----------|----------|----------|----------|
| Emergency | 5 分钟 | 30 分钟 | 15分钟未响应 |
| Critical | 15 分钟 | 2 小时 | 30分钟未响应 |
| Warning | 1 小时 | 4 小时 | 2小时未响应 |
| Info | 1 工作日 | 3 工作日 | 无 |

### 4.3 常见告警处理手册

#### HighCPUUsage

**排查步骤**:
1. 查看容器 CPU 使用: `docker stats`
2. 分析进程 CPU: `docker exec <container> top -bn1`
3. 检查请求量: Grafana QPS 图表
4. 分析慢接口: Prometheus API metrics

**修复方案**:
- 短期: 重启容器释放资源
- 中期: 水平扩容增加实例
- 长期: 优化代码，添加缓存

#### DatabaseConnectionPoolExhausted

**排查步骤**:
1. 查看当前连接数: `SELECT count(*) FROM pg_stat_activity`
2. 分析空闲连接: `SELECT * FROM pg_stat_activity WHERE state = 'idle'`
3. 检查慢查询: `SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes'`

**修复方案**:
- 立即: 杀掉空闲连接
- 短期: 重启应用释放连接
- 长期: 增加连接池大小，优化查询

#### ContainerRestarting

**排查步骤**:
1. 查看容器日志: `docker logs <container> --tail 100`
2. 检查容器状态: `docker inspect <container>`
3. 查看重启历史: `docker ps -a | grep <container>`

**修复方案**:
- 立即: 回滚到上一稳定版本
- 短期: 修复代码问题，重新部署
- 长期: 增加健康检查，优化容器配置

## 五、最佳实践

### 5.1 告警规则设计

✅ **推荐**:
- 告警阈值基于历史数据和容量规划
- 使用 `for` 参数避免短暂波动
- 添加清晰的 `summary` 和 `description`
- 提供 `runbook_url` 指向处理手册
- 合理设置告警级别

❌ **避免**:
- 告警阈值过于敏感，导致频繁误报
- 告警描述不清晰，无法快速定位问题
- 缺少修复指导，增加响应时间
- 告警级别设置不合理

### 5.2 告警抑制设计

✅ **推荐**:
- 上游服务故障抑制下游告警
- 资源告警抑制应用性能告警
- 严重告警抑制同类低级别告警
- 容器告警抑制容器资源告警

❌ **避免**:
- 过度抑制，导致重要告警被忽略
- 抑制规则过于复杂，难以维护

### 5.3 告警通知策略

✅ **推荐**:
- Emergency: 多渠道通知（电话+短信+邮件）
- Critical: 值班寻呼 + Webhook
- Warning: 邮件 + Webhook
- Info: Webhook 记录日志

❌ **避免**:
- 所有告警都发送邮件，导致邮件过载
- 通知渠道单一，响应不及时

### 5.4 告警测试

✅ **推荐**:
- 定期执行告警测试（每月一次）
- 验证告警路由和抑制规则
- 测试通知渠道可用性
- 模拟故障场景

❌ **避免**:
- 从不测试告警配置
- 生产环境才发现告警失效

## 六、故障排查

### 6.1 告警未触发

**可能原因**:
1. Prometheus 未采集到指标
2. 告警规则表达式错误
3. 告警阈值设置过高

**排查步骤**:
```bash
# 1. 检查 Prometheus 指标
curl http://localhost:9090/api/v1/query?query=<metric_name>

# 2. 检查告警规则
curl http://localhost:9090/api/v1/rules

# 3. 检查告警状态
curl http://localhost:9090/api/v1/alerts
```

### 6.2 告警未通知

**可能原因**:
1. Alertmanager 未收到告警
2. 告警被抑制
3. 接收器配置错误

**排查步骤**:
```bash
# 1. 检查 Alertmanager 告警
curl http://localhost:9093/api/v1/alerts

# 2. 检查抑制状态
curl http://localhost:9093/api/v1/silences

# 3. 检查接收器日志
docker logs alertmanager
```

### 6.3 告警风暴

**可能原因**:
1. 告警抑制规则不生效
2. 大量服务同时故障
3. 告警规则过于敏感

**解决方案**:
```bash
# 1. 批量 Silence 告警
./silence-alerts.sh <alertname>

# 2. 优化告警规则
# 增加 for 参数，提高阈值

# 3. 优化抑制规则
# 添加更多抑制规则
```

## 七、配置验证

### 7.1 YAML 语法检查

```bash
# 检查 Alertmanager 配置
amtool check-config monitoring/alertmanager/alertmanager.yml

# 检查 Prometheus 告警规则
promtool check rules monitoring/prometheus/alerts/payment-alerts.yml
```

### 7.2 配置重载

```bash
# 重载 Alertmanager 配置
curl -X POST http://localhost:9093/-/reload

# 重载 Prometheus 配置
curl -X POST http://localhost:9090/-/reload
```

### 7.3 端到端测试

```bash
# 1. 触发测试告警
./test-alerts.sh all

# 2. 检查告警是否触发
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname == "HighCPUUsage")'

# 3. 检查告警是否到达 Alertmanager
curl http://localhost:9093/api/v1/alerts | jq '.data[] | select(.labels.alertname == "HighCPUUsage")'

# 4. 检查 Webhook 是否收到
curl http://localhost:8000/api/v1/alerts/history
```

## 八、运维工具

### 8.1 Alertmanager UI

- **访问地址**: http://localhost:9093
- **功能**: 查看活跃告警、配置 Silence、管理接收器

### 8.2 Prometheus UI

- **访问地址**: http://localhost:9090
- **功能**: 查看告警规则、测试 PromQL、查看指标

### 8.3 Grafana 大盘

- **访问地址**: http://localhost:3000
- **功能**: 可视化监控指标、告警历史、趋势分析

## 九、相关文档

- [监控和日志指南](./MONITORING_AND_LOGGING_GUIDE.md)
- [运维架构设计](./OPS_ARCHITECTURE.md)
- [故障诊断流程](./FAULT_DIAGNOSIS.md)
- [自动修复策略](./AUTO_HEALING.md)

## 十、附录

### A. 告警规则清单

详见: `monitoring/prometheus/alerts/payment-alerts.yml`

### B. PromQL 示例

```promql
# CPU 使用率
system_cpu_usage_percent > 80

# 内存使用率
(system_memory_used_bytes / system_memory_total_bytes) * 100 > 85

# API P95 响应时间
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
) > 3

# 5xx 错误率
(
  sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
  sum(rate(http_requests_total[5m]))
) * 100 > 5
```

### C. 联系方式

- **运维团队**: ops@example.com
- **紧急联系**: emergency@example.com
- **值班电话**: +86-xxx-xxxx-xxxx

---

**最后更新**: 2026-01-24
