#!/bin/bash

##############################################################################
# Redis Cache Cleanup Script
#
# Description: Clean expired keys, analyze memory, and manage cache namespaces
# Usage: ./cleanup-redis.sh [--dry-run] [--namespace <ns>] [--flush]
# Author: AI Platform Ops Team
# Version: 1.0.0
##############################################################################

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/ai-platform/ops"
readonly LOG_FILE="${LOG_DIR}/cleanup-redis-$(date +%Y%m%d).log"

# Redis connection settings (from environment or defaults)
readonly REDIS_HOST="${REDIS_HOST:-localhost}"
readonly REDIS_PORT="${REDIS_PORT:-6379}"
readonly REDIS_DB="${REDIS_DB:-0}"
readonly REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# Cleanup settings
readonly SAMPLE_SIZE=1000
readonly BATCH_SIZE=100

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly NC='\033[0m'

# Flags
DRY_RUN=false
FLUSH_NAMESPACE=false
TARGET_NAMESPACE=""

##############################################################################
# Logging Functions
##############################################################################

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $*"
    log "INFO" "$*"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*"
    log "SUCCESS" "$*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
    log "WARNING" "$*"
}

log_error() {
    echo -e "${RED}✗${NC} $*" >&2
    log "ERROR" "$*"
}

log_stat() {
    echo -e "${CYAN}📊${NC} $*"
    log "STAT" "$*"
}

##############################################################################
# Helper Functions
##############################################################################

init_logging() {
    mkdir -p "${LOG_DIR}"
    log_info "Starting Redis cleanup script"
    log_info "Log file: ${LOG_FILE}"
}

check_dependencies() {
    local missing_deps=()

    if ! command -v redis-cli &> /dev/null; then
        missing_deps+=("redis-cli")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Install Redis client tools"
        exit 1
    fi
}

run_redis() {
    local cmd=$1

    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -n "$REDIS_DB" -a "$REDIS_PASSWORD" --no-auth-warning $cmd 2>/dev/null
    else
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -n "$REDIS_DB" $cmd 2>/dev/null
    fi
}

check_redis_connection() {
    log_info "Checking Redis connection..."

    if run_redis "PING" | grep -q "PONG"; then
        log_success "Redis is reachable"
        return 0
    else
        log_error "Cannot connect to Redis"
        return 1
    fi
}

format_bytes() {
    local bytes=$1
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1024}")KB"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1048576}")MB"
    else
        echo "$(awk "BEGIN {printf \"%.2f\", $bytes/1073741824}")GB"
    fi
}

##############################################################################
# Redis Info Functions
##############################################################################

get_redis_info() {
    log_info "Gathering Redis information..."

    local info=$(run_redis "INFO")

    local used_memory=$(echo "$info" | grep "^used_memory:" | cut -d: -f2 | tr -d '\r')
    local used_memory_peak=$(echo "$info" | grep "^used_memory_peak:" | cut -d: -f2 | tr -d '\r')
    local total_keys=$(run_redis "DBSIZE" | cut -d: -f2 | tr -d '\r')
    local connected_clients=$(echo "$info" | grep "^connected_clients:" | cut -d: -f2 | tr -d '\r')
    local evicted_keys=$(echo "$info" | grep "^evicted_keys:" | cut -d: -f2 | tr -d '\r')

    cat <<EOF
Redis Information:
  Host:              $REDIS_HOST:$REDIS_PORT
  Database:          $REDIS_DB
  Used Memory:       $(format_bytes $used_memory)
  Peak Memory:       $(format_bytes $used_memory_peak)
  Total Keys:        $total_keys
  Connected Clients: $connected_clients
  Evicted Keys:      $evicted_keys
EOF
}

analyze_key_space() {
    log_info "Analyzing key space..."

    local namespaces=$(run_redis "KEYS *" | cut -d: -f1 | sort | uniq -c | sort -rn)

    if [ -z "$namespaces" ]; then
        log_info "No keys found"
        return 0
    fi

    log_stat "Key distribution by namespace:"
    echo "$namespaces" | head -n 10 | while read -r count namespace; do
        log_stat "  $namespace: $count keys"
    done
}

analyze_memory_usage() {
    log_info "Analyzing memory usage by key type..."

    local sample_keys=$(run_redis "RANDOMKEY" 2>/dev/null | head -n $SAMPLE_SIZE)

    if [ -z "$sample_keys" ]; then
        log_info "No keys to sample"
        return 0
    fi

    local string_count=0
    local list_count=0
    local set_count=0
    local zset_count=0
    local hash_count=0

    while IFS= read -r key; do
        [ -z "$key" ] && continue

        local type=$(run_redis "TYPE $key" | tr -d '\r')

        case $type in
            string) string_count=$((string_count + 1)) ;;
            list) list_count=$((list_count + 1)) ;;
            set) set_count=$((set_count + 1)) ;;
            zset) zset_count=$((zset_count + 1)) ;;
            hash) hash_count=$((hash_count + 1)) ;;
        esac
    done <<< "$sample_keys"

    log_stat "Key type distribution (sample of $SAMPLE_SIZE):"
    log_stat "  String: $string_count"
    log_stat "  List:   $list_count"
    log_stat "  Set:    $set_count"
    log_stat "  ZSet:   $zset_count"
    log_stat "  Hash:   $hash_count"
}

##############################################################################
# Cleanup Functions
##############################################################################

find_expired_keys() {
    log_info "Finding keys with expiration..."

    local keys_with_ttl=0
    local keys_without_ttl=0
    local expired_soon=0

    local sample_keys=$(run_redis "KEYS *" | head -n $SAMPLE_SIZE)

    if [ -z "$sample_keys" ]; then
        log_info "No keys to check"
        return 0
    fi

    while IFS= read -r key; do
        [ -z "$key" ] && continue

        local ttl=$(run_redis "TTL $key" | tr -d '\r')

        if [ "$ttl" = "-1" ]; then
            keys_without_ttl=$((keys_without_ttl + 1))
        elif [ "$ttl" = "-2" ]; then
            # Key doesn't exist (already expired)
            continue
        elif [ "$ttl" -lt 60 ]; then
            expired_soon=$((expired_soon + 1))
        else
            keys_with_ttl=$((keys_with_ttl + 1))
        fi
    done <<< "$sample_keys"

    log_stat "Expiration analysis (sample of $SAMPLE_SIZE):"
    log_stat "  Keys with TTL:     $keys_with_ttl"
    log_stat "  Keys without TTL:  $keys_without_ttl"
    log_stat "  Expiring soon:     $expired_soon"
}

cleanup_expired_keys() {
    log_info "Triggering expired key cleanup..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would run: SCAN + DELETE for expired keys"
        return 0
    fi

    # Redis automatically removes expired keys, but we can trigger cleanup
    # by scanning and checking TTL
    local deleted=0
    local cursor=0

    while true; do
        local result=$(run_redis "SCAN $cursor COUNT $BATCH_SIZE")
        cursor=$(echo "$result" | head -n1 | tr -d '\r')
        local keys=$(echo "$result" | tail -n +2)

        if [ -n "$keys" ]; then
            while IFS= read -r key; do
                [ -z "$key" ] && continue

                local ttl=$(run_redis "TTL $key" | tr -d '\r')

                # Delete keys that are expired (TTL = -2)
                if [ "$ttl" = "-2" ]; then
                    run_redis "DEL $key" >/dev/null
                    deleted=$((deleted + 1))
                fi
            done <<< "$keys"
        fi

        [ "$cursor" = "0" ] && break
    done

    log_success "Deleted $deleted expired keys"
}

cleanup_namespace() {
    local namespace=$1

    log_info "Cleaning namespace: $namespace"

    local pattern="${namespace}:*"
    local keys=$(run_redis "KEYS $pattern")

    if [ -z "$keys" ]; then
        log_info "No keys found in namespace: $namespace"
        return 0
    fi

    local count=$(echo "$keys" | wc -l)
    log_warning "Found $count key(s) in namespace: $namespace"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would delete $count key(s)"
        echo "$keys" | head -n 10 | while read -r key; do
            log_warning "  - Would delete: $key"
        done
        return 0
    fi

    # Confirm deletion for large namespaces
    if [ $count -gt 100 ] && [ "$FLUSH_NAMESPACE" = false ]; then
        log_warning "Namespace has >100 keys. Use --flush to confirm deletion."
        return 1
    fi

    local deleted=0
    echo "$keys" | while read -r key; do
        [ -z "$key" ] && continue

        if run_redis "DEL $key" >/dev/null; then
            deleted=$((deleted + 1))
        fi
    done

    log_success "Deleted $deleted key(s) from namespace: $namespace"
}

optimize_memory() {
    log_info "Optimizing Redis memory..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would run: MEMORY PURGE"
        return 0
    fi

    # Try to reclaim memory
    run_redis "MEMORY PURGE" >/dev/null 2>&1 || log_warning "MEMORY PURGE not supported"

    log_success "Memory optimization triggered"
}

##############################################################################
# Report Functions
##############################################################################

generate_report() {
    local status=$1

    cat <<EOF

==============================================================================
Redis Cleanup Report
==============================================================================
Status: $status
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')

Before Cleanup:
$(get_redis_info | sed 's/^/  /')

After Cleanup:
$(get_redis_info | sed 's/^/  /')

Log File: ${LOG_FILE}
==============================================================================

EOF
}

##############################################################################
# Main Function
##############################################################################

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                log_warning "Running in DRY RUN mode - no changes will be made"
                shift
                ;;
            --namespace)
                TARGET_NAMESPACE="$2"
                shift 2
                ;;
            --flush)
                FLUSH_NAMESPACE=true
                shift
                ;;
            --help)
                cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run           Show what would be done without executing
  --namespace <ns>    Clean specific namespace (e.g., "cache", "session")
  --flush             Confirm deletion of large namespaces (>100 keys)
  --help              Show this help message

Environment Variables:
  REDIS_HOST          Redis host (default: localhost)
  REDIS_PORT          Redis port (default: 6379)
  REDIS_DB            Redis database number (default: 0)
  REDIS_PASSWORD      Redis password (optional)

Examples:
  $0                              # General cleanup
  $0 --dry-run                    # Preview cleanup
  $0 --namespace cache            # Clean cache namespace
  $0 --namespace session --flush  # Force clean session namespace
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

    # Check connection
    if ! check_redis_connection; then
        exit 1
    fi

    # Show initial info
    log_info "Initial Redis state:"
    get_redis_info
    echo ""

    # Analyze
    analyze_key_space
    analyze_memory_usage
    find_expired_keys
    echo ""

    # Cleanup
    if [ -n "$TARGET_NAMESPACE" ]; then
        cleanup_namespace "$TARGET_NAMESPACE"
    else
        cleanup_expired_keys
        optimize_memory
    fi

    # Generate report
    generate_report "SUCCESS"

    log_success "Redis cleanup completed successfully"
}

# Execute main function
main "$@"
