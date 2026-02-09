#!/bin/bash
# 告警统计脚本 - 分析告警频率和趋势
# 用法: ./alert-stats.sh [time_range]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
TIME_RANGE="${1:-24h}"  # 默认查询最近24小时

# 打印带颜色的消息
print_header() {
    echo -e "${CYAN}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 检查依赖
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        print_error "jq 未安装，请先安装: sudo apt-get install jq"
        exit 1
    fi

    if ! command -v curl &> /dev/null; then
        print_error "curl 未安装，请先安装: sudo apt-get install curl"
        exit 1
    fi
}

# 查询Prometheus获取告警统计
query_prometheus() {
    local query="$1"
    curl -s -G "${PROMETHEUS_URL}/api/v1/query" \
        --data-urlencode "query=${query}" | jq -r '.data.result'
}

# 查询Prometheus范围数据
query_prometheus_range() {
    local query="$1"
    local range="$2"
    curl -s -G "${PROMETHEUS_URL}/api/v1/query_range" \
        --data-urlencode "query=${query}" \
        --data-urlencode "start=$(date -u -d "${range} ago" +%Y-%m-%dT%H:%M:%SZ)" \
        --data-urlencode "end=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --data-urlencode "step=5m" | jq -r '.data.result'
}

# 获取当前活跃告警
get_active_alerts() {
    print_header "📋 当前活跃告警"

    local alerts=$(curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq '.data')
    local total=$(echo "$alerts" | jq 'length')

    print_info "总计: ${total} 个活跃告警"
    echo ""

    if [ "$total" -eq 0 ]; then
        print_success "没有活跃告警"
        return
    fi

    # 按严重程度统计
    echo -e "${CYAN}按严重程度统计:${NC}"
    echo "$alerts" | jq -r 'group_by(.labels.severity) | .[] | "\(.[]|.labels.severity): \(length) 个"' | sort -rn

    echo ""

    # 按组件统计
    echo -e "${CYAN}按组件统计:${NC}"
    echo "$alerts" | jq -r 'group_by(.labels.component) | .[] | "\(.[]|.labels.component): \(length) 个"' | sort -rn

    echo ""

    # 显示详细列表
    echo -e "${CYAN}告警详情:${NC}"
    printf "%-30s %-15s %-15s %-15s %s\n" "告警名称" "严重程度" "组件" "状态" "持续时间"
    printf "%-30s %-15s %-15s %-15s %s\n" "$(printf '%.0s-' {1..30})" "$(printf '%.0s-' {1..15})" "$(printf '%.0s-' {1..15})" "$(printf '%.0s-' {1..15})" "$(printf '%.0s-' {1..15})"

    echo "$alerts" | jq -r '.[] | "\(.labels.alertname)|\(.labels.severity // "unknown")|\(.labels.component // "unknown")|\(.status.state)|\(.startsAt)"' | \
    while IFS='|' read -r alertname severity component state startsAt; do
        # 计算持续时间
        start_ts=$(date -d "$startsAt" +%s 2>/dev/null || echo "0")
        current_ts=$(date +%s)
        duration=$((current_ts - start_ts))

        hours=$((duration / 3600))
        minutes=$(((duration % 3600) / 60))

        # 根据严重程度着色
        case "$severity" in
            critical|emergency)
                severity_colored="${RED}${severity}${NC}"
                ;;
            warning)
                severity_colored="${YELLOW}${severity}${NC}"
                ;;
            *)
                severity_colored="${severity}"
                ;;
        esac

        printf "%-30s %-24s %-15s %-15s %dh %dm\n" \
            "$alertname" \
            "$severity_colored" \
            "$component" \
            "$state" \
            "$hours" \
            "$minutes"
    done

    echo ""
}

# 统计告警频率
get_alert_frequency() {
    print_header "📊 告警频率统计 (最近 ${TIME_RANGE})"

    # 总告警触发次数
    print_info "查询告警触发次数..."
    local total_alerts=$(query_prometheus "sum(ALERTS{alertstate=\"firing\"})")
    echo "最近 ${TIME_RANGE} 总告警触发次数: ${total_alerts}"

    echo ""

    # 按告警名称统计
    echo -e "${CYAN}按告警名称统计 (Top 10):${NC}"
    query_prometheus 'topk(10, sum by(alertname) (ALERTS{alertstate="firing"}))' | \
    jq -r '.[] | "\(.metric.alertname): \(.value[1])"' | \
    while IFS=':' read -r alertname count; do
        printf "%-40s %s\n" "$alertname" "$count"
    done

    echo ""

    # 按组件统计
    echo -e "${CYAN}按组件统计:${NC}"
    query_prometheus 'sum by(component) (ALERTS{alertstate="firing"})' | \
    jq -r '.[] | "\(.metric.component // "unknown"): \(.value[1])"' | \
    while IFS=':' read -r component count; do
        printf "%-20s %s\n" "$component" "$count"
    done

    echo ""

    # 按严重程度统计
    echo -e "${CYAN}按严重程度统计:${NC}"
    query_prometheus 'sum by(severity) (ALERTS{alertstate="firing"})' | \
    jq -r '.[] | "\(.metric.severity): \(.value[1])"' | \
    while IFS=':' read -r severity count; do
        case "$severity" in
            critical|emergency)
                severity_colored="${RED}${severity}${NC}"
                ;;
            warning)
                severity_colored="${YELLOW}${severity}${NC}"
                ;;
            *)
                severity_colored="${severity}"
                ;;
        esac
        printf "%-24s %s\n" "$severity_colored" "$count"
    done

    echo ""
}

# 分析告警趋势
analyze_alert_trends() {
    print_header "📈 告警趋势分析 (最近 ${TIME_RANGE})"

    # 告警触发率
    print_info "分析告警触发率..."
    local alert_rate=$(query_prometheus "sum(rate(ALERTS{alertstate=\"firing\"}[5m]))")
    echo "当前告警触发率: ${alert_rate} 个/秒"

    echo ""

    # 频繁触发的告警
    echo -e "${CYAN}频繁触发的告警 (过去1小时触发 >3 次):${NC}"
    query_prometheus 'count_over_time(ALERTS{alertstate="firing"}[1h]) > 3' | \
    jq -r '.[] | "\(.metric.alertname) (\(.metric.component)): \(.value[1]) 次"'

    echo ""

    # 长时间未解决的告警
    echo -e "${CYAN}长时间未解决的告警 (>1小时):${NC}"
    local current_ts=$(date +%s)
    curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq -r '.data[] | select(.status.state == "active") | "\(.labels.alertname)|\(.labels.component)|\(.startsAt)"' | \
    while IFS='|' read -r alertname component startsAt; do
        start_ts=$(date -d "$startsAt" +%s 2>/dev/null || echo "$current_ts")
        duration=$((current_ts - start_ts))

        if [ "$duration" -gt 3600 ]; then
            hours=$((duration / 3600))
            minutes=$(((duration % 3600) / 60))
            printf "%-40s %-15s 已持续 %dh %dm\n" "$alertname" "$component" "$hours" "$minutes"
        fi
    done

    echo ""
}

# 健康评分
calculate_health_score() {
    print_header "💯 系统健康评分"

    # 获取告警数据
    local alerts=$(curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq '.data')
    local total_alerts=$(echo "$alerts" | jq 'length')
    local critical_alerts=$(echo "$alerts" | jq '[.[] | select(.labels.severity == "critical")] | length')
    local warning_alerts=$(echo "$alerts" | jq '[.[] | select(.labels.severity == "warning")] | length')

    # 计算健康评分 (100分制)
    local score=100

    # 每个 critical 告警扣 20 分
    score=$((score - critical_alerts * 20))

    # 每个 warning 告警扣 5 分
    score=$((score - warning_alerts * 5))

    # 确保分数不低于 0
    [ "$score" -lt 0 ] && score=0

    # 根据分数显示不同颜色和评级
    local rating=""
    local color=""

    if [ "$score" -ge 90 ]; then
        rating="优秀 (Excellent)"
        color="${GREEN}"
    elif [ "$score" -ge 70 ]; then
        rating="良好 (Good)"
        color="${CYAN}"
    elif [ "$score" -ge 50 ]; then
        rating="一般 (Fair)"
        color="${YELLOW}"
    else
        rating="差 (Poor)"
        color="${RED}"
    fi

    echo -e "健康评分: ${color}${score}/100 - ${rating}${NC}"
    echo ""
    echo "告警统计:"
    echo "  - Total: ${total_alerts}"
    echo "  - Critical: ${critical_alerts}"
    echo "  - Warning: ${warning_alerts}"
    echo ""

    # 给出建议
    if [ "$score" -lt 70 ]; then
        print_warning "系统存在较多告警，建议立即处理 critical 级别告警"
    fi

    echo ""
}

# 告警响应时间统计
analyze_response_time() {
    print_header "⏱️  告警响应时间分析"

    print_info "分析告警解决时间..."

    # 这里需要从 Prometheus 查询已解决告警的时间
    # 由于演示，我们只显示当前活跃告警的持续时间分布

    echo -e "${CYAN}当前活跃告警持续时间分布:${NC}"

    local alerts=$(curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq '.data')
    local current_ts=$(date +%s)

    local count_0_5m=0
    local count_5_15m=0
    local count_15_60m=0
    local count_1h_plus=0

    echo "$alerts" | jq -r '.[] | .startsAt' | while read -r startsAt; do
        start_ts=$(date -d "$startsAt" +%s 2>/dev/null || echo "$current_ts")
        duration=$((current_ts - start_ts))
        duration_min=$((duration / 60))

        if [ "$duration_min" -lt 5 ]; then
            count_0_5m=$((count_0_5m + 1))
        elif [ "$duration_min" -lt 15 ]; then
            count_5_15m=$((count_5_15m + 1))
        elif [ "$duration_min" -lt 60 ]; then
            count_15_60m=$((count_15_60m + 1))
        else
            count_1h_plus=$((count_1h_plus + 1))
        fi
    done

    echo "  0-5分钟:   $count_0_5m 个"
    echo "  5-15分钟:  $count_5_15m 个"
    echo "  15-60分钟: $count_15_60m 个"
    echo "  >1小时:    $count_1h_plus 个"

    echo ""
}

# 生成告警报告
generate_report() {
    print_header "📄 生成告警报告"

    local report_file="alert-report-$(date +%Y%m%d-%H%M%S).txt"

    {
        echo "=========================================="
        echo "告警统计报告"
        echo "生成时间: $(date)"
        echo "时间范围: 最近 ${TIME_RANGE}"
        echo "=========================================="
        echo ""

        echo "## 当前活跃告警"
        curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq '.data[] | {alertname: .labels.alertname, severity: .labels.severity, component: .labels.component, state: .status.state}'
        echo ""

        echo "## 告警频率统计"
        query_prometheus 'sum by(alertname) (ALERTS{alertstate="firing"})' | jq -r '.[] | "\(.metric.alertname): \(.value[1])"'
        echo ""

        echo "## 系统健康评分"
        # 重新计算（避免重复代码，这里简化）
        local alerts=$(curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq '.data')
        local total_alerts=$(echo "$alerts" | jq 'length')
        echo "总告警数: ${total_alerts}"
        echo ""

    } > "$report_file"

    print_success "报告已生成: ${report_file}"
}

# 主菜单
show_menu() {
    echo ""
    echo "=========================================="
    echo "      告警统计分析"
    echo "=========================================="
    echo "1) 查看当前活跃告警"
    echo "2) 告警频率统计"
    echo "3) 告警趋势分析"
    echo "4) 系统健康评分"
    echo "5) 告警响应时间分析"
    echo "6) 生成完整报告"
    echo "7) 运行完整分析"
    echo "0) 退出"
    echo "=========================================="
    echo ""
}

# 运行完整分析
run_full_analysis() {
    get_active_alerts
    get_alert_frequency
    analyze_alert_trends
    calculate_health_score
    analyze_response_time
}

# 主程序
main() {
    # 检查依赖
    check_dependencies

    # 如果提供了参数，直接运行对应分析
    if [ $# -gt 1 ]; then
        case "$2" in
            active) get_active_alerts ;;
            frequency) get_alert_frequency ;;
            trends) analyze_alert_trends ;;
            health) calculate_health_score ;;
            response) analyze_response_time ;;
            report) generate_report ;;
            full) run_full_analysis ;;
            *)
                print_error "未知的分析类型: $2"
                echo "可用的分析类型: active, frequency, trends, health, response, report, full"
                exit 1
                ;;
        esac
        exit 0
    fi

    # 交互式菜单
    while true; do
        show_menu
        read -p "请选择操作 [0-7]: " choice

        case $choice in
            1) get_active_alerts ;;
            2) get_alert_frequency ;;
            3) analyze_alert_trends ;;
            4) calculate_health_score ;;
            5) analyze_response_time ;;
            6) generate_report ;;
            7) run_full_analysis ;;
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
