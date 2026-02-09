# 运维知识库 (Ops Knowledge Base)

## 概述

本知识库提供AI平台的完整运维文档,包括故障排查、操作手册和告警处理指南。

**目标**:
- 📖 标准化运维流程
- ⚡ 快速故障定位和恢复
- 🧠 沉淀运维经验和最佳实践
- 🤖 支持智能运维系统

---

## 文档结构

```
ops-knowledge-base/
├── troubleshooting/     # 故障排查手册
│   ├── service-down.md          # 服务不可用排查 ⭐
│   ├── high-cpu.md              # CPU过高排查 ⭐
│   ├── memory-leak.md           # 内存泄漏排查 ⭐
│   ├── database-slow.md         # 数据库慢查询 ⭐
│   └── network-issues.md        # 网络问题排查
├── runbooks/            # 操作手册
│   ├── deployment.md            # 部署操作 ⭐
│   ├── backup-restore.md        # 备份恢复 ⭐
│   ├── scaling.md               # 服务扩容
│   └── rollback.md              # 回滚操作 ⭐
└── alerts/              # 告警处理指南
    ├── critical.md              # Critical告警 ⭐
    ├── warning.md               # Warning告警
    └── info.md                  # Info告警

⭐ = 核心文档,必读
```

---

## 快速导航

### 🚨 故障排查

#### 服务不可用
**症状**: 服务完全不可用,返回502/503错误

**快速诊断**:
```bash
docker ps -a | grep backend
docker logs --tail 50 backend
curl -f http://localhost:8000/health
```

**详细文档**: [troubleshooting/service-down.md](./troubleshooting/service-down.md)

---

#### CPU使用率过高
**症状**: CPU持续 > 80%,响应变慢

**快速诊断**:
```bash
docker stats backend --no-stream
docker exec backend top -bn1 | head -20
```

**详细文档**: [troubleshooting/high-cpu.md](./troubleshooting/high-cpu.md)

---

#### 内存泄漏
**症状**: 内存持续增长,最终OOM

**快速诊断**:
```bash
docker stats backend --no-stream
# 查看内存趋势图 (Grafana)
```

**详细文档**: [troubleshooting/memory-leak.md](./troubleshooting/memory-leak.md)

---

#### 数据库查询慢
**症状**: API响应慢,数据库CPU高

**快速诊断**:
```sql
-- 查看慢查询
SELECT query, mean_exec_time FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;
```

**详细文档**: [troubleshooting/database-slow.md](./troubleshooting/database-slow.md)

---

### 📋 运维操作

#### 部署
**场景**: 新版本上线

**快速命令**:
```bash
./scripts/deploy.sh v1.2.0
```

**详细文档**: [runbooks/deployment.md](./runbooks/deployment.md)

---

#### 回滚
**场景**: 新版本有问题,需要回滚

**快速命令**:
```bash
./scripts/quick-rollback.sh v1.1.0
```

**详细文档**: [runbooks/rollback.md](./runbooks/rollback.md)

---

#### 备份与恢复
**场景**: 定期备份或灾难恢复

**快速命令**:
```bash
# 备份
./scripts/backup-db.sh

# 恢复
./scripts/restore-db.sh backup_20260124.dump
```

**详细文档**: [runbooks/backup-restore.md](./runbooks/backup-restore.md)

---

#### 扩容
**场景**: 流量增长,需要扩容

**快速命令**:
```bash
docker-compose up -d --scale backend=3
```

**详细文档**: [runbooks/scaling.md](./runbooks/scaling.md)

---

### 🔔 告警处理

#### Critical告警
**响应时间**: 5分钟内

**常见告警**:
- ServiceDown: 服务不可用
- DatabaseDown: 数据库不可用
- OOMKilled: 容器被Kill
- DataLoss: 数据丢失风险

**详细文档**: [alerts/critical.md](./alerts/critical.md)

---

#### Warning告警
**响应时间**: 30分钟内

**常见告警**:
- HighCPUUsage: CPU > 80%
- HighMemoryUsage: 内存 > 85%
- HighResponseTime: 响应时间 > 2s
- SlowDatabaseQuery: 查询 > 1s

**详细文档**: [alerts/warning.md](./alerts/warning.md)

---

#### Info告警
**响应时间**: 工作日内

**常见告警**:
- ContainerRestarted: 容器重启
- BackupCompleted: 备份完成
- CertificateExpiring: 证书即将过期

**详细文档**: [alerts/info.md](./alerts/info.md)

---

## 常见场景

### 场景1: 收到 ServiceDown 告警

**立即行动** (First 5 Minutes):
```bash
# 1. 确认服务状态
docker ps -a | grep backend

# 2. 查看日志
docker logs --tail 50 backend

# 3. 尝试重启
docker restart backend

# 4. 验证恢复
curl -f http://localhost:8000/health
```

**如果重启失败**: 参考 [troubleshooting/service-down.md](./troubleshooting/service-down.md)

---

### 场景2: 部署新版本

**标准流程**:
```bash
# 1. 备份
./scripts/backup-db.sh

# 2. 部署
./scripts/deploy.sh v1.2.0

# 3. 验证
curl -f http://localhost:8000/health
./scripts/smoke-test.sh

# 4. 监控观察 (30分钟)
```

**如果部署失败**: 参考 [runbooks/rollback.md](./runbooks/rollback.md)

---

### 场景3: 数据库查询变慢

**快速诊断**:
```sql
-- 1. 查看慢查询
SELECT query, mean_exec_time FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;

-- 2. 分析查询计划
EXPLAIN ANALYZE <slow_query>;

-- 3. 检查是否缺少索引
EXPLAIN <slow_query>;
-- 看到 Seq Scan → 需要添加索引
```

**修复方案**: 参考 [troubleshooting/database-slow.md](./troubleshooting/database-slow.md)

---

### 场景4: CPU使用率持续高位

**快速诊断**:
```bash
# 1. 查看CPU占用
docker exec backend top -bn1 | head -20

# 2. 生成火焰图
PID=$(docker exec backend pgrep -f uvicorn)
docker exec backend py-spy record -o /tmp/profile.svg --pid $PID --duration 30

# 3. 分析热点代码
```

**优化方案**: 参考 [troubleshooting/high-cpu.md](./troubleshooting/high-cpu.md)

---

## 诊断工具

### 快速诊断脚本

```bash
# 服务不可用诊断
/usr/local/bin/diagnose-service-down.sh

# CPU过高诊断
/usr/local/bin/diagnose-high-cpu.sh

# 内存泄漏诊断
/usr/local/bin/diagnose-memory-leak.sh

# 综合诊断 (收集所有信息)
/usr/local/bin/quick-diagnose.sh
```

### 监控大盘

- **Grafana**: http://localhost:3000
  - Service Overview Dashboard
  - Container Metrics Dashboard
  - Database Metrics Dashboard

- **Prometheus**: http://localhost:9090
  - 查询指标
  - 查看告警规则

---

## 最佳实践

### 故障处理原则

1. **快速恢复优先**: 先恢复服务,后分析根因
2. **遵循标准流程**: 不跳步骤,记录操作
3. **保留现场**: 保留日志和镜像供后续分析
4. **及时通知**: 告知相关方故障状态
5. **事后总结**: 完成故障报告,沉淀经验

### 运维操作原则

1. **变更前备份**: 所有变更前必须备份
2. **渐进式操作**: 分步骤执行,每步验证
3. **监控验证**: 操作后持续监控30分钟
4. **文档记录**: 更新配置和操作文档
5. **自动化优先**: 重复操作自动化

### 监控告警原则

1. **分级响应**: Critical 5分钟, Warning 30分钟, Info 工作日
2. **减少噪音**: 优化告警规则,避免误报
3. **上下文丰富**: 告警包含足够诊断信息
4. **可操作**: 每个告警都有对应处理文档
5. **持续优化**: 定期审查告警有效性

---

## 知识库使用指南

### 新手入门

1. 阅读核心文档 (标记⭐的文档)
2. 熟悉常见场景处理流程
3. 了解监控大盘和告警规则
4. 实践使用诊断工具

### 日常运维

1. 关注告警通知
2. 定期查看监控大盘
3. 执行定期巡检任务
4. 记录运维操作日志

### 故障处理

1. 根据告警查找对应文档
2. 按照文档执行诊断步骤
3. 记录处理过程和结果
4. 更新知识库 (如发现新问题)

### 持续改进

1. 每周审查告警统计
2. 识别重复问题,制定预防措施
3. 优化诊断脚本和工具
4. 更新和完善文档

---

## 贡献指南

### 更新现有文档

1. 发现文档不准确或过时
2. 创建分支进行修改
3. 提交 PR 并说明修改原因
4. 经审核后合并

### 添加新文档

1. 识别缺失的故障场景或操作流程
2. 按照模板创建文档
3. 包含: 概述、诊断步骤、修复方案、案例
4. 提交 PR 供审核

### 文档模板

#### 故障排查文档模板

```markdown
# [故障名称] 排查手册

## 概述
- 问题描述
- 影响范围
- 典型场景

## 症状识别
- 监控告警
- 用户表现
- Grafana大盘

## 快速诊断
- 诊断决策树
- 快速检查命令

## 详细诊断步骤
- Step 1: ...
- Step 2: ...

## 修复方案
- 自动修复
- 手动修复

## 预防措施
- 监控优化
- 代码优化

## 历史案例
- 案例1: ...
- 案例2: ...

## 相关文档
```

---

## 智能运维集成

### AI Agent 使用

本知识库支持智能运维 Agent 自动调用:

```python
# 示例: 诊断 ServiceDown 问题
from app.ops.diagnosis import DiagnosisEngine

engine = DiagnosisEngine(knowledge_base_path="ops-knowledge-base/")
result = await engine.diagnose("ServiceDown", container="backend")

# 输出:
# {
#   "fault_type": "ServiceDown",
#   "root_cause": "Container OOMKilled",
#   "recommendations": ["增加内存限制到4GB", "优化内存使用"],
#   "reference_doc": "troubleshooting/service-down.md#oomkilled"
# }
```

### 自动修复集成

```python
# 示例: 自动执行修复方案
from app.ops.auto_healing import AutoHealer

healer = AutoHealer()
result = await healer.execute_fix(
    fault_type="ServiceDown",
    root_cause="OOMKilled",
    container="backend"
)

# 自动执行:
# 1. 增加内存限制
# 2. 重启容器
# 3. 验证恢复
# 4. 记录操作日志
```

---

## 联系方式

- **运维团队**: ops@example.com
- **技术负责人**: tech-lead@example.com
- **紧急联系**: +86-xxx-xxxx-xxxx
- **Slack频道**: #ops-alerts

---

## 版本历史

- **v1.0.0** (2026-01-24): 初始版本
  - 5个故障排查文档
  - 4个运维操作手册
  - 3个告警处理指南
  - 完整的诊断工具和脚本

---

## 相关资源

- [系统架构文档](../docs/ARCHITECTURE.md)
- [监控指标说明](../docs/MONITORING.md)
- [故障诊断流程](../docs/FAULT_DIAGNOSIS.md)
- [Prometheus告警规则](../prometheus/alerts.yml)
- [Grafana Dashboard配置](../grafana/dashboards/)

---

**最后更新**: 2026-01-24
**维护者**: 运维团队
