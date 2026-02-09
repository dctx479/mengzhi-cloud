#!/bin/bash

# =============================================================================
# 日志清理脚本 (Linux版本)
# 功能：清理过期日志、压缩归档
# 作者：AI赋能云平台运维团队
# 版本：1.0.0
# =============================================================================

set -euo pipefail

# 配置文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/cleanup-config.conf"

# 默认配置
LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-30}"
ARCHIVE_RETENTION_DAYS="${ARCHIVE_RETENTION_DAYS:-90}"
COMPRESS_LOGS="${COMPRESS_LOGS:-true}"
DELETE_EMPTY_DIRS="${DELETE_EMPTY_DIRS:-true}"

# 日志路径配置
LOG_PATHS="${LOG_PATHS:-/var/log /opt/agri-platform/backend/logs /opt/agri-platform/logs}"
SYSTEM_LOG_PATHS="${SYSTEM_LOG_PATHS:-/var/log/syslog /var/log/messages /var/log/auth.log}"
APPLICATION_LOG_PATHS="${APPLICATION_LOG_PATHS:-/opt/agri-platform/backend/logs /opt/agri-platform/logs}"

# 排除配置
EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS:-*.pid *.lock current active}"
EXCLUDE_EXTENSIONS="${EXCLUDE_EXTENSIONS:-pid lock tmp}"

# 压缩配置
COMPRESSION_TYPE="${COMPRESSION_TYPE:-gzip}"
COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"

# 通知配置
NOTIFICATION_ENABLED="${NOTIFICATION_ENABLED:-false}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
EMAIL_ENABLED="${EMAIL_ENABLED:-false}"
EMAIL_TO="${EMAIL_TO:-}"

# 日志配置
CLEANUP_LOG_DIR="${CLEANUP_LOG_DIR:-/var/log/cleanup}"
CLEANUP_LOG_FILE="${CLEANUP_LOG_DIR}/cleanup.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 统计变量
TOTAL_FILES_PROCESSED=0
TOTAL_FILES_DELETED=0
TOTAL_FILES_COMPRESSED=0
TOTAL_SIZE_FREED=0
TOTAL_SIZE_COMPRESSED=0

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
            echo -e "${GREEN}[INFO]${NC} ${timestamp} - $message" | tee -a "$CLEANUP_LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" | tee -a "$CLEANUP_LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$CLEANUP_LOG_FILE"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$CLEANUP_LOG_FILE"
            ;;
    esac
}

# 错误处理
error_exit() {
    log "ERROR" "$1"
    send_notification "FAILED" "$1"
    exit 1
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
    mkdir -p "$CLEANUP_LOG_DIR"
    chmod 750 "$CLEANUP_LOG_DIR"
}

# 检查权限
check_permissions() {
    log "INFO" "检查权限..."

    for path in $LOG_PATHS; do
        if [[ -d "$path" ]]; then
            if [[ ! -r "$path" ]]; then
                log "WARN" "无读取权限: $path"
            fi
            if [[ ! -w "$path" ]]; then
                log "WARN" "无写入权限: $path"
            fi
        fi
    done

    log "INFO" "权限检查完成"
}

# 人性化文件大小
human_readable_size() {
    local size=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0

    while [[ $size -gt 1024 && $unit -lt 4 ]]; do
        size=$((size / 1024))
        ((unit++))
    done

    echo "${size}${units[$unit]}"
}

# =============================================================================
# 日志清理函数
# =============================================================================

# 检查文件是否应该被排除
should_exclude_file() {
    local file_path=$1
    local filename=$(basename "$file_path")
    local extension="${filename##*.}"

    # 检查排除模式
    for pattern in $EXCLUDE_PATTERNS; do
        if [[ "$filename" == $pattern ]]; then
            return 0
        fi
    done

    # 检查排除扩展名
    for ext in $EXCLUDE_EXTENSIONS; do
        if [[ "$extension" == "$ext" ]]; then
            return 0
        fi
    done

    return 1
}

# 清理过期日志文件
cleanup_expired_logs() {
    local log_path=$1
    local retention_days=$2
    local action=$3  # delete 或 compress

    log "INFO" "清理 $log_path 中 $retention_days 天前的日志文件 (动作: $action)..."

    if [[ ! -d "$log_path" ]]; then
        log "WARN" "日志路径不存在: $log_path"
        return
    fi

    local files_found=0
    local files_processed=0

    # 查找过期文件
    while IFS= read -r -d '' file; do
        ((files_found++))
        ((TOTAL_FILES_PROCESSED++))

        # 检查是否应该排除
        if should_exclude_file "$file"; then
            log "DEBUG" "跳过排除文件: $file"
            continue
        fi

        local file_size=$(stat -c%s "$file" 2>/dev/null || echo "0")

        case $action in
            "delete")
                log "DEBUG" "删除文件: $file ($(human_readable_size $file_size))"
                if rm -f "$file"; then
                    ((files_processed++))
                    ((TOTAL_FILES_DELETED++))
                    TOTAL_SIZE_FREED=$((TOTAL_SIZE_FREED + file_size))
                else
                    log "WARN" "删除失败: $file"
                fi
                ;;
            "compress")
                if [[ "$file" != *.gz && "$file" != *.bz2 && "$file" != *.xz ]]; then
                    log "DEBUG" "压缩文件: $file ($(human_readable_size $file_size))"
                    if compress_file "$file"; then
                        ((files_processed++))
                        ((TOTAL_FILES_COMPRESSED++))
                        local compressed_size=$(stat -c%s "${file}.gz" 2>/dev/null || echo "$file_size")
                        TOTAL_SIZE_COMPRESSED=$((TOTAL_SIZE_COMPRESSED + file_size - compressed_size))
                    else
                        log "WARN" "压缩失败: $file"
                    fi
                else
                    log "DEBUG" "文件已压缩，跳过: $file"
                fi
                ;;
        esac
    done < <(find "$log_path" -type f -mtime +$retention_days -print0 2>/dev/null)

    log "INFO" "路径 $log_path: 找到 $files_found 个文件，处理 $files_processed 个"
}

# 压缩文件
compress_file() {
    local file_path=$1

    case $COMPRESSION_TYPE in
        "gzip")
            gzip -$COMPRESSION_LEVEL "$file_path"
            ;;
        "bzip2")
            bzip2 -$COMPRESSION_LEVEL "$file_path"
            ;;
        "xz")
            xz -$COMPRESSION_LEVEL "$file_path"
            ;;
        *)
            log "ERROR" "不支持的压缩类型: $COMPRESSION_TYPE"
            return 1
            ;;
    esac
}

# 清理应用日志
cleanup_application_logs() {
    log "INFO" "清理应用日志..."

    for log_path in $APPLICATION_LOG_PATHS; do
        if [[ -d "$log_path" ]]; then
            # 压缩7天前的日志
            if [[ "$COMPRESS_LOGS" == "true" ]]; then
                cleanup_expired_logs "$log_path" 7 "compress"
            fi

            # 删除超过保留期的日志
            cleanup_expired_logs "$log_path" $LOG_RETENTION_DAYS "delete"
        fi
    done
}

# 清理系统日志
cleanup_system_logs() {
    log "INFO" "清理系统日志..."

    # 使用logrotate清理系统日志
    if command -v logrotate &> /dev/null; then
        log "INFO" "运行logrotate..."
        logrotate -f /etc/logrotate.conf 2>/dev/null || log "WARN" "logrotate执行失败"
    fi

    # 手动清理特定系统日志
    for log_file in $SYSTEM_LOG_PATHS; do
        if [[ -f "$log_file" ]]; then
            local file_size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")

            # 如果文件大于100MB，截断到最后10000行
            if [[ $file_size -gt 104857600 ]]; then
                log "INFO" "截断大文件: $log_file ($(human_readable_size $file_size))"
                tail -10000 "$log_file" > "${log_file}.tmp" && mv "${log_file}.tmp" "$log_file"
                local new_size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")
                TOTAL_SIZE_FREED=$((TOTAL_SIZE_FREED + file_size - new_size))
            fi
        fi
    done
}

# 清理Docker日志
cleanup_docker_logs() {
    log "INFO" "清理Docker日志..."

    if ! command -v docker &> /dev/null; then
        log "WARN" "Docker未安装，跳过Docker日志清理"
        return
    fi

    # 清理Docker容器日志
    local containers=$(docker ps -aq 2>/dev/null || echo "")
    for container in $containers; do
        local log_file="/var/lib/docker/containers/${container}/${container}-json.log"
        if [[ -f "$log_file" ]]; then
            local file_size=$(stat -c%s "$log_file" 2>/dev/null || echo "0")

            # 如果日志文件大于50MB，截断
            if [[ $file_size -gt 52428800 ]]; then
                log "INFO" "截断Docker容器日志: $container"
                echo "" > "$log_file"
                TOTAL_SIZE_FREED=$((TOTAL_SIZE_FREED + file_size))
            fi
        fi
    done

    # 清理Docker系统
    log "INFO" "清理Docker系统..."
    docker system prune -f --volumes &>/dev/null || log "WARN" "Docker系统清理失败"
}

# 清理Nginx日志
cleanup_nginx_logs() {
    log "INFO" "清理Nginx日志..."

    local nginx_log_paths=(
        "/var/log/nginx"
        "/etc/nginx/logs"
        "/usr/local/nginx/logs"
    )

    for nginx_path in "${nginx_log_paths[@]}"; do
        if [[ -d "$nginx_path" ]]; then
            # 压缩7天前的访问日志
            if [[ "$COMPRESS_LOGS" == "true" ]]; then
                cleanup_expired_logs "$nginx_path" 7 "compress"
            fi

            # 删除30天前的日志
            cleanup_expired_logs "$nginx_path" 30 "delete"

            # 重新加载Nginx配置以重新打开日志文件
            if command -v nginx &> /dev/null; then
                nginx -s reopen 2>/dev/null || log "WARN" "Nginx日志重新打开失败"
            fi
        fi
    done
}

# 清理数据库日志
cleanup_database_logs() {
    log "INFO" "清理数据库日志..."

    # MySQL日志清理
    local mysql_log_paths=(
        "/var/log/mysql"
        "/var/lib/mysql"
    )

    for mysql_path in "${mysql_log_paths[@]}"; do
        if [[ -d "$mysql_path" ]]; then
            # 清理MySQL错误日志
            find "$mysql_path" -name "*.err" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true

            # 清理MySQL慢查询日志
            find "$mysql_path" -name "*slow*" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true

            # 清理MySQL二进制日志（谨慎操作）
            if [[ -f "$mysql_path/mysql-bin.index" ]]; then
                log "INFO" "清理MySQL二进制日志..."
                # 这里应该使用MySQL的PURGE BINARY LOGS命令，而不是直接删除文件
                # mysql -e "PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL $LOG_RETENTION_DAYS DAY);" 2>/dev/null || true
            fi
        fi
    done
}

# 清理空目录
cleanup_empty_directories() {
    if [[ "$DELETE_EMPTY_DIRS" != "true" ]]; then
        return
    fi

    log "INFO" "清理空目录..."

    for log_path in $LOG_PATHS; do
        if [[ -d "$log_path" ]]; then
            # 查找并删除空目录（但保留根目录）
            find "$log_path" -type d -empty -not -path "$log_path" -delete 2>/dev/null || true
        fi
    done
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

    # 构建统计信息
    local stats="处理文件: $TOTAL_FILES_PROCESSED, 删除: $TOTAL_FILES_DELETED, 压缩: $TOTAL_FILES_COMPRESSED"
    stats="$stats, 释放空间: $(human_readable_size $TOTAL_SIZE_FREED)"
    stats="$stats, 压缩节省: $(human_readable_size $TOTAL_SIZE_COMPRESSED)"

    # Webhook通知
    if [[ -n "$WEBHOOK_URL" ]]; then
        local payload=$(cat <<EOF
{
    "msgtype": "text",
    "text": {
        "content": "日志清理通知\\n状态: $status\\n时间: $timestamp\\n主机: $hostname\\n统计: $stats\\n消息: $message"
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
        local subject="日志清理通知 - $status"
        local body="时间: $timestamp\\n主机: $hostname\\n状态: $status\\n统计: $stats\\n消息: $message"

        echo -e "$body" | mail -s "$subject" "$EMAIL_TO" &>/dev/null || true
    fi
}

# =============================================================================
# 主函数
# =============================================================================

# 显示帮助信息
show_help() {
    cat <<EOF
日志清理脚本

用法: $0 [选项]

选项:
    -h, --help              显示帮助信息
    -c, --config FILE       指定配置文件路径
    -r, --retention DAYS    指定日志保留天数
    -p, --path PATH         指定要清理的路径
    --no-compress           不压缩日志文件
    --no-system             不清理系统日志
    --no-docker             不清理Docker日志
    --no-nginx              不清理Nginx日志
    --no-database           不清理数据库日志
    --dry-run               模拟运行，不执行实际操作

清理范围:
    - 应用日志文件
    - 系统日志文件
    - Docker容器日志
    - Nginx访问日志
    - 数据库日志文件
    - 空目录清理

示例:
    $0                              # 标准清理
    $0 -r 15                        # 保留15天的日志
    $0 -p /var/log/myapp           # 清理指定路径
    $0 --no-compress               # 不压缩，直接删除
    $0 --dry-run                   # 模拟运行

配置文件示例:
    LOG_RETENTION_DAYS=30
    COMPRESS_LOGS=true
    LOG_PATHS="/var/log /opt/app/logs"
    EXCLUDE_PATTERNS="*.pid *.lock"
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
            -r|--retention)
                LOG_RETENTION_DAYS="$2"
                shift 2
                ;;
            -p|--path)
                LOG_PATHS="$LOG_PATHS $2"
                shift 2
                ;;
            --no-compress)
                COMPRESS_LOGS="false"
                shift
                ;;
            --no-system)
                SKIP_SYSTEM="true"
                shift
                ;;
            --no-docker)
                SKIP_DOCKER="true"
                shift
                ;;
            --no-nginx)
                SKIP_NGINX="true"
                shift
                ;;
            --no-database)
                SKIP_DATABASE="true"
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
    log "INFO" "日志清理开始"
    log "INFO" "=========================================="

    # 解析参数
    parse_args "$@"

    # 加载配置
    load_config

    # 创建目录
    create_directories

    # 检查权限
    check_permissions

    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "模拟运行模式，不执行实际操作"
        log "INFO" "配置信息:"
        log "INFO" "  日志保留天数: $LOG_RETENTION_DAYS"
        log "INFO" "  压缩日志: $COMPRESS_LOGS"
        log "INFO" "  清理路径: $LOG_PATHS"
        log "INFO" "  排除模式: $EXCLUDE_PATTERNS"
        return 0
    fi

    # 执行清理任务
    cleanup_application_logs

    if [[ "${SKIP_SYSTEM:-false}" != "true" ]]; then
        cleanup_system_logs
    fi

    if [[ "${SKIP_DOCKER:-false}" != "true" ]]; then
        cleanup_docker_logs
    fi

    if [[ "${SKIP_NGINX:-false}" != "true" ]]; then
        cleanup_nginx_logs
    fi

    if [[ "${SKIP_DATABASE:-false}" != "true" ]]; then
        cleanup_database_logs
    fi

    cleanup_empty_directories

    local end_time=$(date '+%s')
    local duration=$((end_time - start_time))

    log "INFO" "=========================================="
    log "INFO" "日志清理完成，耗时: ${duration}秒"
    log "INFO" "统计信息:"
    log "INFO" "  处理文件数: $TOTAL_FILES_PROCESSED"
    log "INFO" "  删除文件数: $TOTAL_FILES_DELETED"
    log "INFO" "  压缩文件数: $TOTAL_FILES_COMPRESSED"
    log "INFO" "  释放空间: $(human_readable_size $TOTAL_SIZE_FREED)"
    log "INFO" "  压缩节省: $(human_readable_size $TOTAL_SIZE_COMPRESSED)"
    log "INFO" "=========================================="

    send_notification "SUCCESS" "日志清理成功完成，耗时: ${duration}秒"
}

# 信号处理
trap 'log "INFO" "日志清理被中断"; exit 130' INT TERM

# 执行主函数
main "$@"