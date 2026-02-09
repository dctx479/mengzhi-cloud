#!/bin/bash

# =============================================================================
# 数据库自动备份脚本 (Linux版本)
# 功能：MySQL数据库自动备份、上传到OSS、清理旧备份
# 作者：AI赋能云平台运维团队
# 版本：1.0.0
# =============================================================================

set -euo pipefail

# 配置文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/backup-config.conf"

# 默认配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3307}"
DB_USER="${DB_USER:-agri_user}"
DB_PASSWORD="${DB_PASSWORD:-agri_pass}"
DB_NAME="${DB_NAME:-agri_platform}"

# 备份配置
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/mysql}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
COMPRESS_BACKUP="${COMPRESS_BACKUP:-true}"

# OSS配置
OSS_ENABLED="${OSS_ENABLED:-false}"
OSS_ENDPOINT="${OSS_ENDPOINT:-}"
OSS_ACCESS_KEY_ID="${OSS_ACCESS_KEY_ID:-}"
OSS_ACCESS_KEY_SECRET="${OSS_ACCESS_KEY_SECRET:-}"
OSS_BUCKET="${OSS_BUCKET:-}"
OSS_PATH="${OSS_PATH:-mysql-backups}"

# 通知配置
NOTIFICATION_ENABLED="${NOTIFICATION_ENABLED:-false}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
EMAIL_ENABLED="${EMAIL_ENABLED:-false}"
EMAIL_TO="${EMAIL_TO:-}"

# 日志配置
LOG_DIR="${LOG_DIR:-/var/log/backup}"
LOG_FILE="${LOG_DIR}/mysql-backup.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# 工具函数
# =============================================================================

# 日志函数
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# 错误处理
error_exit() {
    log "ERROR" "$1"
    send_notification "FAILED" "$1"
    exit 1
}

# 检查依赖
check_dependencies() {
    log "INFO" "检查依赖工具..."

    local deps=("mysqldump" "mysql")

    if [[ "$COMPRESS_BACKUP" == "true" ]]; then
        deps+=("gzip")
    fi

    if [[ "$OSS_ENABLED" == "true" ]]; then
        deps+=("ossutil")
    fi

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error_exit "依赖工具 $dep 未安装"
        fi
    done

    log "INFO" "依赖检查完成"
}

# 加载配置文件
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log "INFO" "加载配置文件: $CONFIG_FILE"
        source "$CONFIG_FILE"
    else
        log "WARN" "配置文件不存在，使用默认配置"
    fi
}

# 创建必要目录
create_directories() {
    log "INFO" "创建备份目录..."

    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"

    # 设置权限
    chmod 750 "$BACKUP_DIR"
    chmod 750 "$LOG_DIR"

    log "INFO" "目录创建完成"
}

# 测试数据库连接
test_db_connection() {
    log "INFO" "测试数据库连接..."

    if ! mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
        error_exit "数据库连接失败"
    fi

    log "INFO" "数据库连接正常"
}

# =============================================================================
# 备份函数
# =============================================================================

# 执行数据库备份
perform_backup() {
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_filename="${DB_NAME}_${timestamp}.sql"
    local backup_path="${BACKUP_DIR}/${backup_filename}"

    log "INFO" "开始备份数据库: $DB_NAME"
    log "INFO" "备份文件: $backup_path"

    # 执行备份
    if ! mysqldump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --user="$DB_USER" \
        --password="$DB_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --hex-blob \
        --opt \
        --comments \
        --dump-date \
        "$DB_NAME" > "$backup_path"; then
        error_exit "数据库备份失败"
    fi

    # 验证备份文件
    if [[ ! -f "$backup_path" ]] || [[ ! -s "$backup_path" ]]; then
        error_exit "备份文件创建失败或为空"
    fi

    local file_size=$(du -h "$backup_path" | cut -f1)
    log "INFO" "备份完成，文件大小: $file_size"

    # 压缩备份
    if [[ "$COMPRESS_BACKUP" == "true" ]]; then
        log "INFO" "压缩备份文件..."

        if ! gzip "$backup_path"; then
            error_exit "备份文件压缩失败"
        fi

        backup_path="${backup_path}.gz"
        backup_filename="${backup_filename}.gz"

        local compressed_size=$(du -h "$backup_path" | cut -f1)
        log "INFO" "压缩完成，压缩后大小: $compressed_size"
    fi

    echo "$backup_path"
}

# 上传到OSS
upload_to_oss() {
    local backup_path=$1
    local backup_filename=$(basename "$backup_path")

    if [[ "$OSS_ENABLED" != "true" ]]; then
        log "INFO" "OSS上传未启用，跳过"
        return 0
    fi

    log "INFO" "上传备份到OSS..."

    # 配置OSS
    ossutil config -e "$OSS_ENDPOINT" -i "$OSS_ACCESS_KEY_ID" -k "$OSS_ACCESS_KEY_SECRET"

    # 上传文件
    local oss_path="oss://${OSS_BUCKET}/${OSS_PATH}/${backup_filename}"

    if ! ossutil cp "$backup_path" "$oss_path"; then
        log "ERROR" "OSS上传失败"
        return 1
    fi

    log "INFO" "OSS上传完成: $oss_path"
    return 0
}

# 清理旧备份
cleanup_old_backups() {
    log "INFO" "清理 $BACKUP_RETENTION_DAYS 天前的备份文件..."

    local deleted_count=0

    # 清理本地备份
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted_count++))
        log "INFO" "删除本地备份: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql*" -type f -mtime +$BACKUP_RETENTION_DAYS -print0)

    # 清理OSS备份
    if [[ "$OSS_ENABLED" == "true" ]]; then
        log "INFO" "清理OSS旧备份..."

        # 获取OSS中的旧文件列表
        local cutoff_date=$(date -d "$BACKUP_RETENTION_DAYS days ago" '+%Y%m%d')

        ossutil ls "oss://${OSS_BUCKET}/${OSS_PATH}/" | grep "${DB_NAME}_" | while read -r line; do
            local file_path=$(echo "$line" | awk '{print $NF}')
            local file_date=$(basename "$file_path" | grep -o '[0-9]\{8\}' | head -1)

            if [[ "$file_date" < "$cutoff_date" ]]; then
                if ossutil rm "$file_path"; then
                    ((deleted_count++))
                    log "INFO" "删除OSS备份: $(basename "$file_path")"
                fi
            fi
        done
    fi

    log "INFO" "清理完成，共删除 $deleted_count 个备份文件"
}

# =============================================================================
# 通知函数
# =============================================================================

# 发送通知
send_notification() {
    local status=$1
    local message=$2

    if [[ "$NOTIFICATION_ENABLED" != "true" ]]; then
        return 0
    fi

    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local hostname=$(hostname)

    # Webhook通知
    if [[ -n "$WEBHOOK_URL" ]]; then
        local payload=$(cat <<EOF
{
    "msgtype": "text",
    "text": {
        "content": "数据库备份通知\\n状态: $status\\n时间: $timestamp\\n主机: $hostname\\n数据库: $DB_NAME\\n消息: $message"
    }
}
EOF
)

        curl -s -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "$payload" &>/dev/null || true
    fi

    # 邮件通知
    if [[ "$EMAIL_ENABLED" == "true" ]] && [[ -n "$EMAIL_TO" ]]; then
        local subject="数据库备份通知 - $status"
        local body="时间: $timestamp\\n主机: $hostname\\n数据库: $DB_NAME\\n状态: $status\\n消息: $message"

        echo -e "$body" | mail -s "$subject" "$EMAIL_TO" &>/dev/null || true
    fi
}

# =============================================================================
# 主函数
# =============================================================================

# 显示帮助信息
show_help() {
    cat <<EOF
数据库自动备份脚本

用法: $0 [选项]

选项:
    -h, --help          显示帮助信息
    -c, --config FILE   指定配置文件路径
    -d, --database DB   指定数据库名称
    -o, --output DIR    指定备份输出目录
    -r, --retention N   指定备份保留天数
    --no-compress       不压缩备份文件
    --no-oss           不上传到OSS
    --dry-run          模拟运行，不执行实际操作

示例:
    $0                                  # 使用默认配置
    $0 -c /etc/backup.conf             # 使用指定配置文件
    $0 -d mydb -o /tmp/backup          # 指定数据库和输出目录
    $0 --dry-run                       # 模拟运行

配置文件示例:
    DB_HOST=localhost
    DB_PORT=3307
    DB_USER=backup_user
    DB_PASSWORD=backup_pass
    DB_NAME=agri_platform
    BACKUP_DIR=/opt/backups/mysql
    BACKUP_RETENTION_DAYS=7
    OSS_ENABLED=true
    OSS_BUCKET=my-backup-bucket
EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -d|--database)
                DB_NAME="$2"
                shift 2
                ;;
            -o|--output)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -r|--retention)
                BACKUP_RETENTION_DAYS="$2"
                shift 2
                ;;
            --no-compress)
                COMPRESS_BACKUP="false"
                shift
                ;;
            --no-oss)
                OSS_ENABLED="false"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            *)
                log "ERROR" "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 主函数
main() {
    local start_time=$(date '+%s')

    log "INFO" "=========================================="
    log "INFO" "数据库备份开始"
    log "INFO" "=========================================="

    # 解析参数
    parse_args "$@"

    # 加载配置
    load_config

    # 检查依赖
    check_dependencies

    # 创建目录
    create_directories

    # 测试数据库连接
    test_db_connection

    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "模拟运行模式，不执行实际操作"
        log "INFO" "配置信息:"
        log "INFO" "  数据库: $DB_HOST:$DB_PORT/$DB_NAME"
        log "INFO" "  备份目录: $BACKUP_DIR"
        log "INFO" "  保留天数: $BACKUP_RETENTION_DAYS"
        log "INFO" "  压缩: $COMPRESS_BACKUP"
        log "INFO" "  OSS上传: $OSS_ENABLED"
        return 0
    fi

    # 执行备份
    local backup_path
    backup_path=$(perform_backup)

    # 上传到OSS
    upload_to_oss "$backup_path"

    # 清理旧备份
    cleanup_old_backups

    local end_time=$(date '+%s')
    local duration=$((end_time - start_time))

    log "INFO" "=========================================="
    log "INFO" "数据库备份完成，耗时: ${duration}秒"
    log "INFO" "=========================================="

    send_notification "SUCCESS" "数据库备份成功完成，耗时: ${duration}秒"
}

# 信号处理
trap 'error_exit "脚本被中断"' INT TERM

# 执行主函数
main "$@"