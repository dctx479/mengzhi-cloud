#!/bin/bash

# Grafana社区仪表盘导入脚本
# 使用Grafana API自动导入社区仪表盘

set -e

# 配置
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin123}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Grafana是否就绪
check_grafana() {
    log_info "检查Grafana服务状态..."

    max_retries=30
    retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -s -f "${GRAFANA_URL}/api/health" > /dev/null 2>&1; then
            log_info "Grafana服务已就绪"
            return 0
        fi

        retry_count=$((retry_count + 1))
        log_warn "Grafana未就绪, 重试 $retry_count/$max_retries..."
        sleep 2
    done

    log_error "Grafana服务未就绪,超时退出"
    exit 1
}

# 导入仪表盘
import_dashboard() {
    local dashboard_id=$1
    local dashboard_name=$2

    log_info "导入仪表盘: $dashboard_name (ID: $dashboard_id)"

    # 从Grafana.com获取仪表盘JSON
    log_info "从Grafana.com下载仪表盘..."
    dashboard_json=$(curl -s "https://grafana.com/api/dashboards/${dashboard_id}/revisions/latest/download")

    if [ -z "$dashboard_json" ] || [ "$dashboard_json" = "null" ]; then
        log_error "下载仪表盘失败: $dashboard_name"
        return 1
    fi

    # 构造导入payload
    import_payload=$(cat <<EOF
{
  "dashboard": $dashboard_json,
  "overwrite": true,
  "inputs": [
    {
      "name": "DS_PROMETHEUS",
      "type": "datasource",
      "pluginId": "prometheus",
      "value": "Prometheus"
    }
  ]
}
EOF
)

    # 导入到Grafana
    log_info "导入仪表盘到Grafana..."
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -d "$import_payload" \
        "${GRAFANA_URL}/api/dashboards/import")

    # 检查响应
    if echo "$response" | grep -q "\"uid\""; then
        log_info "✓ 成功导入仪表盘: $dashboard_name"
        dashboard_uid=$(echo "$response" | grep -o '"uid":"[^"]*"' | cut -d'"' -f4)
        log_info "  仪表盘UID: $dashboard_uid"
        log_info "  访问地址: ${GRAFANA_URL}/d/${dashboard_uid}"
        return 0
    else
        log_error "✗ 导入仪表盘失败: $dashboard_name"
        log_error "  响应: $response"
        return 1
    fi
}

# 主函数
main() {
    log_info "=========================================="
    log_info "Grafana社区仪表盘导入工具"
    log_info "=========================================="
    log_info "Grafana URL: $GRAFANA_URL"
    log_info ""

    # 检查Grafana服务
    check_grafana

    # 导入社区仪表盘
    log_info ""
    log_info "开始导入社区仪表盘..."
    log_info ""

    success_count=0
    fail_count=0

    # 1. Node Exporter Full (1860) - 系统监控
    if import_dashboard "1860" "Node Exporter Full"; then
        success_count=$((success_count + 1))
    else
        fail_count=$((fail_count + 1))
    fi

    log_info ""

    # 2. Docker Container & Host Metrics (179) - 容器监控
    if import_dashboard "179" "Docker Container & Host Metrics"; then
        success_count=$((success_count + 1))
    else
        fail_count=$((fail_count + 1))
    fi

    # 汇总结果
    log_info ""
    log_info "=========================================="
    log_info "导入完成"
    log_info "=========================================="
    log_info "成功: $success_count"
    log_info "失败: $fail_count"
    log_info ""

    if [ $fail_count -eq 0 ]; then
        log_info "所有仪表盘导入成功! 🎉"
        log_info "访问Grafana查看: $GRAFANA_URL"
        return 0
    else
        log_warn "部分仪表盘导入失败,请检查日志"
        return 1
    fi
}

# 执行主函数
main "$@"
