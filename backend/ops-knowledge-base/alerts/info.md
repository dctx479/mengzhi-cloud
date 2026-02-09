# Info 级别告警处理指南

## 概述

**Info告警定义**: 系统状态变化、配置更新、定期巡检等通知类告警,不影响服务正常运行。

**响应要求**:
- **响应时间**: 工作日内关注
- **解决目标**: 本周内处理或确认
- **通知方式**: 邮件 / 周报
- **升级机制**: 无自动升级

---

## Info 告警列表

| 告警名称 | 描述 | 处理方式 | 处理文档 |
|----------|------|----------|----------|
| ContainerRestarted | 容器重启通知 | 记录,分析原因 | - |
| ConfigurationChanged | 配置文件变更 | 审查变更 | - |
| BackupCompleted | 备份完成通知 | 验证备份 | [backup-restore.md](../runbooks/backup-restore.md) |
| DeploymentCompleted | 部署完成通知 | 验证部署 | [deployment.md](../runbooks/deployment.md) |
| CertificateExpiring | 证书即将过期 | 续期证书 | - |
| LowDiskSpace | 磁盘空间预警 | 清理空间 | - |
| HighConnectionCount | 连接数较高 | 观察趋势 | - |
| SlowBackgroundJob | 后台任务缓慢 | 优化任务 | - |

---

## ContainerRestarted 告警

### 告警信息
```
AlertName: ContainerRestarted
Severity: Info
Description: Container backend restarted
Restart Count: 1
Last Restart: 2026-01-24 03:05:00
Exit Code: 0
```

### 处理步骤

```bash
# 1. 查看重启原因
docker inspect backend | jq '.[0].State'

# 2. 查看重启前日志
docker logs backend --since "2026-01-24T03:00:00" --until "2026-01-24T03:05:00"

# 3. 记录到运维日志
echo "$(date): Container backend restarted, exit code 0" >> /var/log/ops.log
```

### 判断标准

| 退出码 | 含义 | 是否需要关注 |
|-------|------|-------------|
| 0 | 正常退出 | 否,可能是计划重启 |
| 1 | 应用错误 | 是,需要查看日志 |
| 137 | OOMKilled | 是,需要升级为Warning |
| 143 | SIGTERM | 否,手动停止 |

---

## ConfigurationChanged 告警

### 告警信息
```
AlertName: ConfigurationChanged
Severity: Info
Description: Configuration file .env modified
Modified By: user@example.com
Time: 2026-01-24 10:30:00
```

### 处理步骤

```bash
# 1. 查看变更内容
git diff HEAD~1 HEAD -- .env

# 2. 验证配置合法性
docker-compose config

# 3. 如果变更未经审批,回滚
git revert HEAD
docker-compose restart
```

---

## BackupCompleted 告警

### 告警信息
```
AlertName: BackupCompleted
Severity: Info
Description: Database backup completed successfully
Backup File: backup_20260124_030000.dump
Size: 2.3 GB
Duration: 15 minutes
```

### 处理步骤

```bash
# 1. 验证备份文件存在
ls -lh /backup/postgres/backup_20260124_030000.dump

# 2. 验证备份完整性
./scripts/verify-backup.sh backup_20260124_030000.dump

# 3. 确认备份已上传到远程存储
aws s3 ls s3://backups/postgres/backup_20260124_030000.dump
```

---

## CertificateExpiring 告警

### 告警信息
```
AlertName: CertificateExpiring
Severity: Info
Description: SSL certificate expires in 30 days
Domain: api.example.com
Expiry Date: 2026-02-24
```

### 处理步骤

```bash
# 1. 验证证书到期时间
openssl x509 -in /etc/ssl/api.example.com.crt -noout -enddate

# 2. 续期证书 (Let's Encrypt)
certbot renew --dry-run
certbot renew

# 3. 重启服务应用新证书
docker-compose restart nginx
```

---

## LowDiskSpace 告警

### 告警信息
```
AlertName: LowDiskSpace
Severity: Info
Description: Disk usage > 70%
Current Value: 75%
Mountpoint: /var/lib/docker
```

### 处理步骤

```bash
# 1. 查看磁盘使用
df -h
du -sh /var/lib/docker/* | sort -hr | head -10

# 2. 清理Docker资源
docker system df  # 查看Docker磁盘使用
docker system prune -a  # 清理未使用资源

# 3. 清理旧日志
find /var/log -name "*.log" -mtime +30 -delete
journalctl --vacuum-time=30d

# 4. 清理旧备份
find /backup -name "*.dump" -mtime +7 -delete
```

---

## Info 告警处理原则

### 1. 不要忽视
- Info告警虽然不紧急,但可能预示潜在问题
- 定期审查Info告警,发现趋势

### 2. 批量处理
- 每周固定时间集中处理Info告警
- 使用工具汇总和分类

### 3. 自动化
- 尽量将Info告警处理自动化
- 减少人工介入

### 4. 统计分析
- 统计Info告警频率
- 识别重复出现的问题

---

## 每周Info告警审查清单

```markdown
# 本周Info告警汇总 (2026-01-20 ~ 2026-01-26)

## 统计
- ContainerRestarted: 3次
- BackupCompleted: 7次
- ConfigurationChanged: 1次
- LowDiskSpace: 2次

## 需要关注的
- [ ] backend容器重启3次,最后一次退出码为1,需要排查原因
- [ ] 磁盘空间使用持续上升,已达75%,需要扩容或清理

## 已处理的
- [x] 证书续期完成
- [x] 旧备份清理完成
- [x] 日志轮转配置优化

## 下周计划
- 优化磁盘使用,实施日志自动清理
- 调查backend重启原因
```

---

## 告警优化建议

### 减少噪音
```yaml
# 优化告警规则,减少误报
# prometheus/alerts.yml

# 修改前: 容器重启立即告警
- alert: ContainerRestarted
  expr: rate(container_restart_count[5m]) > 0

# 修改后: 短时间内多次重启才告警
- alert: ContainerRestartingFrequently
  expr: rate(container_restart_count[10m]) > 0.1
  for: 5m
```

### 告警聚合
```yaml
# 将同类Info告警聚合为一条
- alert: DailyOpsReport
  expr: |
    (
      count(container_restart_count > 0) OR
      count(backup_completed == 1) OR
      count(disk_usage_percent > 0.7)
    )
  for: 24h
  annotations:
    summary: "Daily Ops Report: {{ $value }} events"
```

---

## 相关文档

- [Critical告警处理](./critical.md)
- [Warning告警处理](./warning.md)
- [告警规则配置](../../prometheus/alerts.yml)
