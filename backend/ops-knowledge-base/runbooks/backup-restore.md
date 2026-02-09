# 备份与恢复操作手册

## 概述

本手册描述了数据库备份、配置备份、灾难恢复的标准流程。

---

## 数据库备份

### 自动备份 (推荐)

```bash
# 配置 cron 定时备份
# 编辑 crontab
crontab -e

# 添加每日凌晨3点备份
0 3 * * * /opt/ai-platform/scripts/backup-db.sh

# backup-db.sh 脚本内容
#!/bin/bash
BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker exec postgres pg_dump -U ai_platform -Fc ai_platform > $BACKUP_DIR/db_$DATE.dump

# 压缩
gzip $BACKUP_DIR/db_$DATE.dump

# 保留最近7天的备份
find $BACKUP_DIR -name "db_*.dump.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.dump.gz"
```

### 手动备份

```bash
# 完整备份
docker exec postgres pg_dump -U ai_platform -Fc ai_platform > backup_$(date +%Y%m%d_%H%M%S).dump

# 仅备份数据 (不包含schema)
docker exec postgres pg_dump -U ai_platform -a -Fc ai_platform > backup_data_$(date +%Y%m%d_%H%M%S).dump

# 备份单个表
docker exec postgres pg_dump -U ai_platform -t posts -Fc ai_platform > backup_posts_$(date +%Y%m%d_%H%M%S).dump

# 备份到SQL文件 (可读)
docker exec postgres pg_dump -U ai_platform ai_platform > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 数据库恢复

### 完全恢复

```bash
# 1. 停止应用服务
docker-compose stop backend

# 2. 恢复数据库
docker exec postgres pg_restore -U ai_platform -d ai_platform -c backup_20260124_030000.dump

# 或从SQL文件恢复
docker exec -i postgres psql -U ai_platform ai_platform < backup_20260124_030000.sql

# 3. 重启服务
docker-compose start backend

# 4. 验证数据
docker exec postgres psql -U ai_platform -c "SELECT COUNT(*) FROM posts;"
```

### 部分恢复 (恢复单个表)

```bash
# 恢复单个表
docker exec postgres pg_restore -U ai_platform -d ai_platform -t posts backup_posts_20260124_030000.dump
```

---

## 配置文件备份

```bash
# 备份所有配置文件
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    .env \
    docker-compose.yml \
    prometheus/prometheus.yml \
    grafana/provisioning

# 恢复配置文件
tar -xzf config_backup_20260124_030000.tar.gz
```

---

## 灾难恢复

### 场景1: 数据库损坏

```bash
# 1. 停止所有服务
docker-compose down

# 2. 删除损坏的数据卷
docker volume rm ai-platform_postgres_data

# 3. 重新创建数据库
docker-compose up -d postgres

# 4. 等待数据库就绪
sleep 10

# 5. 恢复备份
docker exec postgres pg_restore -U ai_platform -d ai_platform -c backup_latest.dump

# 6. 启动应用
docker-compose up -d
```

### 场景2: 完全系统重建

```bash
# 1. 准备干净环境
docker-compose down -v
docker system prune -a

# 2. 恢复配置文件
tar -xzf config_backup_latest.tar.gz

# 3. 重新部署
docker-compose up -d postgres redis
sleep 10

# 4. 恢复数据库
docker exec postgres pg_restore -U ai_platform -d ai_platform backup_latest.dump

# 5. 启动应用
docker-compose up -d backend

# 6. 验证
curl -f http://localhost:8000/health
```

---

## 备份验证

```bash
# 定期验证备份可用性
./scripts/verify-backup.sh backup_20260124_030000.dump

# verify-backup.sh 脚本内容
#!/bin/bash
BACKUP_FILE=$1

# 创建测试数据库
docker exec postgres psql -U ai_platform -c "CREATE DATABASE test_restore;"

# 恢复到测试数据库
docker exec postgres pg_restore -U ai_platform -d test_restore $BACKUP_FILE

# 验证数据完整性
if docker exec postgres psql -U ai_platform -d test_restore -c "SELECT COUNT(*) FROM posts;" > /dev/null; then
    echo "✅ Backup is valid"
else
    echo "❌ Backup is corrupted"
fi

# 清理测试数据库
docker exec postgres psql -U ai_platform -c "DROP DATABASE test_restore;"
```

---

## 备份最佳实践

1. **3-2-1 原则**:
   - 3份副本
   - 2种存储介质
   - 1份异地备份

2. **定期测试**: 每月验证备份可恢复性

3. **加密存储**: 敏感数据加密后存储

4. **监控告警**: 备份失败时立即告警

---

## 相关文档

- [部署操作手册](./deployment.md)
- [回滚操作手册](./rollback.md)
