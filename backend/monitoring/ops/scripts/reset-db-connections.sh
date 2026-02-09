#!/bin/bash

##############################################################################
# Database Connection Reset Script
#
# Description: Kill idle connections, slow queries, and reset connection pool
# Usage: ./reset-db-connections.sh [--dry-run] [--db-name <name>]
# Author: AI Platform Ops Team
# Version: 1.0.0
##############################################################################

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/ai-platform/ops"
readonly LOG_FILE="${LOG_DIR}/reset-db-connections-$(date +%Y%m%d).log"

# Database connection settings (from environment or defaults)
readonly DB_HOST="${DB_HOST:-localhost}"
readonly DB_PORT="${DB_PORT:-5432}"
readonly DB_USER="${DB_USER:-postgres}"
readonly DB_NAME="${DB_NAME:-ai_platform}"

# Thresholds
readonly IDLE_TIMEOUT_MINUTES=5
readonly SLOW_QUERY_TIMEOUT_SECONDS=10
readonly MAX_CONNECTIONS=100

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Flags
DRY_RUN=false
TARGET_DB=""

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
    log_info "Starting database connection reset script"
    log_info "Log file: ${LOG_FILE}"
}

check_dependencies() {
    local missing_deps=()

    for cmd in psql pg_isready; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Install PostgreSQL client tools"
        exit 1
    fi
}

run_psql() {
    local query=$1
    local db=${2:-$DB_NAME}

    PGPASSWORD="${DB_PASSWORD:-}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db" -t -c "$query" 2>/dev/null || true
}

check_db_connection() {
    log_info "Checking database connection..."

    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" &>/dev/null; then
        log_success "Database is reachable"
        return 0
    else
        log_error "Cannot connect to database"
        return 1
    fi
}

get_connection_stats() {
    local db=${1:-$DB_NAME}

    log_info "Gathering connection statistics..."

    local total_connections=$(run_psql "SELECT count(*) FROM pg_stat_activity WHERE datname = '$db';")
    local active_connections=$(run_psql "SELECT count(*) FROM pg_stat_activity WHERE datname = '$db' AND state = 'active';")
    local idle_connections=$(run_psql "SELECT count(*) FROM pg_stat_activity WHERE datname = '$db' AND state = 'idle';")
    local idle_in_transaction=$(run_psql "SELECT count(*) FROM pg_stat_activity WHERE datname = '$db' AND state = 'idle in transaction';")

    cat <<EOF
Connection Statistics:
  Total:              $(echo $total_connections | xargs)
  Active:             $(echo $active_connections | xargs)
  Idle:               $(echo $idle_connections | xargs)
  Idle in Transaction: $(echo $idle_in_transaction | xargs)
  Max Connections:    $MAX_CONNECTIONS
EOF
}

list_idle_connections() {
    local db=${1:-$DB_NAME}

    log_info "Finding idle connections (idle > ${IDLE_TIMEOUT_MINUTES} minutes)..."

    local query="
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    EXTRACT(EPOCH FROM (NOW() - state_change))::int AS idle_seconds
FROM pg_stat_activity
WHERE datname = '$db'
  AND state = 'idle'
  AND state_change < NOW() - INTERVAL '$IDLE_TIMEOUT_MINUTES minutes'
ORDER BY state_change;
"

    local result=$(run_psql "$query")

    if [ -z "$(echo "$result" | xargs)" ]; then
        log_info "No idle connections found"
        return 0
    fi

    log_warning "Found idle connections:"
    echo "$result" | while read -r line; do
        [ -n "$(echo "$line" | xargs)" ] && log_warning "  $line"
    done

    echo "$result"
}

kill_idle_connections() {
    local db=${1:-$DB_NAME}

    log_info "Killing idle connections..."

    local pids=$(run_psql "
SELECT pid FROM pg_stat_activity
WHERE datname = '$db'
  AND state = 'idle'
  AND state_change < NOW() - INTERVAL '$IDLE_TIMEOUT_MINUTES minutes'
  AND pid != pg_backend_pid();
" | xargs)

    if [ -z "$pids" ]; then
        log_info "No idle connections to kill"
        return 0
    fi

    local count=$(echo "$pids" | wc -w)

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would kill $count idle connection(s)"
        for pid in $pids; do
            log_warning "  - Would kill PID: $pid"
        done
        return 0
    fi

    local killed=0
    for pid in $pids; do
        if run_psql "SELECT pg_terminate_backend($pid);" "$db" | grep -q "t"; then
            killed=$((killed + 1))
            log_success "Killed idle connection: PID $pid"
        else
            log_warning "Failed to kill connection: PID $pid"
        fi
    done

    log_success "Killed $killed idle connection(s)"
}

list_slow_queries() {
    local db=${1:-$DB_NAME}

    log_info "Finding slow queries (running > ${SLOW_QUERY_TIMEOUT_SECONDS}s)..."

    local query="
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    EXTRACT(EPOCH FROM (NOW() - query_start))::int AS query_seconds,
    LEFT(query, 100) AS query_snippet
FROM pg_stat_activity
WHERE datname = '$db'
  AND state = 'active'
  AND query_start < NOW() - INTERVAL '$SLOW_QUERY_TIMEOUT_SECONDS seconds'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;
"

    local result=$(run_psql "$query")

    if [ -z "$(echo "$result" | xargs)" ]; then
        log_info "No slow queries found"
        return 0
    fi

    log_warning "Found slow queries:"
    echo "$result" | while read -r line; do
        [ -n "$(echo "$line" | xargs)" ] && log_warning "  $line"
    done

    echo "$result"
}

kill_slow_queries() {
    local db=${1:-$DB_NAME}

    log_info "Killing slow queries..."

    local pids=$(run_psql "
SELECT pid FROM pg_stat_activity
WHERE datname = '$db'
  AND state = 'active'
  AND query_start < NOW() - INTERVAL '$SLOW_QUERY_TIMEOUT_SECONDS seconds'
  AND query NOT LIKE '%pg_stat_activity%'
  AND pid != pg_backend_pid();
" | xargs)

    if [ -z "$pids" ]; then
        log_info "No slow queries to kill"
        return 0
    fi

    local count=$(echo "$pids" | wc -w)

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would kill $count slow quer(y/ies)"
        for pid in $pids; do
            log_warning "  - Would kill PID: $pid"
        done
        return 0
    fi

    local killed=0
    for pid in $pids; do
        if run_psql "SELECT pg_terminate_backend($pid);" "$db" | grep -q "t"; then
            killed=$((killed + 1))
            log_success "Killed slow query: PID $pid"
        else
            log_warning "Failed to kill query: PID $pid"
        fi
    done

    log_success "Killed $killed slow quer(y/ies)"
}

reset_connection_pool() {
    local db=${1:-$DB_NAME}

    log_info "Resetting connection pool..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would reset connection pool for database: $db"
        return 0
    fi

    # Try to reload configuration
    run_psql "SELECT pg_reload_conf();" "$db" >/dev/null

    log_success "Connection pool reset triggered"
}

verify_recovery() {
    local db=${1:-$DB_NAME}

    log_info "Verifying database recovery..."

    sleep 2

    if ! check_db_connection; then
        log_error "Database connection check failed"
        return 1
    fi

    local active=$(run_psql "SELECT count(*) FROM pg_stat_activity WHERE datname = '$db' AND state = 'active';" | xargs)

    if [ "$active" -lt "$MAX_CONNECTIONS" ]; then
        log_success "Database is accepting connections (active: $active)"
        return 0
    else
        log_warning "Database connection count is high: $active"
        return 1
    fi
}

generate_report() {
    local db=${1:-$DB_NAME}
    local status=$2

    cat <<EOF

==============================================================================
Database Connection Reset Report
==============================================================================
Database: $db
Status: $status
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')

Before Reset:
$(get_connection_stats "$db" | sed 's/^/  /')

After Reset:
$(get_connection_stats "$db" | sed 's/^/  /')

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
            --db-name)
                TARGET_DB="$2"
                shift 2
                ;;
            --help)
                cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run           Show what would be done without executing
  --db-name <name>    Target specific database (default: $DB_NAME)
  --help              Show this help message

Environment Variables:
  DB_HOST             Database host (default: localhost)
  DB_PORT             Database port (default: 5432)
  DB_USER             Database user (default: postgres)
  DB_PASSWORD         Database password
  DB_NAME             Database name (default: ai_platform)

Examples:
  $0                              # Reset default database
  $0 --dry-run                    # Preview reset
  $0 --db-name my_db              # Reset specific database
  DB_HOST=db.example.com $0       # Use custom host
EOF
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Use target database if specified
    local db="${TARGET_DB:-$DB_NAME}"

    # Initialize
    init_logging
    check_dependencies

    # Check connection
    if ! check_db_connection; then
        exit 1
    fi

    # Show initial stats
    log_info "Initial connection statistics:"
    get_connection_stats "$db"

    # List problematic connections
    list_idle_connections "$db"
    list_slow_queries "$db"

    # Kill connections
    kill_idle_connections "$db"
    kill_slow_queries "$db"

    # Reset pool
    reset_connection_pool "$db"

    # Verify recovery
    if verify_recovery "$db"; then
        generate_report "$db" "SUCCESS"
        log_success "Database connection reset completed successfully"
        exit 0
    else
        generate_report "$db" "PARTIAL"
        log_warning "Database connection reset completed with warnings"
        exit 1
    fi
}

# Execute main function
main "$@"
