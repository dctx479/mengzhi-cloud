#!/bin/bash

##############################################################################
# Container Restart Script
#
# Description: Gracefully restart Docker containers with health checks and rollback
# Usage: ./restart-container.sh <container_name> [--dry-run]
# Author: AI Platform Ops Team
# Version: 1.0.0
##############################################################################

set -euo pipefail

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_DIR="/var/log/ai-platform/ops"
readonly LOG_FILE="${LOG_DIR}/restart-container-$(date +%Y%m%d).log"
readonly HEALTH_CHECK_TIMEOUT=30
readonly HEALTH_CHECK_INTERVAL=5
readonly MAX_RETRIES=3

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Dry run mode
DRY_RUN=false

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

##############################################################################
# Helper Functions
##############################################################################

init_logging() {
    mkdir -p "${LOG_DIR}"
    log_info "Starting container restart script"
    log_info "Log file: ${LOG_FILE}"
}

check_dependencies() {
    local missing_deps=()

    for cmd in docker jq curl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi
}

validate_container() {
    local container=$1

    if ! docker inspect "$container" &> /dev/null; then
        log_error "Container '$container' does not exist"
        return 1
    fi

    return 0
}

get_container_status() {
    local container=$1
    docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown"
}

get_container_health() {
    local container=$1
    docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none"
}

get_container_info() {
    local container=$1

    cat <<EOF
Container Information:
  Name: $container
  Status: $(get_container_status "$container")
  Health: $(get_container_health "$container")
  Image: $(docker inspect --format='{{.Config.Image}}' "$container")
  Created: $(docker inspect --format='{{.Created}}' "$container")
  RestartCount: $(docker inspect --format='{{.RestartCount}}' "$container")
EOF
}

backup_container_state() {
    local container=$1
    local backup_file="${LOG_DIR}/container-state-${container}-$(date +%Y%m%d-%H%M%S).json"

    log_info "Backing up container state to: $backup_file"
    docker inspect "$container" > "$backup_file"
    echo "$backup_file"
}

check_health() {
    local container=$1
    local timeout=$2
    local elapsed=0

    log_info "Checking health status (timeout: ${timeout}s)..."

    while [ $elapsed -lt $timeout ]; do
        local status=$(get_container_status "$container")
        local health=$(get_container_health "$container")

        if [ "$status" = "running" ]; then
            if [ "$health" = "healthy" ] || [ "$health" = "none" ]; then
                log_success "Container is healthy"
                return 0
            fi
        fi

        echo -n "."
        sleep $HEALTH_CHECK_INTERVAL
        elapsed=$((elapsed + HEALTH_CHECK_INTERVAL))
    done

    echo ""
    log_error "Health check failed after ${timeout}s"
    return 1
}

stop_container() {
    local container=$1

    log_info "Stopping container: $container"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would execute: docker stop $container"
        return 0
    fi

    if docker stop "$container" --time=30; then
        log_success "Container stopped successfully"
        return 0
    else
        log_error "Failed to stop container"
        return 1
    fi
}

start_container() {
    local container=$1

    log_info "Starting container: $container"

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would execute: docker start $container"
        return 0
    fi

    if docker start "$container"; then
        log_success "Container started successfully"
        return 0
    else
        log_error "Failed to start container"
        return 1
    fi
}

restart_container() {
    local container=$1
    local retry_count=0

    while [ $retry_count -lt $MAX_RETRIES ]; do
        log_info "Restart attempt $((retry_count + 1))/$MAX_RETRIES"

        # Stop container
        if ! stop_container "$container"; then
            retry_count=$((retry_count + 1))
            sleep 5
            continue
        fi

        # Wait a moment
        sleep 2

        # Start container
        if ! start_container "$container"; then
            retry_count=$((retry_count + 1))
            sleep 5
            continue
        fi

        # Check health
        if [ "$DRY_RUN" = false ]; then
            if check_health "$container" $HEALTH_CHECK_TIMEOUT; then
                log_success "Container restarted and healthy"
                return 0
            else
                log_warning "Container started but health check failed"
                retry_count=$((retry_count + 1))
                sleep 5
                continue
            fi
        else
            log_warning "[DRY RUN] Skipping health check"
            return 0
        fi
    done

    log_error "Failed to restart container after $MAX_RETRIES attempts"
    return 1
}

rollback_container() {
    local container=$1
    local backup_file=$2

    log_warning "Initiating rollback..."

    if [ "$DRY_RUN" = true ]; then
        log_warning "[DRY RUN] Would restore container from backup: $backup_file"
        return 0
    fi

    # Try to start the container if it's stopped
    if [ "$(get_container_status "$container")" != "running" ]; then
        if docker start "$container"; then
            log_success "Container started during rollback"
            return 0
        fi
    fi

    log_warning "Rollback completed with warnings"
    return 1
}

generate_report() {
    local container=$1
    local status=$2
    local backup_file=$3

    cat <<EOF

==============================================================================
Container Restart Report
==============================================================================
Container: $container
Status: $status
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Backup File: $backup_file

$(get_container_info "$container")

Log File: ${LOG_FILE}
==============================================================================

EOF
}

##############################################################################
# Main Function
##############################################################################

main() {
    # Parse arguments
    if [ $# -lt 1 ]; then
        cat <<EOF
Usage: $0 <container_name> [--dry-run]

Options:
  --dry-run    Show what would be done without executing

Examples:
  $0 ai-platform-backend
  $0 ai-platform-backend --dry-run
EOF
        exit 1
    fi

    local container=$1

    if [ "${2:-}" = "--dry-run" ]; then
        DRY_RUN=true
        log_warning "Running in DRY RUN mode - no changes will be made"
    fi

    # Initialize
    init_logging
    check_dependencies

    # Validate container
    if ! validate_container "$container"; then
        exit 1
    fi

    # Show initial status
    log_info "Initial container status:"
    get_container_info "$container"

    # Backup state
    local backup_file=$(backup_container_state "$container")

    # Restart container
    if restart_container "$container"; then
        generate_report "$container" "SUCCESS" "$backup_file"
        log_success "Container restart completed successfully"
        exit 0
    else
        log_error "Container restart failed"

        # Attempt rollback
        if rollback_container "$container" "$backup_file"; then
            generate_report "$container" "FAILED (Rolled Back)" "$backup_file"
            log_warning "Rollback completed"
            exit 1
        else
            generate_report "$container" "FAILED (Rollback Incomplete)" "$backup_file"
            log_error "Rollback failed - manual intervention required"
            exit 2
        fi
    fi
}

# Execute main function
main "$@"
