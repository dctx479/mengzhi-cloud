# Phase 3 快速参考卡片

## 🎯 核心目标

构建智能运维系统，实现故障自动检测、诊断、修复和预防。

## 📁 项目结构

```
backend/
├── monitoring/
│   ├── ops/
│   │   ├── scripts/                    # 运维脚本
│   │   │   ├── diagnose_*.py          # 诊断脚本
│   │   │   ├── quick-diagnose.sh      # 快速诊断
│   │   │   └── auto-heal/             # 自动修复脚本
│   │   │       ├── restart-container.sh
│   │   │       ├── cleanup-resources.sh
│   │   │       ├── reset_db_connections.py
│   │   │       ├── cleanup_redis_memory.py
│   │   │       └── scale-out.sh
│   │   ├── config/
│   │   │   └── scaling-policies.yml   # 扩缩容策略
│   │   ├── task-assignments.json      # 任务分配清单
│   │   ├── EXECUTION_GUIDE.md         # 执行指南
│   │   └── README.md
│   │
│   └── ops-knowledge-base/            # 运维知识库
│       ├── troubleshooting/           # 故障排查手册
│       ├── runbooks/                  # 操作手册
│       ├── alerts/                    # 告警处理指南
│       └── README.md
│
├── app/
│   ├── ops/                           # 运维模块
│   │   ├── __init__.py
│   │   ├── auto_healing.py           # 自动修复引擎
│   │   ├── diagnosis.py              # 诊断引擎
│   │   └── autoscaling.py            # 自动扩缩容引擎
│   │
│   ├── api/v1/endpoints/
│   │   ├── webhooks.py               # Alertmanager Webhook
│   │   └── ops.py                    # 运维 API
│   │
│   └── models/
│       └── ops.py                    # 运维数据模型
│
├── tests/
│   ├── test_auto_healing.py          # 修复引擎测试
│   ├── test_autoscaling.py           # 扩缩容测试
│   └── integration/
│       └── test_ops_workflow.py      # 集成测试
│
└── docs/
    ├── OPS_ARCHITECTURE.md            # 系统架构
    ├── FAULT_DIAGNOSIS.md             # 故障诊断流程
    ├── AUTO_HEALING.md                # 自动修复策略
    ├── OPS_USER_GUIDE.md              # 用户指南
    └── PHASE3_COMPLETION_REPORT.md    # 完成报告
```

## 🔧 核心脚本

### 诊断脚本 (Worker-1)

| 脚本 | 功能 | 输出 |
|-----|------|-----|
| `diagnose_service_down.py` | 诊断服务不可用 | JSON |
| `diagnose_high_cpu.py` | 诊断 CPU 过高 | JSON |
| `diagnose_high_memory.py` | 诊断内存过高 | JSON |
| `quick-diagnose.sh` | 一键收集诊断信息 | tar.gz |

### 修复脚本 (Worker-2)

| 脚本 | 功能 | 执行时间 |
|-----|------|---------|
| `restart-container.sh` | 重启容器 | ~30s |
| `cleanup-resources.sh` | 清理资源 | ~2min |
| `reset_db_connections.py` | 重置数据库连接池 | ~1min |
| `cleanup_redis_memory.py` | 清理 Redis 内存 | ~30s |
| `scale-out.sh` | 水平扩容 | ~1min |

## 🔌 API 端点 (Worker-3)

### Webhook 端点
```
POST /api/v1/webhooks/alerts           # 接收 Alertmanager 告警
POST /api/v1/webhooks/critical-alerts  # 接收严重告警
POST /api/v1/webhooks/warning-alerts   # 接收警告告警
```

### 运维 API
```
GET  /api/v1/ops/healing-events                # 查询修复事件
POST /api/v1/ops/healing-events                # 记录修复事件
POST /api/v1/ops/diagnose/{alert_name}         # 手动触发诊断
POST /api/v1/ops/heal/{alert_name}             # 手动触发修复
```

## 📊 数据模型

### HealingEvent (修复事件)
```python
{
    "id": int,
    "alert_name": str,           # 告警名称
    "action": str,               # 修复动作
    "status": str,               # success/failed
    "duration_seconds": float,   # 执行时间
    "error": str,                # 错误信息 (如果失败)
    "created_at": datetime
}
```

### DiagnosisResult (诊断结果)
```python
{
    "id": int,
    "fault_type": str,           # 故障类型
    "root_cause": str,           # 根因
    "diagnosis_steps": list,     # 诊断步骤
    "recommendations": list,     # 修复建议
    "created_at": datetime
}
```

## 🎨 Grafana 大盘面板 (Worker-3)

| 面板 | 类型 | 查询 |
|-----|------|-----|
| Active Alerts | Table | `ALERTS{alertstate="firing"}` |
| Healing Events Timeline | Graph | `rate(healing_events_total[5m])` |
| Healing Success Rate | Gauge | `sum(rate(healing_events_total{status="success"}[5m])) / sum(rate(healing_events_total[5m]))` |
| Average Healing Time | Stat | `avg(healing_duration_seconds)` |
| Scaling Events | Graph | `rate(scaling_events_total[5m])` |
| Service Replicas | Graph | `count(up{job="backend"})` |

## ⚙️ 配置文件

### 扩缩容策略 (scaling-policies.yml)
```yaml
services:
  backend:
    min_replicas: 2
    max_replicas: 10
    target_cpu_utilization: 70
    target_memory_utilization: 80
    target_qps: 1000
    cooldown:
      scale_out: 180  # 3分钟
      scale_in: 600   # 10分钟
```

## 🔍 故障分类

| 类别 | 告警类型 | 修复策略 | 风险 |
|-----|---------|---------|------|
| 服务故障 | ServiceDown | 重启容器 | 低 |
| 资源故障 | HighCPUUsage | 水平扩容 | 低 |
| 资源故障 | HighMemoryUsage | 重启容器 | 中 |
| 资源故障 | LowDiskSpace | 清理资源 | 低 |
| 数据库故障 | ConnectionPoolExhausted | 重置连接池 | 中 |
| 缓存故障 | RedisMemoryHigh | 清理内存 | 低 |

## 📝 日志格式

### 脚本日志
```bash
[2026-01-24 14:30:00] INFO: 开始自动修复: 重启容器 backend
[2026-01-24 14:30:05] INFO: 容器重启成功
[2026-01-24 14:30:10] SUCCESS: 健康检查通过
```

### 修复事件日志
```json
{
  "action": "restart_container",
  "container": "backend",
  "status": "success",
  "timestamp": "2026-01-24T14:30:10Z"
}
```

## 🧪 测试场景

### 集成测试 (Worker-1)
1. **容器崩溃测试**
   - 停止容器: `docker stop backend`
   - 验证: 告警触发 → 自动重启 → 健康检查通过

2. **CPU 过高测试**
   - 模拟高 CPU: `stress --cpu 8`
   - 验证: 告警触发 → 自动扩容 → CPU 降低

3. **磁盘不足测试**
   - 填充磁盘: `dd if=/dev/zero of=/tmp/bigfile bs=1G count=10`
   - 验证: 告警触发 → 自动清理 → 磁盘释放

4. **数据库连接耗尽测试**
   - 创建大量连接
   - 验证: 告警触发 → 重置连接池 → 连接恢复

## 📚 文档清单

### 技术文档 (Worker-1)
- [x] `OPS_ARCHITECTURE.md` - 系统架构设计 ✅
- [x] `FAULT_DIAGNOSIS.md` - 故障诊断流程 ✅
- [x] `AUTO_HEALING.md` - 自动修复策略 ✅
- [ ] `OPS_USER_GUIDE.md` - 用户指南
- [ ] `PHASE3_COMPLETION_REPORT.md` - 完成报告

### 知识库文档 (Worker-1)
- [ ] `troubleshooting/service-down.md`
- [ ] `troubleshooting/high-cpu.md`
- [ ] `troubleshooting/memory-leak.md`
- [ ] `troubleshooting/database-slow.md`
- [ ] `runbooks/deployment.md`
- [ ] `runbooks/backup-restore.md`
- [ ] `runbooks/scaling.md`
- [ ] `alerts/critical-alerts.md`
- [ ] `alerts/warning-alerts.md`

## ✅ 验收标准

### 功能性
- [ ] 所有告警类型都有自动修复策略
- [ ] 修复成功率 > 95%
- [ ] 平均修复时间 < 2 分钟
- [ ] 支持手动触发诊断和修复

### 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过率 100%
- [ ] 代码符合 PEP 8 规范
- [ ] 错误处理完善

### 文档完整性
- [ ] 所有脚本有使用说明
- [ ] API 有 OpenAPI 文档
- [ ] 知识库完整
- [ ] 用户指南清晰

### 可观测性
- [ ] 运维大盘展示所有指标
- [ ] 告警和修复事件可追溯
- [ ] 扩缩容事件可视化
- [ ] 日志记录完整

## 🚀 快速开始

### Worker-1
```bash
# 创建目录
mkdir -p backend/monitoring/ops/scripts

# 实现诊断脚本
cd backend/monitoring/ops/scripts
touch diagnose_service_down.py
touch diagnose_high_cpu.py
touch diagnose_high_memory.py
touch quick-diagnose.sh
chmod +x *.py *.sh

# 创建知识库
mkdir -p backend/monitoring/ops-knowledge-base/{troubleshooting,runbooks,alerts}
```

### Worker-2
```bash
# 创建修复脚本目录
mkdir -p backend/monitoring/ops/scripts/auto-heal

# 实现修复脚本
cd backend/monitoring/ops/scripts/auto-heal
touch restart-container.sh
touch cleanup-resources.sh
touch reset_db_connections.py
touch cleanup_redis_memory.py
touch scale-out.sh
chmod +x *.sh *.py

# 创建扩缩容引擎
mkdir -p backend/app/ops
touch backend/app/ops/autoscaling.py
```

### Worker-3
```bash
# 创建运维模块
mkdir -p backend/app/ops
touch backend/app/ops/__init__.py
touch backend/app/ops/auto_healing.py
touch backend/app/ops/diagnosis.py

# 创建 API
mkdir -p backend/app/api/v1/endpoints
touch backend/app/api/v1/endpoints/webhooks.py
touch backend/app/api/v1/endpoints/ops.py

# 创建数据模型
touch backend/app/models/ops.py

# 创建大盘
mkdir -p backend/monitoring/grafana/dashboards
touch backend/monitoring/grafana/dashboards/ops-dashboard.json
```

## 📞 需要帮助?

- 查阅执行指南: `backend/monitoring/ops/EXECUTION_GUIDE.md`
- 查阅架构文档: `backend/docs/OPS_ARCHITECTURE.md`
- 查阅诊断流程: `backend/docs/FAULT_DIAGNOSIS.md`
- 查阅修复策略: `backend/docs/AUTO_HEALING.md`
