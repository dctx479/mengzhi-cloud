#!/bin/bash

# =============================================================================
# 系统健康检查脚本 (Linux版本)
# 功能：检查服务状态、数据库连接、Redis连接、磁盘空间等
# 作者：AI赋能云平台运维团队
# 版本：1.0.0
# =============================================================================

set -euo pipefail

# 配置文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/health-check-config.conf"

# 默认配置
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
MAX_RETRIES="${MAX_RETRIES:-3}"
TIMEOUT="${TIMEOUT:-10}"

# 服务配置
SERVICES_TO_CHECK="${SERVICES_TO_CHECK:-docker mysql redis nginx}"
DOCKER_CONTAINERS="${DOCKER_CONTAINERS:-agri-backend agri-frontend agri-mysql agri-redis}"

# 数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3307}"
DB_USER="${DB_USER:-agri_user}"
DB_PASSWORD="${DB_PASSWORD:-agri_pass}"
DB_NAME="${DB_NAME:-agri_platform}"

# Redis配置
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6380}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# 磁盘空间检查
DISK_USAGE_THRESHOLD="${DISK_USAGE_THRESHOLD:-80}"
DISK_PATHS_TO_CHECK="${DISK_PATHS_TO_CHECK:-/ /var /opt}"

# 内存使用检查
MEMORY_USAGE_THRESHOLD="${MEMORY_USAGE_THRESHOLD:-85}"

# CPU使用检查
CPU_USAGE_THRESHOLD="${CPU_USAGE_THRESHOLD:-90}"

# 网络检查
NETWORK_HOSTS_TO_CHECK="${NETWORK_HOSTS_TO_CHECK:-8.8.8.8 114.114.114.114}"
API_ENDPOINTS_TO_CHECK="${API_ENDPOINTS_TO_CHECK:-http://localhost:5000/health}"

# 日志配置
LOG_DIR="${LOG_DIR:-/var/log/health-check}"
LOG_FILE="${LOG_DIR}/health-check.log"
ALERT_LOG="${LOG_DIR}/alerts.log"

# 通知配置
NOTIFICATION_ENABLED="${NOTIFICATION_ENABLED:-false}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
EMAIL_ENABLED="${EMAIL_ENABLED:-false}"
EMAIL_TO="${EMAIL_TO:-}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 全局变量
HEALTH_STATUS="HEALTHY"
FAILED_CHECKS=()
WARNING_CHECKS=()

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
            echo "${timestamp} - WARN - $message" >> "$ALERT_LOG"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            echo "${timestamp} - ERROR - $message" >> "$ALERT_LOG"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# 设置健康状态
set_health_status() {
    local status=$1
    local check_name=$2
    local message=$3

    case $status in
        "FAILED")
            HEALTH_STATUS="UNHEALTHY"
            FAILED_CHECKS+=("$check_name: $message")
            log "ERROR" "$check_name 检查失败: $message"
            ;;
        "WARNING")
            if [[ "$HEALTH_STATUS" != "UNHEALTHY" ]]; then
                HEALTH_STATUS="WARNING"
            fi
            WARNING_CHECKS+=("$check_name: $message")
            log "WARN" "$check_name 检查警告: $message"
            ;;
        "PASSED")
            log "INFO" "$check_name 检查通过: $message"
            ;;
    esac
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
    mkdir -p "$LOG_DIR"
    chmod 750 "$LOG_DIR"
}

# =============================================================================
# 健康检查函数
# =============================================================================

# 检查系统服务
check_services() {
    log "INFO" "检查系统服务状态..."

    for service in $SERVICES_TO_CHECK; do
        if systemctl is-active --quiet "$service"; then
            set_health_status "PASSED" "Service-$service" "服务运行正常"
        else
            set_health_status "FAILED" "Service-$service" "服务未运行"
        fi
    done
}

# 检查Docker容器
check_docker_containers() {
    log "INFO" "检查Docker容器状态..."

    if ! command -v docker &> /dev/null; then
        set_health_status "WARNING" "Docker" "Docker未安装"
        return
    fi

    for container in $DOCKER_CONTAINERS; do
        if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
            # 检查容器健康状态
            health_status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")

            case $health_status in
                "healthy")
                    set_health_status "PASSED" "Container-$container" "容器健康"
                    ;;
                "unhealthy")
                    set_health_status "FAILED" "Container-$container" "容器不健康"
                    ;;
                "starting")
                    set_health_status "WARNING" "Container-$container" "容器启动中"
                    ;;
                *)
                    # 如果没有健康检查，检查容器是否运行
                    if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
                        set_health_status "PASSED" "Container-$container" "容器运行中"
                    else
                        set_health_status "FAILED" "Container-$container" "容器未运行"
                    fi
                    ;;
            esac
        else
            set_health_status "FAILED" "Container-$container" "容器未运行"
        fi
    done
}

# 检查数据库连接
check_database() {
    log "INFO" "检查数据库连接..."

    local retry_count=0
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        if timeout "$TIMEOUT" mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
            # 检查数据库性能
            local connections=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SHOW STATUS LIKE 'Threads_connected';" 2>/dev/null | awk 'NR==2 {print $2}')
            local max_connections=$(mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SHOW VARIABLES LIKE 'max_connections';" 2>/dev/null | awk 'NR==2 {print $2}')

            if [[ -n "$connections" && -n "$max_connections" ]]; then
                local usage_percent=$((connections * 100 / max_connections))
                if [[ $usage_percent -gt 80 ]]; then
                    set_health_status "WARNING" "Database" "连接数使用率过高: ${usage_percent}%"
                else
                    set_health_status "PASSED" "Database" "连接正常，使用率: ${usage_percent}%"
                fi
            else
                set_health_status "PASSED" "Database" "连接正常"
            fi
            return
        fi

        ((retry_count++))
        sleep 2
    done

    set_health_status "FAILED" "Database" "连接失败，重试 $MAX_RETRIES 次后仍无法连接"
}

# 检查Redis连接
check_redis() {
    log "INFO" "检查Redis连接..."

    local retry_count=0
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        local redis_cmd="redis-cli -h $REDIS_HOST -p $REDIS_PORT"

        if [[ -n "$REDIS_PASSWORD" ]]; then
            redis_cmd="$redis_cmd -a $REDIS_PASSWORD"
        fi

        if timeout "$TIMEOUT" $redis_cmd ping &>/dev/null; then
            # 检查Redis内存使用
            local memory_info=$($redis_cmd info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')

            if [[ -n "$memory_info" ]]; then
                set_health_status "PASSED" "Redis" "连接正常，内存使用: $memory_info"
            else
                set_health_status "PASSED" "Redis" "连接正常"
            fi
            return
        fi

        ((retry_count++))
        sleep 2
    done

    set_health_status "FAILED" "Redis" "连接失败，重试 $MAX_RETRIES 次后仍无法连接"
}

# 检查磁盘空间
check_disk_space() {
    log "INFO" "检查磁盘空间..."

    for path in $DISK_PATHS_TO_CHECK; do
        if [[ -d "$path" ]]; then
            local usage=$(df "$path" | awk 'NR==2 {print $5}' | sed 's/%//')

            if [[ $usage -gt $DISK_USAGE_THRESHOLD ]]; then
                set_health_status "FAILED" "Disk-$path" "磁盘使用率过高: ${usage}%"
            elif [[ $usage -gt $((DISK_USAGE_THRESHOLD - 10)) ]]; then
                set_health_status "WARNING" "Disk-$path" "磁盘使用率较高: ${usage}%"
            else
                set_health_status "PASSED" "Disk-$path" "磁盘使用率正常: ${usage}%"
            fi
        else
            set_health_status "WARNING" "Disk-$path" "路径不存在"
        fi
    done
}

# 检查内存使用
check_memory_usage() {
    log "INFO" "检查内存使用..."

    local memory_info=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')

    if [[ $memory_info -gt $MEMORY_USAGE_THRESHOLD ]]; then
        set_health_status "FAILED" "Memory" "内存使用率过高: ${memory_info}%"
    elif [[ $memory_info -gt $((MEMORY_USAGE_THRESHOLD - 10)) ]]; then
        set_health_status "WARNING" "Memory" "内存使用率较高: ${memory_info}%"
    else
        set_health_status "PASSED" "Memory" "内存使用率正常: ${memory_info}%"
    fi
}

# 检查CPU使用
check_cpu_usage() {
    log "INFO" "检查CPU使用..."

    # 获取1分钟内的平均CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')

    # 如果top命令格式不同，尝试其他方法
    if [[ -z "$cpu_usage" ]]; then
        cpu_usage=$(sar -u 1 1 | awk 'NR==4 {print 100-$8}' 2>/dev/null || echo "0")
    fi

    # 移除小数点
    cpu_usage=${cpu_usage%.*}

    if [[ $cpu_usage -gt $CPU_USAGE_THRESHOLD ]]; then
        set_health_status "FAILED" "CPU" "CPU使用率过高: ${cpu_usage}%"
    elif [[ $cpu_usage -gt $((CPU_USAGE_THRESHOLD - 10)) ]]; then
        set_health_status "WARNING" "CPU" "CPU使用率较高: ${cpu_usage}%"
    else
        set_health_status "PASSED" "CPU" "CPU使用率正常: ${cpu_usage}%"
    fi
}

# 检查网络连接
check_network() {
    log "INFO" "检查网络连接..."

    for host in $NETWORK_HOSTS_TO_CHECK; do
        if ping -c 1 -W "$TIMEOUT" "$host" &>/dev/null; then
            set_health_status "PASSED" "Network-$host" "网络连接正常"
        else
            set_health_status "FAILED" "Network-$host" "网络连接失败"
        fi
    done
}

# 检查API端点
check_api_endpoints() {
    log "INFO" "检查API端点..."

    for endpoint in $API_ENDPOINTS_TO_CHECK; do
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$endpoint" 2>/dev/null || echo "000")

        if [[ "$response_code" == "200" ]]; then
            set_health_status "PASSED" "API-$endpoint" "API响应正常"
        elif [[ "$response_code" =~ ^[45][0-9][0-9]$ ]]; then
            set_health_status "FAILED" "API-$endpoint" "API返回错误: $response_code"
        else
            set_health_status "FAILED" "API-$endpoint" "API无响应或超时"
        fi
    done
}

# 检查日志错误
check_log_errors() {
    log "INFO" "检查应用日志错误..."

    local log_paths=(
        "/var/log/syslog"
        "/var/log/messages"
        "./backend/logs/app.log"
        "./logs/error.log"
    )

    local error_count=0
    local current_time=$(date '+%Y-%m-%d %H:%M:%S')
    local one_hour_ago=$(date -d '1 hour ago' '+%Y-%m-%d %H:%M:%S')

    for log_path in "${log_paths[@]}"; do
        if [[ -f "$log_path" ]]; then
            # 检查最近1小时的错误日志
            local recent_errors=$(grep -i "error\|exception\|fatal" "$log_path" 2>/dev/null | wc -l || echo "0")
            error_count=$((error_count + recent_errors))
        fi
    done

    if [[ $error_count -gt 50 ]]; then
        set_health_status "FAILED" "Logs" "发现大量错误日志: $error_count 条"
    elif [[ $error_count -gt 10 ]]; then
        set_health_status "WARNING" "Logs" "发现较多错误日志: $error_count 条"
    else
        set_health_status "PASSED" "Logs" "错误日志数量正常: $error_count 条"
    fi
}

# =============================================================================
# 通知函数
# =============================================================================

# 发送通知
send_notification() {
    local status=$1
    local summary=$2

    if [[ "$NOTIFICATION_ENABLED" != "true" ]]; then
        return 0
    fi

    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local hostname=$(hostname)

    # 构建详细消息
    local details=""
    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
        details="${details}失败检查:\n"
        for check in "${FAILED_CHECKS[@]}"; do
            details="${details}- $check\n"
        done
    fi

    if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        details="${details}警告检查:\n"
        for check in "${WARNING_CHECKS[@]}"; do
            details="${details}- $check\n"
        done
    fi

    # Webhook通知
    if [[ -n "$WEBHOOK_URL" ]]; then
        local payload=$(cat <<EOF
{
    "msgtype": "text",
    "text": {
        "content": "系统健康检查报告\\n状态: $status\\n时间: $timestamp\\n主机: $hostname\\n摘要: $summary\\n\\n$details"
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
        local subject="系统健康检查报告 - $status"
        local body="时间: $timestamp\\n主机: $hostname\\n状态: $status\\n摘要: $summary\\n\\n$details"

        echo -e "$body" | mail -s "$subject" "$EMAIL_TO" &>/dev/null || true
    fi
}

# =============================================================================
# 主函数
# =============================================================================

# 显示帮助信息
show_help() {
    cat <<EOF
系统健康检查脚本

用法: $0 [选项]

选项:
    -h, --help          显示帮助信息
    -c, --config FILE   指定配置文件路径
    -i, --interval N    指定检查间隔（秒）
    -o, --once          只执行一次检查
    -v, --verbose       详细输出
    --daemon            后台运行
    --stop              停止后台运行的检查

检查项目:
    - 系统服务状态
    - Docker容器状态
    - 数据库连接
    - Redis连接
    - 磁盘空间使用
    - 内存使用率
    - CPU使用率
    - 网络连接
    - API端点响应
    - 应用日志错误

示例:
    $0                          # 执行一次完整检查
    $0 --daemon                 # 后台持续监控
    $0 -i 30 --once            # 30秒间隔执行一次
    $0 -c /etc/health.conf     # 使用指定配置文件
EOF
}

# 执行所有健康检查
run_health_checks() {
    log "INFO" "开始系统健康检查..."

    # 重置状态
    HEALTH_STATUS="HEALTHY"
    FAILED_CHECKS=()
    WARNING_CHECKS=()

    # 执行各项检查
    check_services
    check_docker_containers
    check_database
    check_redis
    check_disk_space
    check_memory_usage
    check_cpu_usage
    check_network
    check_api_endpoints
    check_log_errors

    # 生成报告
    generate_report
}

# 生成健康检查报告
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    log "INFO" "=========================================="
    log "INFO" "健康检查报告 - $timestamp"
    log "INFO" "=========================================="
    log "INFO" "总体状态: $HEALTH_STATUS"

    if [[ ${#FAILED_CHECKS[@]} -gt 0 ]]; then
        log "ERROR" "失败检查 (${#FAILED_CHECKS[@]}):"
        for check in "${FAILED_CHECKS[@]}"; do
            log "ERROR" "  - $check"
        done
    fi

    if [[ ${#WARNING_CHECKS[@]} -gt 0 ]]; then
        log "WARN" "警告检查 (${#WARNING_CHECKS[@]}):"
        for check in "${WARNING_CHECKS[@]}"; do
            log "WARN" "  - $check"
        done
    fi

    log "INFO" "=========================================="

    # 发送通知
    local summary="失败: ${#FAILED_CHECKS[@]}, 警告: ${#WARNING_CHECKS[@]}"
    send_notification "$HEALTH_STATUS" "$summary"

    # 返回适当的退出码
    case "$HEALTH_STATUS" in
        "HEALTHY")
            return 0
            ;;
        "WARNING")
            return 1
            ;;
        "UNHEALTHY")
            return 2
            ;;
    esac
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
            -i|--interval)
                CHECK_INTERVAL="$2"
                shift 2
                ;;
            -o|--once)
                RUN_ONCE="true"
                shift
                ;;
            -v|--verbose)
                VERBOSE="true"
                shift
                ;;
            --daemon)
                DAEMON_MODE="true"
                shift
                ;;
            --stop)
                STOP_DAEMON="true"
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

# 后台运行模式
run_daemon() {
    local pid_file="/var/run/health-check.pid"

    if [[ "${STOP_DAEMON:-false}" == "true" ]]; then
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                rm -f "$pid_file"
                log "INFO" "健康检查守护进程已停止"
            else
                log "WARN" "PID文件存在但进程不存在"
                rm -f "$pid_file"
            fi
        else
            log "WARN" "健康检查守护进程未运行"
        fi
        exit 0
    fi

    # 检查是否已经在运行
    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "ERROR" "健康检查守护进程已在运行 (PID: $pid)"
            exit 1
        else
            rm -f "$pid_file"
        fi
    fi

    # 启动守护进程
    log "INFO" "启动健康检查守护进程，检查间隔: ${CHECK_INTERVAL}秒"

    # 后台运行
    (
        echo $$ > "$pid_file"

        while true; do
            run_health_checks
            sleep "$CHECK_INTERVAL"
        done
    ) &

    log "INFO" "健康检查守护进程已启动 (PID: $!)"
}

# 主函数
main() {
    # 解析参数
    parse_args "$@"

    # 加载配置
    load_config

    # 创建目录
    create_directories

    # 检查运行模式
    if [[ "${DAEMON_MODE:-false}" == "true" ]] || [[ "${STOP_DAEMON:-false}" == "true" ]]; then
        run_daemon
    elif [[ "${RUN_ONCE:-false}" == "true" ]]; then
        run_health_checks
    else
        # 默认执行一次检查
        run_health_checks
    fi
}

# 信号处理
trap 'log "INFO" "健康检查被中断"; exit 130' INT TERM

# 执行主函数
main "$@"