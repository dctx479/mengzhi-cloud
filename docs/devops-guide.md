# AI赋能云平台 - 自动化运维系统指南

## 概述

本文档详细介绍了AI赋能云平台的自动化运维系统，包括CI/CD流程、自动化脚本使用、监控告警、故障处理等运维相关内容。

## 目录

- [1. 系统架构](#1-系统架构)
- [2. CI/CD流程](#2-cicd流程)
- [3. 自动化脚本](#3-自动化脚本)
- [4. 监控与告警](#4-监控与告警)
- [5. 故障处理](#5-故障处理)
- [6. 安全管理](#6-安全管理)
- [7. 性能优化](#7-性能优化)
- [8. 备份与恢复](#8-备份与恢复)
- [9. 日常维护](#9-日常维护)
- [10. 应急预案](#10-应急预案)

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    负载均衡层 (Nginx)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                 应用层                                       │
│  ┌─────────────┐   │   ┌─────────────┐   ┌─────────────┐   │
│  │   前端服务   │   │   │   后端服务   │   │   API网关    │   │
│  │  (Vue.js)   │   │   │ (FastAPI)   │   │             │   │
│  └─────────────┘   │   └─────────────┘   └─────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                 数据层                                       │
│  ┌─────────────┐   │   ┌─────────────┐   ┌─────────────┐   │
│  │    MySQL    │   │   │    Redis    │   │  文件存储    │   │
│  │   (主数据)   │   │   │   (缓存)    │   │   (OSS)     │   │
│  └─────────────┘   │   └─────────────┘   └─────────────┘   │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│               基础设施层                                     │
│  ┌─────────────┐   │   ┌─────────────┐   ┌─────────────┐   │
│  │   Docker    │   │   │   监控系统   │   │   日志系统   │   │
│  │  容器化部署  │   │   │ (Prometheus)│   │ (ELK Stack) │   │
│  └─────────────┘   │   └─────────────┘   └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 部署环境

| 环境 | 用途 | 配置 | 访问地址 |
|------|------|------|----------|
| 开发环境 | 开发测试 | 2C4G | http://dev.agri-platform.com |
| 预生产环境 | 集成测试 | 4C8G | http://staging.agri-platform.com |
| 生产环境 | 正式服务 | 8C16G | https://agri-platform.com |

### 1.3 技术栈

- **前端**: Vue.js 3 + TypeScript + Element Plus
- **后端**: Python FastAPI + SQLAlchemy + Alembic
- **数据库**: MySQL 8.0 + Redis 7.0
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack (Elasticsearch + Logstash + Kibana)

## 2. CI/CD流程

### 2.1 流程概述

```mermaid
graph LR
    A[代码提交] --> B[CI触发]
    B --> C[代码检查]
    C --> D[单元测试]
    D --> E[构建镜像]
    E --> F[集成测试]
    F --> G[部署到开发环境]
    G --> H[部署到预生产环境]
    H --> I[生产环境部署]
    I --> J[健康检查]
    J --> K[通知完成]
```

### 2.2 CI配置 (.github/workflows/ci.yml)

**触发条件**:
- 推送到 `main` 或 `develop` 分支
- 创建 Pull Request

**执行步骤**:
1. **前端测试**: ESLint检查、单元测试、构建验证
2. **后端测试**: 代码格式检查、类型检查、单元测试
3. **代码质量**: 安全扫描、依赖检查
4. **Docker构建**: 构建并测试Docker镜像
5. **集成测试**: 端到端测试
6. **性能测试**: 负载测试（仅主分支）

### 2.3 CD配置 (.github/workflows/cd.yml)

**部署策略**:
- **开发环境**: 自动部署 `develop` 分支
- **预生产环境**: 自动部署 `main` 分支
- **生产环境**: 手动触发，使用蓝绿部署

**部署流程**:
1. 构建并推送Docker镜像到Registry
2. 连接目标服务器
3. 拉取最新镜像
4. 滚动更新服务
5. 健康检查
6. 发送部署通知

### 2.4 环境变量配置

**GitHub Secrets**:
```bash
# 开发环境
DEV_HOST=dev.example.com
DEV_USERNAME=deploy
DEV_SSH_KEY=<私钥内容>
DEV_BASE_URL=http://dev.agri-platform.com

# 预生产环境
STAGING_HOST=staging.example.com
STAGING_USERNAME=deploy
STAGING_SSH_KEY=<私钥内容>
STAGING_BASE_URL=http://staging.agri-platform.com

# 生产环境
PROD_HOST=prod.example.com
PROD_USERNAME=deploy
PROD_SSH_KEY=<私钥内容>
PROD_BASE_URL=https://agri-platform.com

# 通知配置
SLACK_WEBHOOK_URL=<Slack Webhook URL>
DINGTALK_WEBHOOK_URL=<钉钉 Webhook URL>
```

## 3. 自动化脚本

### 3.1 数据库备份脚本

**位置**: `scripts/backup/backup-database.sh` (Linux) / `backup-database.bat` (Windows)

**功能**:
- 自动备份MySQL数据库
- 压缩备份文件
- 上传到OSS存储
- 清理过期备份
- 发送备份状态通知

**使用方法**:
```bash
# Linux
./scripts/backup/backup-database.sh

# 指定配置文件
./scripts/backup/backup-database.sh -c /path/to/config.conf

# 指定数据库和输出目录
./scripts/backup/backup-database.sh -d agri_platform -o /backup/mysql

# 模拟运行
./scripts/backup/backup-database.sh --dry-run

# Windows
scripts\backup\backup-database.bat
scripts\backup\backup-database.bat /c config.bat
scripts\backup\backup-database.bat /d agri_platform /o C:\Backup\MySQL
```

**配置文件** (`backup-config.conf`):
```bash
# 数据库连接
DB_HOST=localhost
DB_PORT=3307
DB_USER=backup_user
DB_PASSWORD=backup_pass
DB_NAME=agri_platform

# 备份设置
BACKUP_DIR=/opt/backups/mysql
BACKUP_RETENTION_DAYS=7
COMPRESS_BACKUP=true

# OSS配置
OSS_ENABLED=true
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET=agri-platform-backup

# 通知配置
NOTIFICATION_ENABLED=true
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

**定时任务设置**:
```bash
# 每天凌晨2点执行备份
0 2 * * * /opt/agri-platform/scripts/backup/backup-database.sh
```

### 3.2 健康检查脚本

**位置**: `scripts/health-check/health-check.sh` (Linux) / `health-check.bat` (Windows)

**检查项目**:
- 系统服务状态 (MySQL, Redis, Nginx, Docker)
- Docker容器状态
- 数据库连接
- Redis连接
- 磁盘空间使用率
- 内存使用率
- CPU使用率
- 网络连接
- API端点响应
- 应用日志错误

**使用方法**:
```bash
# 执行一次检查
./scripts/health-check/health-check.sh

# 后台持续监控
./scripts/health-check/health-check.sh --daemon

# 停止后台监控
./scripts/health-check/health-check.sh --stop

# 指定检查间隔
./scripts/health-check/health-check.sh -i 30 --daemon
```

**配置文件** (`health-check-config.conf`):
```bash
# 检查配置
CHECK_INTERVAL=60
DISK_USAGE_THRESHOLD=80
MEMORY_USAGE_THRESHOLD=85
CPU_USAGE_THRESHOLD=90

# 服务配置
SERVICES_TO_CHECK="docker mysql redis nginx"
DOCKER_CONTAINERS="agri-backend agri-frontend agri-mysql agri-redis"

# API端点
API_ENDPOINTS_TO_CHECK="http://localhost:5000/health"

# 通知配置
NOTIFICATION_ENABLED=true
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

### 3.3 自动化部署脚本

**位置**: `scripts/deploy/deploy.sh` (Linux) / `deploy.bat` (Windows)

**部署流程**:
1. 创建部署备份
2. 拉取最新代码
3. 构建应用
4. 安装依赖
5. 执行数据库迁移
6. 重启服务
7. 健康检查
8. 运行测试
9. 清理旧备份

**使用方法**:
```bash
# 标准部署
./scripts/deploy/deploy.sh

# 部署指定分支
./scripts/deploy/deploy.sh -b develop

# 跳过测试的部署
./scripts/deploy/deploy.sh --no-tests

# 回滚到指定部署
./scripts/deploy/deploy.sh --rollback deploy_20240123_143052

# 模拟运行
./scripts/deploy/deploy.sh --dry-run
```

**配置文件** (`deploy-config.conf`):
```bash
# 项目配置
PROJECT_DIR=/opt/agri-platform
GIT_REPO=https://github.com/your-org/agri-platform.git
GIT_BRANCH=main

# 部署配置
ENABLE_BACKUP=true
ENABLE_MIGRATION=true
ENABLE_TESTS=false
ROLLBACK_ON_FAILURE=true
HEALTH_CHECK_TIMEOUT=300

# 通知配置
NOTIFICATION_ENABLED=true
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

### 3.4 日志清理脚本

**位置**: `scripts/maintenance/cleanup-logs.sh` (Linux) / `cleanup-logs.bat` (Windows)

**清理范围**:
- 应用日志文件
- 系统日志文件
- Docker容器日志
- Nginx访问日志
- 数据库日志文件
- 空目录清理

**使用方法**:
```bash
# 标准清理
./scripts/maintenance/cleanup-logs.sh

# 指定保留天数
./scripts/maintenance/cleanup-logs.sh -r 15

# 清理指定路径
./scripts/maintenance/cleanup-logs.sh -p /var/log/myapp

# 不压缩，直接删除
./scripts/maintenance/cleanup-logs.sh --no-compress
```

**定时任务设置**:
```bash
# 每周日凌晨3点执行日志清理
0 3 * * 0 /opt/agri-platform/scripts/maintenance/cleanup-logs.sh
```

## 4. 监控与告警

### 4.1 监控指标

**系统指标**:
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络I/O
- 负载均衡

**应用指标**:
- 请求响应时间
- 请求成功率
- 并发用户数
- 数据库连接数
- 缓存命中率

**业务指标**:
- 用户注册数
- 订单成交量
- 支付成功率
- 数据处理量

### 4.2 告警规则

**系统告警**:
```yaml
# CPU使用率超过80%
- alert: HighCPUUsage
  expr: cpu_usage_percent > 80
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "CPU使用率过高"

# 内存使用率超过85%
- alert: HighMemoryUsage
  expr: memory_usage_percent > 85
  for: 5m
  labels:
    severity: warning

# 磁盘使用率超过90%
- alert: HighDiskUsage
  expr: disk_usage_percent > 90
  for: 2m
  labels:
    severity: critical
```

**应用告警**:
```yaml
# API响应时间超过2秒
- alert: SlowAPIResponse
  expr: api_response_time > 2000
  for: 3m
  labels:
    severity: warning

# 错误率超过5%
- alert: HighErrorRate
  expr: error_rate > 0.05
  for: 2m
  labels:
    severity: critical

# 数据库连接数超过80%
- alert: HighDBConnections
  expr: db_connections_percent > 80
  for: 5m
  labels:
    severity: warning
```

### 4.3 告警通知

**通知渠道**:
- 钉钉群消息
- 邮件通知
- 短信告警（紧急情况）
- Slack通知

**通知配置**:
```yaml
# 钉钉通知
dingtalk:
  webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
  at_mobiles: ["13800138000"]

# 邮件通知
email:
  smtp_server: "smtp.example.com"
  smtp_port: 587
  username: "alert@example.com"
  password: "password"
  to: ["admin@example.com", "ops@example.com"]

# 短信通知
sms:
  provider: "aliyun"
  access_key: "xxx"
  secret_key: "xxx"
  template_id: "SMS_123456789"
  phones: ["13800138000"]
```

## 5. 故障处理

### 5.1 常见故障及处理方法

#### 5.1.1 服务无法启动

**症状**: Docker容器启动失败或频繁重启

**排查步骤**:
1. 查看容器日志
   ```bash
   docker logs agri-backend
   docker logs agri-frontend
   ```

2. 检查配置文件
   ```bash
   # 检查环境变量
   cat .env

   # 检查Docker Compose配置
   docker-compose config
   ```

3. 检查端口占用
   ```bash
   netstat -tlnp | grep :5000
   netstat -tlnp | grep :5173
   ```

4. 检查磁盘空间
   ```bash
   df -h
   ```

**解决方案**:
- 修复配置文件错误
- 释放磁盘空间
- 重启相关服务
- 回滚到上一个稳定版本

#### 5.1.2 数据库连接失败

**症状**: 应用无法连接到MySQL数据库

**排查步骤**:
1. 检查数据库服务状态
   ```bash
   docker ps | grep mysql
   systemctl status mysql
   ```

2. 测试数据库连接
   ```bash
   mysql -h localhost -P 3307 -u agri_user -p
   ```

3. 检查数据库日志
   ```bash
   docker logs agri-mysql
   tail -f /var/log/mysql/error.log
   ```

**解决方案**:
- 重启MySQL服务
- 检查用户权限
- 修复数据库配置
- 恢复数据库备份

#### 5.1.3 Redis连接失败

**症状**: 缓存功能异常，Redis连接超时

**排查步骤**:
1. 检查Redis服务状态
   ```bash
   docker ps | grep redis
   redis-cli -h localhost -p 6380 ping
   ```

2. 检查Redis配置
   ```bash
   docker exec agri-redis redis-cli config get "*"
   ```

**解决方案**:
- 重启Redis服务
- 清理Redis内存
- 调整Redis配置

#### 5.1.4 磁盘空间不足

**症状**: 系统响应缓慢，日志写入失败

**排查步骤**:
1. 检查磁盘使用情况
   ```bash
   df -h
   du -sh /var/log/*
   du -sh /opt/agri-platform/*
   ```

2. 查找大文件
   ```bash
   find / -type f -size +100M 2>/dev/null
   ```

**解决方案**:
- 清理日志文件
- 删除临时文件
- 清理Docker镜像和容器
- 扩容磁盘

### 5.2 故障处理流程

```mermaid
graph TD
    A[故障发生] --> B[告警触发]
    B --> C[故障确认]
    C --> D[影响评估]
    D --> E[应急处理]
    E --> F[根因分析]
    F --> G[永久修复]
    G --> H[验证修复]
    H --> I[总结归档]
```

### 5.3 故障等级定义

| 等级 | 定义 | 响应时间 | 处理时间 |
|------|------|----------|----------|
| P0 | 系统完全不可用 | 5分钟 | 1小时 |
| P1 | 核心功能异常 | 15分钟 | 4小时 |
| P2 | 部分功能异常 | 30分钟 | 1天 |
| P3 | 性能问题 | 1小时 | 3天 |
| P4 | 一般问题 | 4小时 | 1周 |

## 6. 安全管理

### 6.1 访问控制

**SSH访问**:
- 禁用root直接登录
- 使用密钥认证
- 配置防火墙规则
- 定期更换密钥

**数据库访问**:
- 创建专用数据库用户
- 限制访问IP
- 使用强密码
- 定期审计访问日志

**应用访问**:
- 实施HTTPS
- 配置CORS策略
- 使用JWT认证
- 实施API限流

### 6.2 数据安全

**数据加密**:
- 数据库字段加密
- 传输层加密(TLS)
- 备份文件加密
- 敏感配置加密

**备份安全**:
- 定期备份验证
- 异地备份存储
- 备份访问控制
- 备份恢复测试

### 6.3 安全监控

**入侵检测**:
- 异常登录监控
- 文件完整性检查
- 网络流量分析
- 恶意请求检测

**安全审计**:
- 访问日志审计
- 权限变更审计
- 配置变更审计
- 安全事件记录

## 7. 性能优化

### 7.1 应用性能优化

**后端优化**:
- 数据库查询优化
- 缓存策略优化
- 异步处理优化
- 连接池配置

**前端优化**:
- 代码分割
- 资源压缩
- CDN加速
- 缓存策略

### 7.2 数据库性能优化

**MySQL优化**:
```sql
-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 分析查询性能
EXPLAIN SELECT * FROM users WHERE email = 'user@example.com';

-- 优化索引
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_order_status_date ON orders(status, created_at);
```

**Redis优化**:
```bash
# 内存使用分析
redis-cli info memory

# 键空间分析
redis-cli --bigkeys

# 慢查询分析
redis-cli slowlog get 10
```

### 7.3 系统性能优化

**操作系统优化**:
```bash
# 调整文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 调整内核参数
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" >> /etc/sysctl.conf
sysctl -p
```

**Docker优化**:
```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## 8. 备份与恢复

### 8.1 备份策略

**备份类型**:
- **全量备份**: 每周一次，包含完整数据
- **增量备份**: 每日一次，包含变更数据
- **实时备份**: 关键数据实时同步

**备份内容**:
- 数据库数据
- 应用代码
- 配置文件
- 用户上传文件
- 日志文件

### 8.2 备份存储

**存储策略**:
- 本地存储: 7天
- 远程存储: 30天
- 归档存储: 1年

**存储位置**:
- 本地磁盘: `/opt/backups/`
- 阿里云OSS: `agri-platform-backup`
- 异地机房: 冷备份

### 8.3 恢复流程

**数据库恢复**:
```bash
# 停止应用服务
docker-compose down

# 恢复数据库
mysql -h localhost -P 3307 -u root -p agri_platform < backup_20240123.sql

# 启动应用服务
docker-compose up -d

# 验证数据完整性
./scripts/health-check/health-check.sh
```

**应用恢复**:
```bash
# 回滚到指定版本
./scripts/deploy/deploy.sh --rollback deploy_20240123_143052

# 或者从备份恢复
cd /opt/agri-platform
git reset --hard backup_commit_hash
docker-compose up -d --build
```

### 8.4 恢复测试

**定期测试**:
- 每月进行恢复演练
- 验证备份文件完整性
- 测试恢复时间
- 记录恢复过程

## 9. 日常维护

### 9.1 日常检查清单

**每日检查**:
- [ ] 系统资源使用情况
- [ ] 应用服务状态
- [ ] 错误日志检查
- [ ] 备份任务执行状态
- [ ] 监控告警处理

**每周检查**:
- [ ] 磁盘空间清理
- [ ] 数据库性能分析
- [ ] 安全日志审计
- [ ] 备份恢复测试
- [ ] 系统更新检查

**每月检查**:
- [ ] 系统安全扫描
- [ ] 性能基线更新
- [ ] 容量规划评估
- [ ] 文档更新维护
- [ ] 应急预案演练

### 9.2 维护脚本

**系统巡检脚本**:
```bash
#!/bin/bash
# 系统巡检脚本

echo "=== 系统巡检报告 $(date) ==="

# 检查系统负载
echo "系统负载:"
uptime

# 检查磁盘使用
echo "磁盘使用:"
df -h

# 检查内存使用
echo "内存使用:"
free -h

# 检查服务状态
echo "服务状态:"
docker-compose ps

# 检查最近错误
echo "最近错误:"
tail -20 /var/log/syslog | grep -i error
```

**性能监控脚本**:
```bash
#!/bin/bash
# 性能监控脚本

# 收集性能数据
iostat -x 1 5 > /tmp/iostat.log
vmstat 1 5 > /tmp/vmstat.log
netstat -i > /tmp/netstat.log

# 分析并报告
python3 /opt/scripts/performance_analyzer.py
```

### 9.3 维护窗口

**维护时间**:
- 日常维护: 每日 02:00-04:00
- 周维护: 每周日 01:00-05:00
- 月维护: 每月第一个周日 00:00-06:00

**维护内容**:
- 系统更新
- 数据库维护
- 日志清理
- 备份验证
- 性能优化

## 10. 应急预案

### 10.1 服务中断应急预案

**触发条件**:
- 服务完全不可访问
- 响应时间超过30秒
- 错误率超过50%

**应急步骤**:
1. **立即响应** (5分钟内)
   - 确认故障范围
   - 启动应急小组
   - 发布故障通知

2. **快速恢复** (30分钟内)
   - 切换到备用服务
   - 回滚到稳定版本
   - 启用降级模式

3. **根因分析** (2小时内)
   - 分析故障原因
   - 制定修复方案
   - 实施永久修复

4. **服务恢复** (4小时内)
   - 验证修复效果
   - 逐步恢复服务
   - 监控服务状态

### 10.2 数据丢失应急预案

**触发条件**:
- 数据库损坏
- 重要数据误删
- 存储设备故障

**应急步骤**:
1. **立即隔离** (10分钟内)
   - 停止相关服务
   - 保护现场数据
   - 评估损失范围

2. **数据恢复** (1小时内)
   - 从最近备份恢复
   - 验证数据完整性
   - 补充增量数据

3. **服务恢复** (2小时内)
   - 重启应用服务
   - 验证功能正常
   - 通知用户恢复

### 10.3 安全事件应急预案

**触发条件**:
- 检测到入侵行为
- 发现数据泄露
- 系统被恶意攻击

**应急步骤**:
1. **立即隔离** (5分钟内)
   - 断开网络连接
   - 保护证据现场
   - 启动安全小组

2. **威胁评估** (30分钟内)
   - 分析攻击方式
   - 评估影响范围
   - 制定应对策略

3. **系统加固** (2小时内)
   - 修复安全漏洞
   - 更新安全策略
   - 加强监控措施

4. **恢复服务** (4小时内)
   - 验证系统安全
   - 逐步恢复服务
   - 持续安全监控

### 10.4 联系方式

**应急联系人**:
- 技术负责人: 张三 (13800138001)
- 运维负责人: 李四 (13800138002)
- 安全负责人: 王五 (13800138003)
- 产品负责人: 赵六 (13800138004)

**外部支持**:
- 阿里云技术支持: 95187
- 网络服务商: 10000
- 硬件供应商: 400-xxx-xxxx

## 附录

### A. 常用命令

**Docker相关**:
```bash
# 查看容器状态
docker ps -a

# 查看容器日志
docker logs -f container_name

# 进入容器
docker exec -it container_name bash

# 重启容器
docker restart container_name

# 清理无用镜像
docker image prune -f
```

**系统监控**:
```bash
# 查看系统负载
top
htop

# 查看磁盘使用
df -h
du -sh /path/to/directory

# 查看网络连接
netstat -tlnp
ss -tlnp

# 查看进程
ps aux | grep process_name
```

**日志查看**:
```bash
# 查看系统日志
journalctl -f
tail -f /var/log/syslog

# 查看应用日志
tail -f /opt/agri-platform/backend/logs/app.log

# 搜索日志
grep "ERROR" /var/log/syslog
```

### B. 配置文件模板

**环境变量模板** (`.env`):
```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://agri_user:agri_pass@mysql:3306/agri_platform
REDIS_URL=redis://redis:6379/0

# 应用配置
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# 外部服务
OSS_ACCESS_KEY_ID=your-oss-access-key
OSS_ACCESS_KEY_SECRET=your-oss-secret-key
OSS_BUCKET=agri-platform-files

# 通知配置
WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=noreply@example.com
EMAIL_PASSWORD=email-password
```

**Nginx配置模板**:
```nginx
server {
    listen 80;
    server_name agri-platform.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name agri-platform.com;

    ssl_certificate /etc/ssl/certs/agri-platform.crt;
    ssl_certificate_key /etc/ssl/private/agri-platform.key;

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### C. 故障排查检查表

**服务无法启动**:
- [ ] 检查端口是否被占用
- [ ] 检查配置文件语法
- [ ] 检查环境变量设置
- [ ] 检查磁盘空间
- [ ] 检查文件权限
- [ ] 查看错误日志

**性能问题**:
- [ ] 检查CPU使用率
- [ ] 检查内存使用率
- [ ] 检查磁盘I/O
- [ ] 检查网络延迟
- [ ] 分析慢查询
- [ ] 检查缓存命中率

**数据库问题**:
- [ ] 检查数据库服务状态
- [ ] 测试数据库连接
- [ ] 检查数据库日志
- [ ] 分析慢查询日志
- [ ] 检查表锁情况
- [ ] 验证数据完整性

---

**文档版本**: v1.0.0
**最后更新**: 2024年1月23日
**维护人员**: AI赋能云平台运维团队