#!/bin/bash
# 告警测试脚本 - 触发测试告警验证配置
# 用法: ./test-alerts.sh [alert_type]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查服务可用性
check_services() {
    print_info "检查服务可用性..."

    if ! curl -s "${PROMETHEUS_URL}/-/healthy" > /dev/null; then
        print_error "Prometheus 不可用: ${PROMETHEUS_URL}"
        exit 1
    fi
    print_success "Prometheus 正常"

    if ! curl -s "${ALERTMANAGER_URL}/-/healthy" > /dev/null; then
        print_error "Alertmanager 不可用: ${ALERTMANAGER_URL}"
        exit 1
    fi
    print_success "Alertmanager 正常"
}

# 触发高CPU使用率告警
test_high_cpu() {
    print_info "触发 HighCPUUsage 告警..."

    # 发送测试告警到 Alertmanager
    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighCPUUsage",
                    "severity": "warning",
                    "component": "system",
                    "instance": "test-server-01"
                },
                "annotations": {
                    "summary": "CPU使用率过高 (测试告警)",
                    "description": "系统CPU使用率为 85%，超过80%阈值。这是一个测试告警。"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "HighCPUUsage 告警已触发"
}

# 触发高内存使用率告警
test_high_memory() {
    print_info "触发 HighMemoryUsage 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighMemoryUsage",
                    "severity": "warning",
                    "component": "system",
                    "instance": "test-server-01"
                },
                "annotations": {
                    "summary": "内存使用率过高 (测试告警)",
                    "description": "系统内存使用率为 90%，超过85%阈值。这是一个测试告警。"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "HighMemoryUsage 告警已触发"
}

# 触发磁盘使用率告警
test_high_disk() {
    print_info "触发 HighDiskUsage 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighDiskUsage",
                    "severity": "warning",
                    "component": "system",
                    "instance": "test-server-01",
                    "mountpoint": "/data"
                },
                "annotations": {
                    "summary": "磁盘使用率过高 (/data) (测试告警)",
                    "description": "挂载点 /data 磁盘使用率为 88%，超过85%阈值。这是一个测试告警。",
                    "runbook_url": "https://docs.example.com/runbooks/high-disk-usage"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "HighDiskUsage 告警已触发"
}

# 触发数据库连接池告警
test_db_pool() {
    print_info "触发 DatabaseConnectionPoolExhausted 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "DatabaseConnectionPoolExhausted",
                    "severity": "critical",
                    "component": "database",
                    "instance": "postgres-01"
                },
                "annotations": {
                    "summary": "数据库连接池即将耗尽 (测试告警)",
                    "description": "数据库连接池使用率为 95%，超过90%阈值。这是一个测试告警。",
                    "runbook_url": "https://docs.example.com/runbooks/db-pool-exhausted"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "DatabaseConnectionPoolExhausted 告警已触发"
}

# 触发Redis内存告警
test_redis_memory() {
    print_info "触发 RedisMemoryHigh 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "RedisMemoryHigh",
                    "severity": "warning",
                    "component": "redis",
                    "instance": "redis-01"
                },
                "annotations": {
                    "summary": "Redis内存使用率过高 (测试告警)",
                    "description": "Redis内存使用率为 92%，超过90%阈值。这是一个测试告警。",
                    "runbook_url": "https://docs.example.com/runbooks/redis-memory-high"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "RedisMemoryHigh 告警已触发"
}

# 触发容器重启告警
test_container_restart() {
    print_info "触发 ContainerRestarting 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "ContainerRestarting",
                    "severity": "critical",
                    "component": "container",
                    "container_name": "backend-api"
                },
                "annotations": {
                    "summary": "容器频繁重启 (backend-api) (测试告警)",
                    "description": "容器 backend-api 在过去15分钟内重启超过3次。这是一个测试告警。",
                    "runbook_url": "https://docs.example.com/runbooks/container-restarting"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "ContainerRestarting 告警已触发"
}

# 触发API错误率告警
test_api_error() {
    print_info "触发 HighErrorRate 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighErrorRate",
                    "severity": "critical",
                    "component": "api",
                    "endpoint": "/api/v1/payments"
                },
                "annotations": {
                    "summary": "API错误率过高 (/api/v1/payments) (测试告警)",
                    "description": "端点 /api/v1/payments 的5xx错误率为 8%，超过5%阈值。这是一个测试告警。",
                    "runbook_url": "https://docs.example.com/runbooks/high-error-rate"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "HighErrorRate 告警已触发"
}

# 触发支付失败率告警
test_payment_failure() {
    print_info "触发 HighPaymentFailureRate 告警..."

    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighPaymentFailureRate",
                    "severity": "critical",
                    "component": "payment",
                    "payment_method": "alipay"
                },
                "annotations": {
                    "summary": "支付失败率过高 (alipay) (测试告警)",
                    "description": "alipay 支付方式的失败率为 7%，超过5%阈值。这是一个测试告警。",
                    "runbook_url": "https://docs.example.com/runbooks/payment-failure-rate"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "HighPaymentFailureRate 告警已触发"
}

# 测试告警抑制
test_alert_inhibition() {
    print_info "测试告警抑制机制..."

    # 先触发严重告警
    print_info "1. 触发 critical 级别告警..."
    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighCPUUsage",
                    "severity": "critical",
                    "component": "system",
                    "instance": "test-server-02"
                },
                "annotations": {
                    "summary": "CPU使用率严重过高 (测试抑制)",
                    "description": "系统CPU使用率为 95%，这是严重告警，应该抑制同组的warning告警。"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    sleep 2

    # 再触发警告告警（应该被抑制）
    print_info "2. 触发 warning 级别告警 (应该被抑制)..."
    curl -s -X POST "${ALERTMANAGER_URL}/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d '[
            {
                "labels": {
                    "alertname": "HighCPUUsage",
                    "severity": "warning",
                    "component": "system",
                    "instance": "test-server-02"
                },
                "annotations": {
                    "summary": "CPU使用率过高 (测试抑制 - 应该被抑制)",
                    "description": "系统CPU使用率为 85%，这个告警应该被同组的critical告警抑制。"
                },
                "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
            }
        ]'

    print_success "告警抑制测试已触发，请查看 Alertmanager UI 验证警告告警是否被抑制"
}

# 查看当前活跃告警
view_active_alerts() {
    print_info "查看当前活跃告警..."

    curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq '.data[] | {
        alertname: .labels.alertname,
        severity: .labels.severity,
        component: .labels.component,
        state: .status.state,
        inhibited: .status.inhibitedBy
    }'
}

# 清除所有测试告警
clear_test_alerts() {
    print_info "清除测试告警..."
    print_warning "注意: 需要手动在 Alertmanager UI 中 Silence 或等待告警过期"
    print_info "Alertmanager UI: ${ALERTMANAGER_URL}"
}

# 主菜单
show_menu() {
    echo ""
    echo "=========================================="
    echo "      告警测试脚本"
    echo "=========================================="
    echo "1) 测试 HighCPUUsage 告警"
    echo "2) 测试 HighMemoryUsage 告警"
    echo "3) 测试 HighDiskUsage 告警"
    echo "4) 测试 DatabaseConnectionPoolExhausted 告警"
    echo "5) 测试 RedisMemoryHigh 告警"
    echo "6) 测试 ContainerRestarting 告警"
    echo "7) 测试 HighErrorRate 告警"
    echo "8) 测试 HighPaymentFailureRate 告警"
    echo "9) 测试告警抑制机制"
    echo "10) 查看当前活跃告警"
    echo "11) 运行所有测试"
    echo "0) 退出"
    echo "=========================================="
    echo ""
}

# 运行所有测试
run_all_tests() {
    print_info "运行所有告警测试..."

    test_high_cpu
    sleep 1
    test_high_memory
    sleep 1
    test_high_disk
    sleep 1
    test_db_pool
    sleep 1
    test_redis_memory
    sleep 1
    test_container_restart
    sleep 1
    test_api_error
    sleep 1
    test_payment_failure
    sleep 2
    test_alert_inhibition

    print_success "所有测试已完成！"
    print_info "请访问以下地址查看结果:"
    print_info "  - Alertmanager: ${ALERTMANAGER_URL}"
    print_info "  - Prometheus: ${PROMETHEUS_URL}/alerts"
}

# 主程序
main() {
    # 检查服务
    check_services

    # 如果提供了参数，直接运行对应测试
    if [ $# -gt 0 ]; then
        case "$1" in
            cpu) test_high_cpu ;;
            memory) test_high_memory ;;
            disk) test_high_disk ;;
            db) test_db_pool ;;
            redis) test_redis_memory ;;
            container) test_container_restart ;;
            api) test_api_error ;;
            payment) test_payment_failure ;;
            inhibit) test_alert_inhibition ;;
            all) run_all_tests ;;
            view) view_active_alerts ;;
            *)
                print_error "未知的测试类型: $1"
                echo "可用的测试类型: cpu, memory, disk, db, redis, container, api, payment, inhibit, all, view"
                exit 1
                ;;
        esac
        exit 0
    fi

    # 交互式菜单
    while true; do
        show_menu
        read -p "请选择操作 [0-11]: " choice

        case $choice in
            1) test_high_cpu ;;
            2) test_high_memory ;;
            3) test_high_disk ;;
            4) test_db_pool ;;
            5) test_redis_memory ;;
            6) test_container_restart ;;
            7) test_api_error ;;
            8) test_payment_failure ;;
            9) test_alert_inhibition ;;
            10) view_active_alerts ;;
            11) run_all_tests ;;
            0)
                print_info "退出脚本"
                exit 0
                ;;
            *)
                print_error "无效的选择，请重试"
                ;;
        esac

        echo ""
        read -p "按 Enter 键继续..."
    done
}

# 运行主程序
main "$@"
