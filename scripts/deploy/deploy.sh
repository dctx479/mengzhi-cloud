#!/bin/bash

# =============================================================================
# 自动化部署脚本 (Linux版本)
# 功能：拉取代码、安装依赖、数据库迁移、重启服务
# 作者：AI赋能云平台运维团队
# 版本：1.0.0
# =============================================================================

set -euo pipefail

# 配置文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/deploy-config.conf"

# 默认配置
PROJECT_DIR="${PROJECT_DIR:-/opt/agri-platform}"
GIT_REPO="${GIT_REPO:-https://github.com/your-org/agri-platform.git}"
GIT_BRANCH="${GIT_BRANCH:-main}"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/deployments}"

# 服务配置
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-docker-compose.yml}"
SERVICES_TO_RESTART="${SERVICES_TO_RESTART:-backend frontend}"

# 数据库配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3307}"
DB_USER="${DB_USER:-agri_user}"
DB_PASSWORD="${DB_PASSWORD:-agri_pass}"
DB_NAME="${DB_NAME:-agri_platform}"

# 部署配置
ENABLE_BACKUP="${ENABLE_BACKUP:-true}"
ENABLE_MIGRATION="${ENABLE_MIGRATION:-true}"
ENABLE_TESTS="${ENABLE_TESTS:-false}"
ROLLBACK_ON_FAILURE="${ROLLBACK_ON_FAILURE:-true}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"

# 通知配置
NOTIFICATION_ENABLED="${NOTIFICATION_ENABLED:-false}"
WEBHOOK_URL="${WEBHOOK_URL:-}"
EMAIL_ENABLED="${EMAIL_ENABLED:-false}"
EMAIL_TO="${EMAIL_TO:-}"

# 日志配置
LOG_DIR="${LOG_DIR:-/var/log/deploy}"
LOG_FILE="${LOG_DIR}/deploy.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 全局变量
DEPLOYMENT_ID=""
BACKUP_PATH=""
PREVIOUS_COMMIT=""
CURRENT_COMMIT=""
DEPLOYMENT_STATUS="UNKNOWN"

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
    DEPLOYMENT_STATUS="FAILED"
    send_notification "FAILED" "$1"

    if [[ "$ROLLBACK_ON_FAILURE" == "true" ]] && [[ -n "$BACKUP_PATH" ]]; then
        log "WARN" "开始自动回滚..."
        rollback_deployment
    fi

    exit 1
}

# 成功处理
success_exit() {
    log "INFO" "$1"
    DEPLOYMENT_STATUS="SUCCESS"
    send_notification "SUCCESS" "$1"
    exit 0
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
    log "INFO" "创建必要目录..."

    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"

    # 设置权限
    chmod 750 "$LOG_DIR"
    chmod 750 "$BACKUP_DIR"

    log "INFO" "目录创建完成"
}

# 检查依赖
check_dependencies() {
    log "INFO" "检查依赖工具..."

    local deps=("git" "docker" "docker-compose")

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            error_exit "依赖工具 $dep 未安装"
        fi
    done

    log "INFO" "依赖检查完成"
}

# 生成部署ID
generate_deployment_id() {
    DEPLOYMENT_ID="deploy_$(date '+%Y%m%d_%H%M%S')_$$"
    log "INFO" "部署ID: $DEPLOYMENT_ID"
}

# =============================================================================
# 备份函数
# =============================================================================

# 创建部署备份
create_backup() {
    if [[ "$ENABLE_BACKUP" != "true" ]]; then
        log "INFO" "备份功能未启用，跳过"
        return 0
    fi

    log "INFO" "创建部署备份..."

    BACKUP_PATH="${BACKUP_DIR}/${DEPLOYMENT_ID}"
    mkdir -p "$BACKUP_PATH"

    # 备份代码
    if [[ -d "$PROJECT_DIR" ]]; then
        log "INFO" "备份项目代码..."
        cp -r "$PROJECT_DIR" "${BACKUP_PATH}/code"
    fi

    # 备份数据库
    log "INFO" "备份数据库..."
    if command -v mysqldump &> /dev/null; then
        mysqldump \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --user="$DB_USER" \
            --password="$DB_PASSWORD" \
            --single-transaction \
            --routines \
            --triggers \
            "$DB_NAME" > "${BACKUP_PATH}/database.sql"

        if [[ $? -eq 0 ]]; then
            log "INFO" "数据库备份完成"
        else
            log "WARN" "数据库备份失败，但继续部署"
        fi
    else
        log "WARN" "mysqldump 未找到，跳过数据库备份"
    fi

    # 备份Docker镜像信息
    log "INFO" "备份Docker镜像信息..."
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}" > "${BACKUP_PATH}/docker-images.txt"

    # 备份配置文件
    if [[ -f "${PROJECT_DIR}/.env" ]]; then
        cp "${PROJECT_DIR}/.env" "${BACKUP_PATH}/"
    fi

    if [[ -f "${PROJECT_DIR}/${DOCKER_COMPOSE_FILE}" ]]; then
        cp "${PROJECT_DIR}/${DOCKER_COMPOSE_FILE}" "${BACKUP_PATH}/"
    fi

    log "INFO" "备份创建完成: $BACKUP_PATH"
}

# =============================================================================
# 代码部署函数
# =============================================================================

# 拉取代码
pull_code() {
    log "INFO" "拉取最新代码..."

    cd "$PROJECT_DIR" || error_exit "无法进入项目目录: $PROJECT_DIR"

    # 记录当前提交
    if git rev-parse HEAD &>/dev/null; then
        PREVIOUS_COMMIT=$(git rev-parse HEAD)
        log "INFO" "当前提交: $PREVIOUS_COMMIT"
    fi

    # 拉取最新代码
    if ! git fetch origin "$GIT_BRANCH"; then
        error_exit "拉取代码失败"
    fi

    # 检查是否有更新
    local remote_commit=$(git rev-parse "origin/$GIT_BRANCH")
    if [[ "$PREVIOUS_COMMIT" == "$remote_commit" ]]; then
        log "INFO" "代码无更新，跳过部署"
        exit 0
    fi

    # 切换到最新代码
    if ! git reset --hard "origin/$GIT_BRANCH"; then
        error_exit "切换代码失败"
    fi

    CURRENT_COMMIT=$(git rev-parse HEAD)
    log "INFO" "更新到提交: $CURRENT_COMMIT"

    # 显示变更信息
    if [[ -n "$PREVIOUS_COMMIT" ]]; then
        log "INFO" "代码变更:"
        git log --oneline "$PREVIOUS_COMMIT..$CURRENT_COMMIT" | head -10 | while read -r line; do
            log "INFO" "  $line"
        done
    fi
}

# 构建应用
build_application() {
    log "INFO" "构建应用..."

    cd "$PROJECT_DIR" || error_exit "无法进入项目目录"

    # 构建Docker镜像
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache; then
        error_exit "Docker镜像构建失败"
    fi

    log "INFO" "应用构建完成"
}

# 安装依赖
install_dependencies() {
    log "INFO" "安装依赖..."

    cd "$PROJECT_DIR" || error_exit "无法进入项目目录"

    # 后端依赖
    if [[ -f "backend/requirements.txt" ]]; then
        log "INFO" "安装后端依赖..."
        # 这里假设在Docker容器中安装，实际可能需要调整
        docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend pip install -r requirements.txt
    fi

    # 前端依赖
    if [[ -f "frontend/package.json" ]]; then
        log "INFO" "安装前端依赖..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm frontend npm ci
    fi

    log "INFO" "依赖安装完成"
}

# =============================================================================
# 数据库迁移函数
# =============================================================================

# 执行数据库迁移
run_database_migration() {
    if [[ "$ENABLE_MIGRATION" != "true" ]]; then
        log "INFO" "数据库迁移未启用，跳过"
        return 0
    fi

    log "INFO" "执行数据库迁移..."

    cd "$PROJECT_DIR" || error_exit "无法进入项目目录"

    # 检查数据库连接
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T mysql mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1;" &>/dev/null; then
        error_exit "数据库连接失败，无法执行迁移"
    fi

    # 执行Alembic迁移
    if [[ -d "backend/migrations" ]]; then
        log "INFO" "执行Alembic迁移..."
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend alembic upgrade head; then
            error_exit "数据库迁移失败"
        fi
    fi

    # 执行自定义SQL脚本
    if [[ -d "database/migrations" ]]; then
        log "INFO" "执行自定义SQL迁移..."
        for sql_file in database/migrations/*.sql; do
            if [[ -f "$sql_file" ]]; then
                log "INFO" "执行: $sql_file"
                if ! docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T mysql mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$sql_file"; then
                    error_exit "SQL脚本执行失败: $sql_file"
                fi
            fi
        done
    fi

    log "INFO" "数据库迁移完成"
}

# =============================================================================
# 服务管理函数
# =============================================================================

# 重启服务
restart_services() {
    log "INFO" "重启服务..."

    cd "$PROJECT_DIR" || error_exit "无法进入项目目录"

    # 停止服务
    log "INFO" "停止现有服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    # 启动服务
    log "INFO" "启动服务..."
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" up -d; then
        error_exit "服务启动失败"
    fi

    log "INFO" "服务重启完成"
}

# 健康检查
health_check() {
    log "INFO" "执行健康检查..."

    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=10
    local elapsed=0

    while [[ $elapsed -lt $timeout ]]; do
        # 检查容器状态
        local unhealthy_containers=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -v "Up" | grep -v "Name" | wc -l)

        if [[ $unhealthy_containers -eq 0 ]]; then
            # 检查API端点
            if curl -f -s "http://localhost:5000/health" &>/dev/null; then
                log "INFO" "健康检查通过"
                return 0
            fi
        fi

        log "INFO" "等待服务启动... ($elapsed/$timeout 秒)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done

    error_exit "健康检查失败，服务在 $timeout 秒内未能正常启动"
}

# =============================================================================
# 测试函数
# =============================================================================

# 运行测试
run_tests() {
    if [[ "$ENABLE_TESTS" != "true" ]]; then
        log "INFO" "测试未启用，跳过"
        return 0
    fi

    log "INFO" "运行测试..."

    cd "$PROJECT_DIR" || error_exit "无法进入项目目录"

    # 后端测试
    if [[ -f "backend/pytest.ini" ]] || [[ -d "backend/tests" ]]; then
        log "INFO" "运行后端测试..."
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend pytest tests/ -v; then
            error_exit "后端测试失败"
        fi
    fi

    # 前端测试
    if [[ -f "frontend/package.json" ]]; then
        log "INFO" "运行前端测试..."
        if ! docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm frontend npm test; then
            error_exit "前端测试失败"
        fi
    fi

    log "INFO" "测试完成"
}

# =============================================================================
# 回滚函数
# =============================================================================

# 回滚部署
rollback_deployment() {
    if [[ -z "$BACKUP_PATH" ]] || [[ ! -d "$BACKUP_PATH" ]]; then
        log "ERROR" "备份路径不存在，无法回滚"
        return 1
    fi

    log "WARN" "开始回滚部署..."

    cd "$PROJECT_DIR" || {
        log "ERROR" "无法进入项目目录"
        return 1
    }

    # 停止当前服务
    docker-compose -f "$DOCKER_COMPOSE_FILE" down || true

    # 恢复代码
    if [[ -d "${BACKUP_PATH}/code" ]]; then
        log "INFO" "恢复代码..."
        rm -rf "${PROJECT_DIR:?}"/*
        cp -r "${BACKUP_PATH}/code/"* "$PROJECT_DIR/"
    fi

    # 恢复配置文件
    if [[ -f "${BACKUP_PATH}/.env" ]]; then
        cp "${BACKUP_PATH}/.env" "$PROJECT_DIR/"
    fi

    if [[ -f "${BACKUP_PATH}/${DOCKER_COMPOSE_FILE}" ]]; then
        cp "${BACKUP_PATH}/${DOCKER_COMPOSE_FILE}" "$PROJECT_DIR/"
    fi

    # 恢复数据库
    if [[ -f "${BACKUP_PATH}/database.sql" ]]; then
        log "INFO" "恢复数据库..."
        mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "${BACKUP_PATH}/database.sql" || {
            log "WARN" "数据库恢复失败"
        }
    fi

    # 重启服务
    log "INFO" "重启服务..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    # 等待服务启动
    sleep 30

    # 简单健康检查
    if curl -f -s "http://localhost:5000/health" &>/dev/null; then
        log "INFO" "回滚完成，服务正常"
        DEPLOYMENT_STATUS="ROLLBACK_SUCCESS"
        send_notification "ROLLBACK_SUCCESS" "部署回滚成功"
    else
        log "ERROR" "回滚后服务仍然异常"
        DEPLOYMENT_STATUS="ROLLBACK_FAILED"
        send_notification "ROLLBACK_FAILED" "部署回滚失败"
    fi
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

    # 构建详细信息
    local details=""
    if [[ -n "$PREVIOUS_COMMIT" ]] && [[ -n "$CURRENT_COMMIT" ]]; then
        details="从 ${PREVIOUS_COMMIT:0:8} 更新到 ${CURRENT_COMMIT:0:8}"
    fi

    # Webhook通知
    if [[ -n "$WEBHOOK_URL" ]]; then
        local payload=$(cat <<EOF
{
    "msgtype": "text",
    "text": {
        "content": "部署通知\\n状态: $status\\n时间: $timestamp\\n主机: $hostname\\n部署ID: $DEPLOYMENT_ID\\n详情: $details\\n消息: $message"
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
        local subject="部署通知 - $status"
        local body="时间: $timestamp\\n主机: $hostname\\n部署ID: $DEPLOYMENT_ID\\n状态: $status\\n详情: $details\\n消息: $message"

        echo -e "$body" | mail -s "$subject" "$EMAIL_TO" &>/dev/null || true
    fi
}

# =============================================================================
# 清理函数
# =============================================================================

# 清理旧备份
cleanup_old_backups() {
    log "INFO" "清理旧备份..."

    local retention_days=7

    # 清理旧的部署备份
    find "$BACKUP_DIR" -name "deploy_*" -type d -mtime +$retention_days -exec rm -rf {} \; 2>/dev/null || true

    # 清理旧的Docker镜像
    docker image prune -f &>/dev/null || true

    log "INFO" "清理完成"
}

# =============================================================================
# 主函数
# =============================================================================

# 显示帮助信息
show_help() {
    cat <<EOF
自动化部署脚本

用法: $0 [选项]

选项:
    -h, --help              显示帮助信息
    -c, --config FILE       指定配置文件路径
    -b, --branch BRANCH     指定Git分支
    -e, --env ENV           指定环境 (dev/staging/prod)
    --no-backup             跳过备份
    --no-migration          跳过数据库迁移
    --no-tests              跳过测试
    --no-rollback           失败时不自动回滚
    --rollback ID           回滚到指定部署
    --dry-run               模拟运行，不执行实际操作

部署流程:
    1. 创建备份
    2. 拉取最新代码
    3. 构建应用
    4. 安装依赖
    5. 执行数据库迁移
    6. 重启服务
    7. 健康检查
    8. 运行测试
    9. 清理旧备份

示例:
    $0                              # 标准部署
    $0 -b develop                   # 部署develop分支
    $0 --no-tests                   # 跳过测试的部署
    $0 --rollback deploy_20240123   # 回滚到指定部署
    $0 --dry-run                    # 模拟运行

配置文件示例:
    PROJECT_DIR=/opt/agri-platform
    GIT_REPO=https://github.com/your-org/agri-platform.git
    GIT_BRANCH=main
    ENABLE_BACKUP=true
    ENABLE_MIGRATION=true
    ENABLE_TESTS=false
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
            -b|--branch)
                GIT_BRANCH="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --no-backup)
                ENABLE_BACKUP="false"
                shift
                ;;
            --no-migration)
                ENABLE_MIGRATION="false"
                shift
                ;;
            --no-tests)
                ENABLE_TESTS="false"
                shift
                ;;
            --no-rollback)
                ROLLBACK_ON_FAILURE="false"
                shift
                ;;
            --rollback)
                ROLLBACK_ID="$2"
                shift 2
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
    log "INFO" "自动化部署开始"
    log "INFO" "=========================================="

    # 解析参数
    parse_args "$@"

    # 加载配置
    load_config

    # 生成部署ID
    generate_deployment_id

    # 检查依赖
    check_dependencies

    # 创建目录
    create_directories

    # 处理回滚请求
    if [[ -n "${ROLLBACK_ID:-}" ]]; then
        BACKUP_PATH="${BACKUP_DIR}/${ROLLBACK_ID}"
        rollback_deployment
        exit $?
    fi

    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log "INFO" "模拟运行模式，不执行实际操作"
        log "INFO" "配置信息:"
        log "INFO" "  项目目录: $PROJECT_DIR"
        log "INFO" "  Git仓库: $GIT_REPO"
        log "INFO" "  Git分支: $GIT_BRANCH"
        log "INFO" "  备份: $ENABLE_BACKUP"
        log "INFO" "  迁移: $ENABLE_MIGRATION"
        log "INFO" "  测试: $ENABLE_TESTS"
        return 0
    fi

    # 执行部署流程
    create_backup
    pull_code
    build_application
    install_dependencies
    run_database_migration
    restart_services
    health_check
    run_tests
    cleanup_old_backups

    local end_time=$(date '+%s')
    local duration=$((end_time - start_time))

    log "INFO" "=========================================="
    log "INFO" "自动化部署完成，耗时: ${duration}秒"
    log "INFO" "=========================================="

    success_exit "部署成功完成，耗时: ${duration}秒"
}

# 信号处理
trap 'error_exit "部署被中断"' INT TERM

# 执行主函数
main "$@"