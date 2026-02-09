# Phase 3 智能运维系统 - 任务执行指南

## 概述

本指南为 Worker Agents 提供 Phase 3 任务的详细执行说明。

## 任务分配

- **Worker-1**: 故障检测、知识库、集成测试
- **Worker-2**: 自动修复、自动扩缩容
- **Worker-3**: 修复引擎、API、运维大盘

## 执行顺序

### Day 1-2: 基础设施
```
Worker-1: task-1 (故障检测脚本) → task-4 (知识库)
Worker-2: task-2 (自动修复脚本)
Worker-3: task-3 (修复引擎和 API - 可先实现框架)
```

### Day 3-4: 高级功能
```
Worker-2: task-5 (自动扩缩容引擎)
Worker-3: task-6 (运维大盘)
```

### Day 4-5: 集成测试
```
Worker-1: task-7 (集成测试和文档)
```

## Worker-1 任务详情

### Task-1: 实现故障检测脚本 (45min)

**目标**: 实现自动化故障诊断脚本

**步骤**:

1. **创建目录结构**
```bash
mkdir -p backend/monitoring/ops/scripts
cd backend/monitoring/ops/scripts
```

2. **实现服务不可用诊断脚本**
- 文件: `diagnose_service_down.py`
- 参考: `backend/docs/FAULT_DIAGNOSIS.md` 第 2.1.1 节
- 功能:
  - 检查容器状态 (docker inspect)
  - 检查进程状态 (docker exec ps)
  - 检查端口监听 (docker exec netstat)
  - 检查健康检查端点 (curl /health)
  - 检查网络连通性 (docker exec ping)
  - 输出 JSON 格式的诊断结果

3. **实现 CPU 过高诊断脚本**
- 文件: `diagnose_high_cpu.py`
- 参考: `backend/docs/FAULT_DIAGNOSIS.md` 第 2.2.1 节
- 功能:
  - 识别高 CPU 进程 (docker stats, top)
  - 检查是否有死循环/死锁
  - 检查请求量是否突增
  - 判断根因 (代码问题/流量洪峰/资源不足)

4. **实现内存过高诊断脚本**
- 文件: `diagnose_high_memory.py`
- 参考: `backend/docs/FAULT_DIAGNOSIS.md` 第 2.2.2 节
- 功能:
  - 检查内存使用情况
  - 分析内存泄漏
  - 检查缓存使用
  - 检查数据库连接池

5. **实现快速诊断脚本**
- 文件: `quick-diagnose.sh`
- 参考: `backend/docs/FAULT_DIAGNOSIS.md` 第 3.1 节
- 功能:
  - 一键收集所有诊断信息
  - 生成诊断报告
  - 打包为 tar.gz

**验收标准**:
- [ ] 所有脚本可执行且无语法错误
- [ ] 输出格式为 JSON (Python) 或结构化日志 (Bash)
- [ ] 包含根因分析和修复建议
- [ ] 执行时间 < 30 秒

### Task-4: 创建运维知识库 (45min)

**目标**: 创建运维知识库文档

**步骤**:

1. **创建目录结构**
```bash
mkdir -p backend/monitoring/ops-knowledge-base/{troubleshooting,runbooks,alerts}
```

2. **编写故障排查手册**
- 文件:
  - `troubleshooting/service-down.md`
  - `troubleshooting/high-cpu.md`
  - `troubleshooting/memory-leak.md`
  - `troubleshooting/database-slow.md`
- 内容:
  - 故障现象描述
  - 诊断步骤 (可执行命令)
  - 常见根因
  - 修复方案
  - 预防措施

3. **编写操作手册**
- 文件:
  - `runbooks/deployment.md`
  - `runbooks/backup-restore.md`
  - `runbooks/scaling.md`
- 内容:
  - 操作前准备
  - 详细操作步骤
  - 验证方法
  - 回滚方案

4. **编写告警处理指南**
- 文件:
  - `alerts/critical-alerts.md`
  - `alerts/warning-alerts.md`
- 内容:
  - 告警级别定义
  - 响应时间要求
  - 处理流程
  - 升级策略

5. **编写知识库 README**
- 文件: `README.md`
- 内容:
  - 知识库结构说明
  - 使用指南
  - 贡献指南

**验收标准**:
- [ ] 所有文档格式统一 (Markdown)
- [ ] 包含可执行的命令示例
- [ ] 内容与诊断脚本输出一致
- [ ] 结构清晰，易于查阅

### Task-7: 集成测试和文档完善 (60min)

**目标**: 验证端到端流程，完善文档

**步骤**:

1. **编写集成测试**
- 文件: `backend/tests/integration/test_ops_workflow.py`
- 测试场景:
  - 模拟容器崩溃，验证自动重启
  - 模拟 CPU 过高，验证自动扩容
  - 模拟磁盘不足，验证自动清理
  - 模拟数据库连接耗尽，验证连接池重置

2. **编写运维系统 README**
- 文件: `backend/monitoring/ops/README.md`
- 内容:
  - 系统架构概述
  - 快速开始
  - 脚本使用说明
  - 故障排查指南

3. **编写用户指南**
- 文件: `backend/docs/OPS_USER_GUIDE.md`
- 内容:
  - 如何查看运维大盘
  - 如何手动触发诊断
  - 如何手动触发修复
  - 如何查看修复历史
  - 常见问题

4. **编写完成报告**
- 文件: `backend/docs/PHASE3_COMPLETION_REPORT.md`
- 内容:
  - 实现功能清单
  - 测试结果
  - 性能指标
  - 已知问题
  - 后续计划

**验收标准**:
- [ ] 所有集成测试通过
- [ ] 用户指南清晰易懂
- [ ] 完成报告完整

## Worker-2 任务详情

### Task-2: 实现自动修复脚本 (60min)

**目标**: 实现自动修复脚本

**步骤**:

1. **创建目录结构**
```bash
mkdir -p backend/monitoring/ops/scripts/auto-heal
cd backend/monitoring/ops/scripts/auto-heal
```

2. **实现容器重启脚本**
- 文件: `restart-container.sh`
- 参考: `backend/docs/AUTO_HEALING.md` 第 3.1 节
- 功能:
  - 记录重启前状态
  - 执行容器重启
  - 健康检查验证
  - 记录修复事件

3. **实现资源清理脚本**
- 文件: `cleanup-resources.sh`
- 参考: `backend/docs/AUTO_HEALING.md` 第 3.2 节
- 功能:
  - 清理 Docker 资源
  - 清理应用日志
  - 清理系统日志
  - 清理缓存
  - 验证清理效果

4. **实现数据库连接池重置脚本**
- 文件: `reset_db_connections.py`
- 参考: `backend/docs/AUTO_HEALING.md` 第 3.3 节
- 功能:
  - 杀掉空闲连接
  - 杀掉长时间运行的查询
  - 重启应用连接池
  - 验证连接数

5. **实现 Redis 内存清理脚本**
- 文件: `cleanup_redis_memory.py`
- 参考: `backend/docs/AUTO_HEALING.md` 第 3.4 节
- 功能:
  - 删除过期键
  - 清理大 key
  - 执行 MEMORY PURGE
  - 验证内存释放

6. **实现水平扩容脚本**
- 文件: `scale-out.sh`
- 参考: `backend/docs/AUTO_HEALING.md` 第 3.5 节
- 功能:
  - 获取当前副本数
  - 执行扩容
  - 验证副本数
  - 记录扩容事件

**验收标准**:
- [ ] 所有脚本可执行且无语法错误
- [ ] 包含修复前后状态验证
- [ ] 记录修复事件到 API
- [ ] 执行时间符合要求

### Task-5: 实现自动扩缩容引擎 (60min)

**目标**: 实现自动扩缩容引擎

**步骤**:

1. **实现扩缩容引擎**
- 文件: `backend/app/ops/autoscaling.py`
- 参考: `backend/docs/OPS_ARCHITECTURE.md` 第 2.5 节
- 功能:
  - 检查监控指标
  - 计算目标副本数
  - 执行扩容/缩容
  - 检查冷却时间
  - 记录扩缩容事件

2. **创建扩缩容策略配置**
- 文件: `backend/monitoring/ops/config/scaling-policies.yml`
- 内容:
  - 最小/最大副本数
  - 目标 CPU/内存/QPS
  - 扩容/缩容触发条件
  - 冷却时间

3. **实现扩缩容检查脚本**
- 文件: `backend/monitoring/ops/scripts/check-scaling.py`
- 功能:
  - 查询 Prometheus 指标
  - 判断是否需要扩缩容
  - 调用扩缩容引擎

4. **编写单元测试**
- 文件: `backend/tests/test_autoscaling.py`
- 测试场景:
  - 测试目标副本数计算
  - 测试冷却时间检查
  - 测试扩容流程
  - 测试缩容流程

**验收标准**:
- [ ] 扩缩容引擎工作正常
- [ ] 支持多种指标
- [ ] 冷却时间生效
- [ ] 单元测试覆盖率 > 80%

## Worker-3 任务详情

### Task-3: 实现自动修复引擎和 API (90min)

**目标**: 实现自动修复引擎和相关 API

**步骤**:

1. **创建目录结构**
```bash
mkdir -p backend/app/ops
mkdir -p backend/app/api/v1/endpoints
mkdir -p backend/app/models
```

2. **实现自动修复引擎**
- 文件: `backend/app/ops/auto_healing.py`
- 参考: `backend/docs/AUTO_HEALING.md` 第 4.1 节
- 功能:
  - 告警处理逻辑
  - 修复策略映射
  - 修复动作执行
  - 修复效果验证
  - 记录修复事件

3. **实现诊断引擎**
- 文件: `backend/app/ops/diagnosis.py`
- 功能:
  - 调用诊断脚本
  - 解析诊断结果
  - 生成诊断报告

4. **实现 Webhook API**
- 文件: `backend/app/api/v1/endpoints/webhooks.py`
- 参考: `backend/docs/AUTO_HEALING.md` 第 4.2 节
- API:
  - `POST /api/v1/webhooks/alerts`
  - `POST /api/v1/webhooks/critical-alerts`
  - `POST /api/v1/webhooks/warning-alerts`

5. **实现运维 API**
- 文件: `backend/app/api/v1/endpoints/ops.py`
- API:
  - `GET /api/v1/ops/healing-events` - 查询修复事件
  - `POST /api/v1/ops/healing-events` - 记录修复事件
  - `POST /api/v1/ops/diagnose/{alert_name}` - 手动触发诊断
  - `POST /api/v1/ops/heal/{alert_name}` - 手动触发修复

6. **实现数据模型**
- 文件: `backend/app/models/ops.py`
- 模型:
  - `HealingEvent` - 修复事件记录
  - `DiagnosisResult` - 诊断结果记录

7. **编写单元测试**
- 文件: `backend/tests/test_auto_healing.py`
- 测试场景:
  - 测试告警处理流程
  - 测试修复策略选择
  - 测试修复动作执行
  - 测试 Webhook 接收

**验收标准**:
- [ ] 修复引擎工作正常
- [ ] Webhook 接收告警并触发修复
- [ ] 修复后验证效果
- [ ] API 返回正确数据
- [ ] 单元测试覆盖率 > 80%

### Task-6: 创建运维大盘 (45min)

**目标**: 创建 Grafana 运维大盘

**步骤**:

1. **创建大盘 JSON**
- 文件: `backend/monitoring/grafana/dashboards/ops-dashboard.json`
- 参考: `backend/monitoring/grafana/dashboards/ai-platform-overview.json`

2. **添加面板**
- Active Alerts (Table)
  - 数据源: Prometheus
  - 查询: `ALERTS{alertstate="firing"}`
  - 显示: 告警名称、级别、时间、实例

- Healing Events Timeline (Graph)
  - 数据源: Prometheus
  - 查询: `rate(healing_events_total[5m])`
  - 显示: 修复事件时间线

- Healing Success Rate (Gauge)
  - 数据源: Prometheus
  - 查询: `sum(rate(healing_events_total{status="success"}[5m])) / sum(rate(healing_events_total[5m]))`
  - 显示: 修复成功率

- Average Healing Time (Stat)
  - 数据源: Prometheus
  - 查询: `avg(healing_duration_seconds)`
  - 显示: 平均修复时间

- Scaling Events (Graph)
  - 数据源: Prometheus
  - 查询: `rate(scaling_events_total[5m])`
  - 显示: 扩缩容事件

- Service Replicas (Graph)
  - 数据源: Prometheus
  - 查询: `count(up{job="backend"})`
  - 显示: 服务副本数变化

3. **配置大盘**
- 设置刷新间隔: 30s
- 设置时间范围: Last 24 hours
- 添加变量: $service (服务名称)

**验收标准**:
- [ ] 大盘展示所有关键指标
- [ ] 数据可视化美观
- [ ] 面板布局清晰
- [ ] 支持时间范围选择

## 通用要求

### 代码规范
- Python: 遵循 PEP 8
- Bash: 遵循 Shell Script Best Practices
- 注释清晰，变量命名规范
- 错误处理完善

### 测试要求
- 单元测试覆盖率 > 80%
- 集成测试通过率 100%
- 测试用例覆盖正常和异常场景

### 文档要求
- 所有脚本包含使用说明
- API 包含 OpenAPI 文档
- 操作手册详细清晰

### 日志要求
- 所有操作记录日志
- 日志格式统一: `[时间] [级别] 消息`
- 包含执行时间、结果、错误信息

## 依赖关系

```
task-1 ──┐
         ├─→ task-3 ──┐
task-2 ──┘            ├─→ task-7
                      │
task-4 ───────────────┤
task-5 ───────────────┤
task-6 ───────────────┘
```

## 完成标准

### 功能完整性
- [ ] 所有定义的告警类型都有自动修复策略
- [ ] 修复成功率 > 95%
- [ ] 平均修复时间 < 2 分钟

### 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过率 100%
- [ ] 代码符合规范

### 文档完整性
- [ ] 运维知识库完整
- [ ] 用户指南清晰
- [ ] 完成报告详细

### 可观测性
- [ ] 运维大盘展示所有指标
- [ ] 告警和修复事件可追溯
- [ ] 扩缩容事件可视化

## 联系方式

如有问题，请联系架构师或查阅以下文档:
- `backend/docs/OPS_ARCHITECTURE.md`
- `backend/docs/FAULT_DIAGNOSIS.md`
- `backend/docs/AUTO_HEALING.md`
