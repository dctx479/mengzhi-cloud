#!/bin/bash

##############################################################################
# Resource Cleanup Script
#
# Description: Clean up Docker resources, temp files, and old logs
# Usage: ./cleanup-resources.sh [--dry-run] [--aggressive]
# Author: AI Platform Ops Team
# Version: 1.0.0
##############################################################################

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/ai-platform/ops"
readonly LOG_FILE="${LOG_DIR}/cleanup-resources-$(date +%Y%m%d).log"
readonly TEMP_DIR="/tmp/ai-platform"
readonly LOG_RETENTION_DAYS=7
readonly DOCKER_IMAGE_RETENTION_DAYS=30

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m'

# Flags
DRY_RUN=false
AGGRESSIVE=false

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
    log_info "Starting resource cleanup script"
    log_info "Log file: ${LOG_FILE}"
}

check_dependencies() {
    local missing_deps=()

    for cmd in docker du df find; do
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

##############################################################################
# Docker Cleanup Functions
##############################################################################

cleanup_docker_containers() {
    log_info "Cleaning up Docker containers..."

    local stopped_containers=$(docker ps -a -q -f status=exited -f status=dead 2>/dev/null || true)

    if [ -z "$stopped_containers" ]; then
        log_info "No stopped containers to remove"
        return 0
    fi

    local count=$(echo "$stopped_containers" | wc -l)
    log_info "Found $count stopped container(s)"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would remove $count stopped containers"
        echo "$stopped_containers" | while read -r container; do
            local name=$(docker inspect --format='{{.Name}}' "$container" 2>/dev/null | sed 's/^\///')
            log_warning "  - Would remove: $name ($container)"
        done
        return 0
    fi

    echo "$stopped_containers" | xargs docker rm -v 2>/dev/null || true
    log_success "Removed $count stopped container(s)"
}

cleanup_docker_images() {
    log_info "Cleaning up Docker images..."

    # Remove dangling images
    local dangling_images=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    local dangling_count=0

    if [ -n "$dangling_images" ]; then
        dangling_count=$(echo "$dangling_images" | wc -l)
        log_info "Found $dangling_count dangling image(s)"

        if [ "$DRY_RUN" = true ]; then
            log_warning "[DRY RUN] Would remove $dangling_count dangling images"
        else
            echo "$dangling_images" | xargs docker rmi 2>/dev/null || true
            log_success "Removed $dangling_count dangling image(s)"
        fi
    else
        log_info "No dangling images found"
    fi

    # Remove old unused images (aggressive mode only)
    if [ "$AGGRESSIVE" = true ]; then
        log_info "Aggressive mode: Checking for old unused images..."

        local old_date=$(date -d "$DOCKER_IMAGE_RETENTION_DAYS days ago" +%s 2>/dev/null || date -v-${DOCKER_IMAGE_RETENTION_DAYS}d +%s)
        local old_images=()

        while IFS= read -r image; do
            local created=$(docker inspect --format='{{.Created}}' "$image" 2>/dev/null | cut -d'T' -f1)
            local created_ts=$(date -d "$created" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "$created" +%s)

            if [ "$created_ts" -lt "$old_date" ]; then
                old_images+=("$image")
            fi
        done < <(docker images -q 2>/dev/null || true)

        if [ ${#old_images[@]} -gt 0 ]; then
            log_info "Found ${#old_images[@]} old unused image(s)"

            if [ "$DRY_RUN" = true ]; then
                log_warning "[DRY RUN] Would remove ${#old_images[@]} old images"
            else
                for img in "${old_images[@]}"; do
                    docker rmi "$img" 2>/dev/null || log_warning "Could not remove image: $img"
                done
                log_success "Removed old unused images"
            fi
        fi
    fi
}

cleanup_docker_volumes() {
    log_info "Cleaning up Docker volumes..."

    local unused_volumes=$(docker volume ls -qf dangling=true 2>/dev/null || true)

    if [ -z "$unused_volumes" ]; then
        log_info "No unused volumes to remove"
        return 0
    fi

    local count=$(echo "$unused_volumes" | wc -l)
    log_info "Found $count unused volume(s)"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would remove $count unused volumes"
        echo "$unused_volumes" | while read -r volume; do
            log_warning "  - Would remove: $volume"
        done
        return 0
    fi

    echo "$unused_volumes" | xargs docker volume rm 2>/dev/null || true
    log_success "Removed $count unused volume(s)"
}

cleanup_docker_networks() {
    log_info "Cleaning up Docker networks..."

    local unused_networks=$(docker network ls -q -f "type=custom" 2>/dev/null || true)
    local removed=0

    if [ -z "$unused_networks" ]; then
        log_info "No custom networks to check"
        return 0
    fi

    while IFS= read -r network; do
        local containers=$(docker network inspect --format='{{range .Containers}}{{.Name}} {{end}}' "$network" 2>/dev/null || true)

        if [ -z "$containers" ]; then
            local name=$(docker network inspect --format='{{.Name}}' "$network" 2>/dev/null || echo "unknown")

            if [ "$DRY_RUN" = true ]; then
                log_warning "[DRY RUN] Would remove unused network: $name"
            else
                if docker network rm "$network" 2>/dev/null; then
                    removed=$((removed + 1))
                fi
            fi
        fi
    done <<< "$unused_networks"

    if [ $removed -gt 0 ]; then
        log_success "Removed $removed unused network(s)"
    else
        log_info "No unused networks to remove"
    fi
}

cleanup_docker_build_cache() {
    log_info "Cleaning up Docker build cache..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would prune Docker build cache"
        return 0
    fi

    local output=$(docker builder prune -f 2>&1 || true)
    log_success "Build cache cleaned"
    echo "$output" | grep "Total reclaimed space" && true
}

##############################################################################
# File System Cleanup Functions
##############################################################################

cleanup_temp_files() {
    log_info "Cleaning up temporary files..."

    if [ ! -d "$TEMP_DIR" ]; then
        log_info "Temp directory does not exist: $TEMP_DIR"
        return 0
    fi

    local before_size=$(get_disk_usage "$TEMP_DIR")

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would clean: $TEMP_DIR"
        local file_count=$(find "$TEMP_DIR" -type f 2>/dev/null | wc -l)
        log_warning "  - Files to remove: $file_count"
        log_warning "  - Space to reclaim: $(format_bytes $before_size)"
        return 0
    fi

    # Remove files older than 1 day
    find "$TEMP_DIR" -type f -mtime +1 -delete 2>/dev/null || true

    # Remove empty directories
    find "$TEMP_DIR" -type d -empty -delete 2>/dev/null || true

    local after_size=$(get_disk_usage "$TEMP_DIR")
    local reclaimed=$((before_size - after_size))

    log_success "Cleaned temp files, reclaimed: $(format_bytes $reclaimed)"
}

cleanup_old_logs() {
    log_info "Cleaning up old log files..."

    if [ ! -d "$LOG_DIR" ]; then
        log_info "Log directory does not exist: $LOG_DIR"
        return 0
    fi

    local before_size=$(get_disk_usage "$LOG_DIR")

    if [ "$DRY_RUN" = true ]; then
        local old_logs=$(find "$LOG_DIR" -name "*.log" -type f -mtime +$LOG_RETENTION_DAYS 2>/dev/null || true)
        local count=$(echo "$old_logs" | grep -c . || echo "0")

        log_warning "[DRY RUN] Would remove logs older than $LOG_RETENTION_DAYS days"
        log_warning "  - Files to remove: $count"
        log_warning "  - Space to reclaim: $(format_bytes $before_size)"
        return 0
    fi

    # Remove logs older than retention period
    find "$LOG_DIR" -name "*.log" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true

    # Compress logs older than 1 day
    find "$LOG_DIR" -name "*.log" -type f -mtime +1 ! -name "*.gz" -exec gzip {} \; 2>/dev/null || true

    local after_size=$(get_disk_usage "$LOG_DIR")
    local reclaimed=$((before_size - after_size))

    log_success "Cleaned old logs, reclaimed: $(format_bytes $reclaimed)"
}

cleanup_application_logs() {
    log_info "Cleaning up application logs..."

    local app_log_dirs=(
        "/var/log/ai-platform"
        "${SCRIPT_DIR}/../../../logs"
    )

    local total_reclaimed=0

    for log_dir in "${app_log_dirs[@]}"; do
        if [ ! -d "$log_dir" ]; then
            continue
        fi

        local before_size=$(get_disk_usage "$log_dir")

        if [ "$DRY_RUN" = true ]; then
            log_warning "[DRY RUN] Would clean: $log_dir"
            continue
        fi

        # Remove logs older than retention period
        find "$log_dir" -name "*.log" -type f -mtime +$LOG_RETENTION_DAYS -delete 2>/dev/null || true

        # Compress old logs
        find "$log_dir" -name "*.log" -type f -mtime +1 ! -name "*.gz" -exec gzip {} \; 2>/dev/null || true

        local after_size=$(get_disk_usage "$log_dir")
        local reclaimed=$((before_size - after_size))
        total_reclaimed=$((total_reclaimed + reclaimed))
    done

    if [ $total_reclaimed -gt 0 ]; then
        log_success "Cleaned application logs, reclaimed: $(format_bytes $total_reclaimed)"
    fi
}

##############################################################################
# Report Functions
##############################################################################

generate_report() {
    local docker_space_before=$1
    local docker_space_after=$2

    cat <<EOF

==============================================================================
Resource Cleanup Report
==============================================================================
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Mode: $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "EXECUTE")
Aggressive: $([ "$AGGRESSIVE" = true ] && echo "YES" || echo "NO")

Docker Space:
  Before: $(format_bytes $docker_space_before)
  After:  $(format_bytes $docker_space_after)
  Saved:  $(format_bytes $((docker_space_before - docker_space_after)))

Disk Usage:
$(df -h / | tail -n1 | awk '{printf "  Total: %s\n  Used: %s (%s)\n  Available: %s\n", $2, $3, $5, $4}')

Log File: ${LOG_FILE}
==============================================================================

EOF
}

##############################################################################
# Main Function
##############################################################################

main() {
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --dry-run)
                DRY_RUN=true
                log_warning "Running in DRY RUN mode - no changes will be made"
                ;;
            --aggressive)
                AGGRESSIVE=true
                log_warning "Running in AGGRESSIVE mode - will remove old images"
                ;;
            --help)
                cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run       Show what would be done without executing
  --aggressive    Also remove old unused images (>$DOCKER_IMAGE_RETENTION_DAYS days)
  --help          Show this help message

Examples:
  $0                          # Normal cleanup
  $0 --dry-run                # Preview cleanup
  $0 --aggressive             # Aggressive cleanup
  $0 --dry-run --aggressive   # Preview aggressive cleanup
EOF
                exit 0
                ;;
        esac
    done

    # Initialize
    init_logging
    check_dependencies

    # Get initial Docker space usage
    local docker_space_before=$(docker system df -v 2>/dev/null | grep "Total" | awk '{print $4}' | sed 's/[^0-9.]//g' || echo "0")
    docker_space_before=$(echo "$docker_space_before * 1073741824" | bc | cut -d'.' -f1)

    # Run cleanup tasks
    log_info "Starting cleanup tasks..."

    cleanup_docker_containers
    cleanup_docker_images
    cleanup_docker_volumes
    cleanup_docker_networks
    cleanup_docker_build_cache

    cleanup_temp_files
    cleanup_old_logs
    cleanup_application_logs

    # Get final Docker space usage
    local docker_space_after=$(docker system df -v 2>/dev/null | grep "Total" | awk '{print $4}' | sed 's/[^0-9.]//g' || echo "0")
    docker_space_after=$(echo "$docker_space_after * 1073741824" | bc | cut -d'.' -f1)

    # Generate report
    generate_report "$docker_space_before" "$docker_space_after"

    log_success "Resource cleanup completed successfully"
}

# Execute main function
main "$@"
