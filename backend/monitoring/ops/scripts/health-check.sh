#!/bin/bash

##############################################################################
# Health Check Script
#
# Description: Check health status of all services and resources
# Usage: ./health-check.sh [--format <json|text|summary>] [--check <service>]
# Author: AI Platform Ops Team
# Version: 1.0.0
##############################################################################

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/ai-platform/ops"
readonly LOG_FILE="${LOG_DIR}/health-check-$(date +%Y%m%d).log"

# Thresholds
readonly CPU_WARNING_THRESHOLD=70
readonly CPU_CRITICAL_THRESHOLD=90
readonly MEMORY_WARNING_THRESHOLD=75
readonly MEMORY_CRITICAL_THRESHOLD=90
readonly DISK_WARNING_THRESHOLD=75
readonly DISK_CRITICAL_THRESHOLD=85

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Flags
OUTPUT_FORMAT="text"
CHECK_SPECIFIC=""

##############################################################################
# Logging Functions
##############################################################################

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" >> "${LOG_FILE}"
}

log_info() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${BLUE}ℹ${NC} $*"
    fi
    log "INFO" "$*"
}

log_success() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${GREEN}✓${NC} $*"
    fi
    log "SUCCESS" "$*"
}

log_warning() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${YELLOW}⚠${NC} $*"
    fi
    log "WARNING" "$*"
}

log_error() {
    if [ "$OUTPUT_FORMAT" != "json" ]; then
        echo -e "${RED}✗${NC} $*" >&2
    fi
    log "ERROR" "$*"
}

##############################################################################
# Helper Functions
##############################################################################

init_logging() {
    mkdir -p "${LOG_DIR}"
}

check_dependencies() {
    local missing_deps=()

    for cmd in docker curl jq df ps; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi
}

get_status_level() {
    local value=$1
    local warning=$2
    local critical=$3

    if [ "$value" -ge "$critical" ]; then
        echo "critical"
    elif [ "$value" -ge "$warning" ]; then
        echo "warning"
    else
        echo "healthy"
    fi
}

##############################################################################
# System Resource Checks
##############################################################################

check_cpu() {
    log_info "Checking CPU usage..."

    local cpu_usage
    if command -v mpstat &>/dev/null; then
        cpu_usage=$(mpstat 1 1 | tail -n1 | awk '{print 100 - $NF}' | cut -d. -f1)
    else
        # Fallback: use top
        cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}' | cut -d. -f1)
    fi

    local status=$(get_status_level "$cpu_usage" "$CPU_WARNING_THRESHOLD" "$CPU_CRITICAL_THRESHOLD")

    cat <<EOF
{
  "name": "CPU",
  "status": "$status",
  "usage_percent": $cpu_usage,
  "warning_threshold": $CPU_WARNING_THRESHOLD,
  "critical_threshold": $CPU_CRITICAL_THRESHOLD
}
EOF
}

check_memory() {
    log_info "Checking memory usage..."

    local total_mem=$(free -b | grep Mem | awk '{print $2}')
    local used_mem=$(free -b | grep Mem | awk '{print $3}')
    local memory_usage=$(awk "BEGIN {printf \"%.0f\", ($used_mem/$total_mem)*100}")

    local status=$(get_status_level "$memory_usage" "$MEMORY_WARNING_THRESHOLD" "$MEMORY_CRITICAL_THRESHOLD")

    cat <<EOF
{
  "name": "Memory",
  "status": "$status",
  "usage_percent": $memory_usage,
  "total_bytes": $total_mem,
  "used_bytes": $used_mem,
  "warning_threshold": $MEMORY_WARNING_THRESHOLD,
  "critical_threshold": $MEMORY_CRITICAL_THRESHOLD
}
EOF
}

check_disk() {
    log_info "Checking disk usage..."

    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    local total=$(df -B1 / | tail -1 | awk '{print $2}')
    local used=$(df -B1 / | tail -1 | awk '{print $3}')

    local status=$(get_status_level "$disk_usage" "$DISK_WARNING_THRESHOLD" "$DISK_CRITICAL_THRESHOLD")

    cat <<EOF
{
  "name": "Disk",
  "status": "$status",
  "usage_percent": $disk_usage,
  "total_bytes": $total,
  "used_bytes": $used,
  "warning_threshold": $DISK_WARNING_THRESHOLD,
  "critical_threshold": $DISK_CRITICAL_THRESHOLD
}
EOF
}

check_load() {
    log_info "Checking system load..."

    local load_1=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs)
    local load_5=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $2}' | xargs)
    local load_15=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $3}' | xargs)
    local cpu_cores=$(nproc 2>/dev/null || echo "1")

    # Status based on 5-minute load average vs CPU cores
    local load_percent=$(awk "BEGIN {printf \"%.0f\", ($load_5/$cpu_cores)*100}")
    local status=$(get_status_level "$load_percent" "70" "90")

    cat <<EOF
{
  "name": "System Load",
  "status": "$status",
  "load_1min": $load_1,
  "load_5min": $load_5,
  "load_15min": $load_15,
  "cpu_cores": $cpu_cores,
  "load_percent": $load_percent
}
EOF
}

##############################################################################
# Service Checks
##############################################################################

check_docker_containers() {
    log_info "Checking Docker containers..."

    local containers=$(docker ps --format '{{.Names}}' 2>/dev/null || true)

    if [ -z "$containers" ]; then
        cat <<EOF
{
  "name": "Docker Containers",
  "status": "warning",
  "message": "No containers found",
  "containers": []
}
EOF
        return
    fi

    local container_checks="["
    local overall_status="healthy"
    local first=true

    while IFS= read -r container; do
        [ -z "$container" ] && continue

        local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
        local health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container" 2>/dev/null || echo "none")

        local container_status="healthy"
        if [ "$status" != "running" ]; then
            container_status="critical"
            overall_status="critical"
        elif [ "$health" = "unhealthy" ]; then
            container_status="critical"
            overall_status="critical"
        elif [ "$health" = "starting" ]; then
            container_status="warning"
            [ "$overall_status" = "healthy" ] && overall_status="warning"
        fi

        [ "$first" = false ] && container_checks+=","
        first=false

        container_checks+=$(cat <<EOF
{
  "name": "$container",
  "status": "$container_status",
  "state": "$status",
  "health": "$health"
}
EOF
)
    done <<< "$containers"

    container_checks+="]"

    cat <<EOF
{
  "name": "Docker Containers",
  "status": "$overall_status",
  "containers": $container_checks
}
EOF
}

check_database() {
    log_info "Checking database..."

    local db_host="${DB_HOST:-localhost}"
    local db_port="${DB_PORT:-5432}"
    local db_user="${DB_USER:-postgres}"

    if pg_isready -h "$db_host" -p "$db_port" -U "$db_user" &>/dev/null 2>&1; then
        cat <<EOF
{
  "name": "PostgreSQL",
  "status": "healthy",
  "host": "$db_host",
  "port": $db_port
}
EOF
    else
        cat <<EOF
{
  "name": "PostgreSQL",
  "status": "critical",
  "host": "$db_host",
  "port": $db_port,
  "message": "Database not reachable"
}
EOF
    fi
}

check_redis() {
    log_info "Checking Redis..."

    local redis_host="${REDIS_HOST:-localhost}"
    local redis_port="${REDIS_PORT:-6379}"

    if redis-cli -h "$redis_host" -p "$redis_port" ping 2>/dev/null | grep -q "PONG"; then
        cat <<EOF
{
  "name": "Redis",
  "status": "healthy",
  "host": "$redis_host",
  "port": $redis_port
}
EOF
    else
        cat <<EOF
{
  "name": "Redis",
  "status": "critical",
  "host": "$redis_host",
  "port": $redis_port,
  "message": "Redis not reachable"
}
EOF
    fi
}

check_http_endpoint() {
    local name=$1
    local url=$2

    log_info "Checking HTTP endpoint: $name"

    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    local response_time=$(curl -s -o /dev/null -w "%{time_total}" "$url" 2>/dev/null || echo "0")

    local status="healthy"
    if [ "$response_code" = "000" ]; then
        status="critical"
    elif [ "$response_code" -ge 500 ]; then
        status="critical"
    elif [ "$response_code" -ge 400 ]; then
        status="warning"
    fi

    cat <<EOF
{
  "name": "$name",
  "status": "$status",
  "url": "$url",
  "response_code": $response_code,
  "response_time_seconds": $response_time
}
EOF
}

##############################################################################
# Output Functions
##############################################################################

output_json() {
    local checks=$1

    cat <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hostname": "$(hostname)",
  "checks": $checks
}
EOF
}

output_text() {
    local checks=$1

    echo ""
    echo "=============================================================================="
    echo "Health Check Report"
    echo "=============================================================================="
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Hostname:  $(hostname)"
    echo ""

    echo "$checks" | jq -r '.[] |
        "\(.name):\n" +
        "  Status: \(.status)\n" +
        if .usage_percent then "  Usage: \(.usage_percent)%\n" else "" end +
        if .containers then "  Containers: \(.containers | length)\n" else "" end +
        if .message then "  Message: \(.message)\n" else "" end'

    echo "=============================================================================="
    echo ""
}

output_summary() {
    local checks=$1

    local total=$(echo "$checks" | jq '. | length')
    local healthy=$(echo "$checks" | jq '[.[] | select(.status == "healthy")] | length')
    local warning=$(echo "$checks" | jq '[.[] | select(.status == "warning")] | length')
    local critical=$(echo "$checks" | jq '[.[] | select(.status == "critical")] | length')

    local overall_status="healthy"
    [ "$critical" -gt 0 ] && overall_status="critical"
    [ "$warning" -gt 0 ] && [ "$overall_status" = "healthy" ] && overall_status="warning"

    cat <<EOF
Status: $overall_status
Total Checks: $total
Healthy: $healthy
Warning: $warning
Critical: $critical
EOF
}

##############################################################################
# Main Function
##############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --check)
                CHECK_SPECIFIC="$2"
                shift 2
                ;;
            --help)
                cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --format <type>    Output format: json, text, summary (default: text)
  --check <name>     Run specific check only
  --help             Show this help message

Available Checks:
  cpu, memory, disk, load, docker, database, redis

Examples:
  $0                              # Full health check
  $0 --format json                # JSON output
  $0 --format summary             # Summary only
  $0 --check docker               # Check Docker only
EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Initialize
    init_logging
    check_dependencies

    # Run checks
    local checks="["
    local first=true

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "cpu" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_cpu)
    fi

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "memory" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_memory)
    fi

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "disk" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_disk)
    fi

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "load" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_load)
    fi

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "docker" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_docker_containers)
    fi

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "database" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_database)
    fi

    if [ -z "$CHECK_SPECIFIC" ] || [ "$CHECK_SPECIFIC" = "redis" ]; then
        [ "$first" = false ] && checks+=","
        first=false
        checks+=$(check_redis)
    fi

    checks+="]"

    # Output results
    case $OUTPUT_FORMAT in
        json)
            output_json "$checks"
            ;;
        summary)
            output_summary "$checks"
            ;;
        text|*)
            output_text "$checks"
            ;;
    esac

    # Exit code based on status
    local critical_count=$(echo "$checks" | jq '[.[] | select(.status == "critical")] | length')
    [ "$critical_count" -gt 0 ] && exit 2 || exit 0
}

# Execute main function
main "$@"
