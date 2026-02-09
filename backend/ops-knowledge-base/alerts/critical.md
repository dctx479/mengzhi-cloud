# Critical 级别告警处理指南

## 概述

本文档描述了所有 Critical 级别告警的处理流程、责任人、响应时间要求。

**Critical告警定义**: 影响系统核心功能,导致服务不可用或数据丢失风险的告警。

**响应要求**:
- **响应时间**: 5分钟内
- **解决目标**: 30分钟内恢复服务
- **通知方式**: 电话 + 短信 + Slack
- **升级机制**: 15分钟无响应自动升级

---

## Critical 告警列表

| 告警名称 | 描述 | 影响 | SLA | 处理文档 |
|----------|------|------|-----|----------|
| ServiceDown | 服务完全不可用 | 全部用户 | 99.9% | [service-down.md](../troubleshooting/service-down.md) |
| DatabaseDown | 数据库不可用 | 全部用户 | 99.9% | [database-slow.md](../troubleshooting/database-slow.md) |
| DataLoss | 数据丢失风险 | 数据完整性 | 0容忍 | [data-loss.md](../troubleshooting/data-loss.md) |
| SecurityBreach | 安全入侵 | 系统安全 | 立即 | [security-incident.md](../troubleshooting/security-incident.md) |
| DiskFull | 磁盘空间耗尽 | 服务降级 | 15分钟 | [disk-full.md](../troubleshooting/disk-full.md) |
| CriticalCPUUsage | CPU持续100% | 服务缓慢 | 10分钟 | [high-cpu.md](../troubleshooting/high-cpu.md) |
| OOMKilled | 容器被OOM Kill | 服务重启 | 5分钟 | [memory-leak.md](../troubleshooting/memory-leak.md) |

---

## ServiceDown 告警处理

### 告警信息
```
AlertName: ServiceDown
Severity: Critical
Description: Backend service is down for more than 1 minute
Instance: ai-platform-backend:8000
Time: 2026-01-24 14:30:00
```

### 立即行动 (First 5 Minutes)

```bash
# 1. 确认服务状态 (30秒)
docker ps -a | grep backend
curl -f http://localhost:8000/health

# 2. 查看最近日志 (30秒)
docker logs --tail 50 backend

# 3. 快速重启 (如果容器已停止)
docker restart backend

# 4. 等待并验证 (1分钟)
sleep 10
curl -f http://localhost:8000/health
```

### 如果快速重启失败

**执行完整诊断**:
```bash
# 运行诊断脚本
/usr/local/bin/diagnose-service-down.sh

# 根据诊断结果采取行动:
# - OOMKilled → 增加内存限制
# - 数据库连接失败 → 检查数据库
# - 配置错误 → 恢复配置文件
```

### 升级路径

| 时间 | 行动 | 责任人 |
|------|------|--------|
| 0-5分钟 | 值班工程师尝试快速修复 | On-Call Engineer |
| 5-15分钟 | 执行标准故障排查流程 | On-Call Engineer |
| 15-30分钟 | 升级到技术负责人 | Tech Lead |
| 30分钟+ | 启动应急预案,通知管理层 | CTO |

---

## DatabaseDown 告警处理

### 告警信息
```
AlertName: DatabaseDown
Severity: Critical
Description: PostgreSQL is unreachable
Instance: postgres:5432
```

### 立即行动

```bash
# 1. 检查数据库容器
docker ps | grep postgres
docker logs --tail 50 postgres

# 2. 尝试重启
docker restart postgres

# 3. 检查数据完整性
docker exec postgres pg_isready -U ai_platform

# 4. 如果重启失败,从备份恢复
docker-compose down
docker volume rm ai-platform_postgres_data
docker-compose up -d postgres
docker exec postgres pg_restore -U ai_platform -d ai_platform backup_latest.dump
```

---

## DataLoss 告警处理

### 告警信息
```
AlertName: DataLoss
Severity: Critical
Description: Data inconsistency detected
Tables Affected: posts, users
```

### 立即行动

```bash
# 1. 立即停止写入操作
docker-compose stop backend

# 2. 评估数据损失范围
docker exec postgres psql -U ai_platform -c "SELECT COUNT(*) FROM posts;"

# 3. 从最近备份恢复
./scripts/restore-from-backup.sh backup_latest.dump

# 4. 验证数据完整性
./scripts/verify-data-integrity.sh

# 5. 通知所有相关人员
# 6. 记录故障报告
```

**重要**: 数据丢失是最严重的事故,必须立即通知管理层和客户。

---

## SecurityBreach 告警处理

### 告警信息
```
AlertName: SecurityBreach
Severity: Critical
Description: Suspicious activity detected
Source IP: 192.168.1.100
Attack Type: SQL Injection
```

### 立即行动

```bash
# 1. 隔离受影响系统
docker-compose stop backend

# 2. 阻止攻击源
sudo iptables -A INPUT -s 192.168.1.100 -j DROP

# 3. 收集证据
docker logs backend > security_incident_$(date +%Y%m%d_%H%M%S).log

# 4. 通知安全团队
# 5. 启动安全事件响应流程
# 6. 不要清理现场,保留所有日志
```

**重要**: 安全事件必须由专业安全团队处理,不要擅自操作。

---

## OOMKilled 告警处理

### 告警信息
```
AlertName: ContainerOOMKilled
Severity: Critical
Description: Container killed due to OOM
Container: backend
Memory Limit: 2GB
Memory Used: 2.1GB
```

### 立即行动

```bash
# 1. 重启容器
docker restart backend

# 2. 临时增加内存限制
docker update --memory="4g" backend
docker restart backend

# 3. 查看内存使用趋势
curl 'http://localhost:9090/api/v1/query_range?query=container_memory_usage_bytes{container="backend"}&start='$(date -d '1 hour ago' +%s)'&end='$(date +%s)'&step=60'

# 4. 后续: 分析内存泄漏原因
```

---

## 告警响应最佳实践

### 1. 保持冷静
- 不要慌张,按照标准流程操作
- 记录所有操作步骤
- 不要跳过诊断直接修复

### 2. 优先恢复服务
- 先恢复服务,后分析根因
- 使用已知可行的方法 (如重启)
- 如果不确定,选择最安全的方案

### 3. 沟通透明
- 及时更新告警处理进度
- 通知受影响用户
- 记录故障时间线

### 4. 事后分析
- 完成故障报告
- 分析根本原因
- 制定预防措施

---

## 告警处理模板

```markdown
# 故障处理记录

## 基本信息
- 告警名称: ServiceDown
- 告警时间: 2026-01-24 14:30:00
- 响应时间: 2026-01-24 14:32:00
- 恢复时间: 2026-01-24 14:45:00
- 影响时长: 15分钟
- 处理人员: 张三

## 故障现象
- 服务完全不可用
- 用户无法登录
- Grafana显示服务离线

## 处理过程
1. [14:32] 确认告警,检查服务状态
2. [14:33] 发现容器已停止,退出码137 (OOMKilled)
3. [14:34] 重启容器,增加内存限制
4. [14:35] 服务恢复正常
5. [14:45] 完成验证,告警解除

## 根本原因
- 处理大文件上传时内存溢出
- 容器内存限制2GB不足
- 未使用流式处理

## 修复措施
- 临时: 增加内存限制到4GB
- 永久: 优化文件处理逻辑,使用流式处理

## 预防措施
- 添加内存使用预警 (85%)
- 代码审查: 所有文件操作使用流式处理
- 定期压测验证容量
```

---

## 相关文档

- [Warning告警处理](./warning.md)
- [故障排查手册](../troubleshooting/)
- [应急预案](../runbooks/emergency-response.md)
