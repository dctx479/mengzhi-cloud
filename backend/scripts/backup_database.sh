#!/bin/bash
# 数据库备份脚本
# 版本: 1.0

set -e

# 配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-root}"
DB_PASS="${DB_PASS:-root123}"
DB_NAME="${DB_NAME:-agri_platform}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 生成备份文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"

echo "🔄 开始备份数据库: $DB_NAME"
echo "📁 备份文件: $BACKUP_FILE"

# 执行备份
mysqldump -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASS" \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  "$DB_NAME" > "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "✅ 备份完成: $BACKUP_FILE"
echo "📊 文件大小: $(du -h "$BACKUP_FILE" | cut -f1)"

# 清理旧备份
echo "🧹 清理 $RETENTION_DAYS 天前的备份..."
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ 备份任务完成"
