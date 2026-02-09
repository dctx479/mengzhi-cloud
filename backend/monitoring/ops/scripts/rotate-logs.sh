#!/bin/bash

##############################################################################
# Log Rotation Script
#
# Description: Archive, compress, and delete old log files
# Usage: ./rotate-logs.sh [--dry-run] [--retention-days <days>]
# Author: AI Platform Ops Team
# Version: 1.0.0
##############################################################################

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/ai-platform/ops"
readonly LOG_FILE="${LOG_DIR}/rotate-logs-$(date +%Y%m%d).log"

# Default settings
readonly DEFAULT_RETENTION_DAYS=30
readonly ARCHIVE_RETENTION_DAYS=90
readonly DISK_USAGE_THRESHOLD=85
readonly COMPRESS_AFTER_DAYS=1

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Flags
DRY_RUN=false
RETENTION_DAYS=$DEFAULT_RETENTION_DAYS

# Log directories to manage
LOG_DIRECTORIES=(
    "/var/log/ai-platform"
    "${SCRIPT_DIR}/../../../logs"
    "/var/log/nginx"
    "/var/log/postgresql"
)

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
    log_info "Starting log rotation script"
    log_info "Log file: ${LOG_FILE}"
}

check_dependencies() {
    local missing_deps=()

    for cmd in find gzip df du; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        exit 1
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

get_disk_usage() {
    local path=$1
    if [ -d "$path" ]; then
        du -sb "$path" 2>/dev/null | awk '{print $1}' || echo "0"
    else
        echo "0"
    fi
}

get_disk_usage_percent() {
    local path=$1
    df "$path" 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//' || echo "0"
}

check_disk_space() {
    log_info "Checking disk space..."

    local usage_percent=$(get_disk_usage_percent "/")

    log_stat "Disk usage: ${usage_percent}%"

    if [ "$usage_percent" -gt "$DISK_USAGE_THRESHOLD" ]; then
        log_warning "Disk usage exceeds threshold (${DISK_USAGE_THRESHOLD}%)"
        return 1
    else
        log_success "Disk usage within acceptable range"
        return 0
    fi
}

##############################################################################
# Log Rotation Functions
##############################################################################

rotate_directory() {
    local log_dir=$1

    if [ ! -d "$log_dir" ]; then
        log_warning "Directory does not exist: $log_dir"
        return 0
    fi

    log_info "Processing directory: $log_dir"

    local before_size=$(get_disk_usage "$log_dir")
    log_stat "Current size: $(format_bytes $before_size)"

    # Compress old logs
    compress_old_logs "$log_dir"

    # Delete old logs
    delete_old_logs "$log_dir"

    # Delete old archives
    delete_old_archives "$log_dir"

    local after_size=$(get_disk_usage "$log_dir")
    local saved=$((before_size - after_size))

    if [ $saved -gt 0 ]; then
        log_success "Reclaimed: $(format_bytes $saved)"
    fi
}

compress_old_logs() {
    local log_dir=$1

    log_info "Compressing logs older than $COMPRESS_AFTER_DAYS day(s)..."

    # Find uncompressed log files older than COMPRESS_AFTER_DAYS
    local files=$(find "$log_dir" -name "*.log" -type f -mtime +$COMPRESS_AFTER_DAYS ! -name "*.gz" 2>/dev/null || true)

    if [ -z "$files" ]; then
        log_info "No logs to compress"
        return 0
    fi

    local count=$(echo "$files" | wc -l)
    log_info "Found $count log file(s) to compress"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would compress $count file(s)"
        echo "$files" | head -n 5 | while read -r file; do
            log_warning "  - Would compress: $file"
        done
        return 0
    fi

    local compressed=0
    local failed=0

    while IFS= read -r file; do
        [ -z "$file" ] && continue

        local size_before=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")

        if gzip -9 "$file" 2>/dev/null; then
            compressed=$((compressed + 1))
            local size_after=$(stat -f%z "${file}.gz" 2>/dev/null || stat -c%s "${file}.gz" 2>/dev/null || echo "0")
            local saved=$((size_before - size_after))
            log_success "Compressed: $(basename "$file") (saved: $(format_bytes $saved))"
        else
            failed=$((failed + 1))
            log_warning "Failed to compress: $file"
        fi
    done <<< "$files"

    log_success "Compressed: $compressed, Failed: $failed"
}

delete_old_logs() {
    local log_dir=$1

    log_info "Deleting logs older than $RETENTION_DAYS day(s)..."

    # Find log files older than retention period
    local files=$(find "$log_dir" -name "*.log" -type f -mtime +$RETENTION_DAYS 2>/dev/null || true)

    if [ -z "$files" ]; then
        log_info "No old logs to delete"
        return 0
    fi

    local count=$(echo "$files" | wc -l)
    local total_size=0

    while IFS= read -r file; do
        [ -z "$file" ] && continue
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        total_size=$((total_size + size))
    done <<< "$files"

    log_warning "Found $count old log file(s) to delete ($(format_bytes $total_size))"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would delete $count file(s)"
        echo "$files" | head -n 5 | while read -r file; do
            log_warning "  - Would delete: $file"
        done
        return 0
    fi

    local deleted=0
    local failed=0

    while IFS= read -r file; do
        [ -z "$file" ] && continue

        if rm -f "$file" 2>/dev/null; then
            deleted=$((deleted + 1))
        else
            failed=$((failed + 1))
            log_warning "Failed to delete: $file"
        fi
    done <<< "$files"

    log_success "Deleted: $deleted, Failed: $failed (reclaimed: $(format_bytes $total_size))"
}

delete_old_archives() {
    local log_dir=$1

    log_info "Deleting archives older than $ARCHIVE_RETENTION_DAYS day(s)..."

    # Find compressed archives older than archive retention period
    local files=$(find "$log_dir" -name "*.log.gz" -type f -mtime +$ARCHIVE_RETENTION_DAYS 2>/dev/null || true)

    if [ -z "$files" ]; then
        log_info "No old archives to delete"
        return 0
    fi

    local count=$(echo "$files" | wc -l)
    local total_size=0

    while IFS= read -r file; do
        [ -z "$file" ] && continue
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
        total_size=$((total_size + size))
    done <<< "$files"

    log_warning "Found $count old archive(s) to delete ($(format_bytes $total_size))"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would delete $count archive(s)"
        echo "$files" | head -n 5 | while read -r file; do
            log_warning "  - Would delete: $file"
        done
        return 0
    fi

    local deleted=0
    local failed=0

    while IFS= read -r file; do
        [ -z "$file" ] && continue

        if rm -f "$file" 2>/dev/null; then
            deleted=$((deleted + 1))
        else
            failed=$((failed + 1))
            log_warning "Failed to delete: $file"
        fi
    done <<< "$files"

    log_success "Deleted: $deleted, Failed: $failed (reclaimed: $(format_bytes $total_size))"
}

##############################################################################
# Report Functions
##############################################################################

generate_summary() {
    cat <<EOF

==============================================================================
Log Rotation Summary
==============================================================================
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Retention: $RETENTION_DAYS days (logs), $ARCHIVE_RETENTION_DAYS days (archives)

Disk Usage:
$(df -h / | tail -n1 | awk '{printf "  Total: %s\n  Used: %s (%s)\n  Available: %s\n", $2, $3, $5, $4}')

Processed Directories:
EOF

    for dir in "${LOG_DIRECTORIES[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(get_disk_usage "$dir")
            echo "  $dir: $(format_bytes $size)"
        fi
    done

    cat <<EOF

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
            --retention-days)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --help)
                cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run                Show what would be done without executing
  --retention-days <days>  Set log retention period (default: $DEFAULT_RETENTION_DAYS)
  --help                   Show this help message

Behavior:
  - Compress logs older than $COMPRESS_AFTER_DAYS day(s)
  - Delete logs older than retention period
  - Delete archives older than $ARCHIVE_RETENTION_DAYS day(s)
  - Keep disk usage below ${DISK_USAGE_THRESHOLD}%

Examples:
  $0                              # Normal rotation
  $0 --dry-run                    # Preview rotation
  $0 --retention-days 14          # Keep logs for 14 days
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

    # Check initial disk space
    check_disk_space

    # Rotate logs in all directories
    for log_dir in "${LOG_DIRECTORIES[@]}"; do
        rotate_directory "$log_dir"
        echo ""
    done

    # Generate summary
    generate_summary

    # Check final disk space
    if check_disk_space; then
        log_success "Log rotation completed successfully"
        exit 0
    else
        log_warning "Log rotation completed but disk usage is still high"
        log_warning "Consider lowering retention period or adding more disk space"
        exit 1
    fi
}

# Execute main function
main "$@"
