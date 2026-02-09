# 部署操作手册 (Deployment Runbook)

## 概述

本手册描述了AI平台的标准部署流程、回滚步骤、验证方法和故障处理。

---

## 前置检查清单

### 部署前必须确认

- [ ] 代码已通过CI/CD测试 (单元测试、集成测试)
- [ ] 已在测试环境验证功能
- [ ] 数据库迁移脚本已准备并测试
- [ ] 配置文件已更新 (.env, config.yml)
- [ ] 依赖服务状态正常 (数据库、Redis、外部API)
- [ ] 备份已完成 (数据库、配置文件)
- [ ] 通知相关人员部署时间窗口
- [ ] 准备回滚方案

---

## 标准部署流程

### Step 1: 备份当前状态

```bash
# 1. 备份数据库
docker exec postgres pg_dump -U ai_platform -Fc ai_platform > backup_$(date +%Y%m%d_%H%M%S).dump

# 2. 备份配置文件
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
cp docker-compose.yml docker-compose.yml.backup

# 3. 记录当前镜像版本
docker images | grep backend > images_before.txt
```

### Step 2: 拉取最新代码

```bash
# 拉取代码
git pull origin main

# 或者切换到特定版本
git checkout v1.2.0
```

### Step 3: 构建新镜像

```bash
# 构建镜像
docker-compose build backend

# 打标签
docker tag ai-platform-backend:latest ai-platform-backend:v1.2.0

# (可选) 推送到镜像仓库
docker push ai-platform-backend:v1.2.0
```

### Step 4: 数据库迁移

```bash
# 检查迁移脚本
docker-compose run --rm backend alembic history
docker-compose run --rm backend alembic current

# 执行迁移 (先在测试环境验证!)
docker-compose run --rm backend alembic upgrade head

# 验证迁移成功
docker exec postgres psql -U ai_platform -c "\dt"  # 查看表结构
```

### Step 5: 滚动更新服务

**方式1: 零停机部署 (推荐)**

```bash
# 启动新容器,保持旧容器运行
docker-compose up -d --no-deps --scale backend=2 backend

# 等待新容器健康检查通过
sleep 30
curl -f http://localhost:8001/health  # 假设新容器端口8001

# 健康检查通过后,停止旧容器
docker stop backend_old

# 验证服务正常
curl -f http://localhost:8000/health
```

**方式2: 快速重启**

```bash
# 停止服务
docker-compose stop backend

# 启动新版本
docker-compose up -d backend

# 等待服务就绪
sleep 10
```

### Step 6: 验证部署

```bash
# 1. 健康检查
curl -f http://localhost:8000/health
curl -f http://localhost:8000/ready

# 2. 查看版本信息
curl http://localhost:8000/api/v1/version

# 3. 查看容器日志
docker-compose logs -f --tail=100 backend

# 4. 查看容器状态
docker ps | grep backend

# 5. 执行冒烟测试
./scripts/smoke-test.sh
```

### Step 7: 监控观察

```bash
# 查看 Grafana 大盘
# - Service Availability: 应该为 100%
# - Error Rate: 应该为 0% 或低于阈值
# - Response Time: P95 < 500ms
# - Container Restarts: 应该为 0

# 查看 Prometheus 告警
# - 确保没有新的告警触发

# 查看应用日志
docker-compose logs -f backend | grep -i "error\|exception"
```

---

## 回滚流程

### 快速回滚 (推荐)

```bash
# 1. 停止当前版本
docker-compose stop backend

# 2. 恢复旧镜像
docker tag ai-platform-backend:v1.1.0 ai-platform-backend:latest

# 3. 启动服务
docker-compose up -d backend

# 4. 验证回滚成功
curl -f http://localhost:8000/health
```

### 完全回滚 (包括数据库)

```bash
# 1. 回滚数据库
docker exec postgres pg_restore -U ai_platform -d ai_platform -c backup_20260124_140000.dump

# 2. 恢复配置文件
cp .env.backup_20260124_140000 .env

# 3. 回滚镜像
docker-compose down
git checkout v1.1.0
docker-compose build backend
docker-compose up -d

# 4. 验证回滚
curl -f http://localhost:8000/health
```

---

## 常见部署问题

### 问题1: 数据库迁移失败

**现象**: `alembic upgrade head` 报错

**处理**:
```bash
# 查看当前版本
docker-compose run --rm backend alembic current

# 回滚到上一个版本
docker-compose run --rm backend alembic downgrade -1

# 修复迁移脚本后重新执行
docker-compose run --rm backend alembic upgrade head
```

### 问题2: 健康检查失败

**现象**: `/health` 端点返回 503

**处理**:
```bash
# 查看日志
docker-compose logs backend | tail -50

# 检查依赖服务
docker-compose ps
curl http://localhost:5432  # PostgreSQL
curl http://localhost:6379  # Redis

# 重启服务
docker-compose restart backend
```

### 问题3: 配置文件错误

**现象**: 服务启动失败,日志显示配置错误

**处理**:
```bash
# 恢复配置文件
cp .env.backup_20260124_140000 .env

# 重启服务
docker-compose restart backend
```

---

## 部署最佳实践

### 1. 使用蓝绿部署

```yaml
# docker-compose.yml
services:
  backend-blue:
    image: ai-platform-backend:v1.1.0
    ports:
      - "8000:8000"

  backend-green:
    image: ai-platform-backend:v1.2.0
    ports:
      - "8001:8000"

  nginx:
    # 切换upstream指向blue或green
```

### 2. 金丝雀发布

```bash
# 部署新版本到10%流量
docker-compose up -d --scale backend-v1=9 --scale backend-v2=1

# 观察指标,逐步增加比例
docker-compose up -d --scale backend-v1=5 --scale backend-v2=5

# 全部切换
docker-compose up -d --scale backend-v1=0 --scale backend-v2=10
```

### 3. 自动化部署脚本

```bash
#!/bin/bash
# scripts/deploy.sh

set -e  # 遇到错误立即退出

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <version>"
    exit 1
fi

echo "开始部署版本: $VERSION"

# 1. 备份
./scripts/backup.sh

# 2. 拉取代码
git fetch origin
git checkout $VERSION

# 3. 构建镜像
docker-compose build backend

# 4. 数据库迁移
docker-compose run --rm backend alembic upgrade head

# 5. 滚动更新
docker-compose up -d --no-deps backend

# 6. 等待服务就绪
echo "等待服务就绪..."
sleep 30

# 7. 健康检查
if curl -f http://localhost:8000/health; then
    echo "✅ 部署成功!"
else
    echo "❌ 健康检查失败,开始回滚..."
    ./scripts/rollback.sh
    exit 1
fi

# 8. 冒烟测试
./scripts/smoke-test.sh

echo "🎉 部署完成!"
```

---

## 相关文档

- [回滚操作手册](./rollback.md)
- [备份恢复手册](./backup-restore.md)
- [服务不可用排查](../troubleshooting/service-down.md)

---

## 部署检查清单

### 部署前
- [ ] 备份数据库
- [ ] 备份配置文件
- [ ] 测试环境验证
- [ ] 通知相关人员

### 部署中
- [ ] 构建新镜像
- [ ] 执行数据库迁移
- [ ] 滚动更新服务
- [ ] 健康检查通过

### 部署后
- [ ] 冒烟测试
- [ ] 监控指标正常
- [ ] 无新告警
- [ ] 用户反馈正常

### 如果失败
- [ ] 立即回滚
- [ ] 分析根因
- [ ] 记录故障报告
- [ ] 优化部署流程
