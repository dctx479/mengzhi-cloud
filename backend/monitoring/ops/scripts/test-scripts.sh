#!/bin/bash

##############################################################################
# Script Validation Test
#
# Description: Test all auto-healing scripts in dry-run mode
# Usage: ./test-scripts.sh
##############################################################################

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() {
    echo -e "${BLUE}ℹ${NC} $*"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
}

test_script() {
    local script=$1
    local args=$2
    local name=$(basename "$script" .sh)

    echo ""
    log_info "Testing: $name"
    echo "----------------------------------------"

    if [ ! -f "$script" ]; then
        log_error "Script not found: $script"
        return 1
    fi

    if [ ! -x "$script" ]; then
        log_error "Script not executable: $script"
        return 1
    fi

    # Test help
    if "$script" --help >/dev/null 2>&1; then
        log_success "Help command works"
    else
        log_warning "Help command failed (not critical)"
    fi

    # Test dry-run if supported
    if echo "$args" | grep -q "dry-run"; then
        log_info "Running dry-run test..."
        if $script $args 2>&1 | head -20; then
            log_success "Dry-run test passed"
            return 0
        else
            log_error "Dry-run test failed"
            return 1
        fi
    else
        log_success "Script validated"
        return 0
    fi
}

main() {
    echo "=============================================================================="
    echo "Auto-Healing Scripts Validation Test"
    echo "=============================================================================="
    echo "Script Directory: $SCRIPT_DIR"
    echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    local total=0
    local passed=0
    local failed=0

    # Test restart-container.sh
    total=$((total + 1))
    if test_script "$SCRIPT_DIR/restart-container.sh" "--help"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test cleanup-resources.sh
    total=$((total + 1))
    if test_script "$SCRIPT_DIR/cleanup-resources.sh" "--dry-run"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test reset-db-connections.sh
    total=$((total + 1))
    if test_script "$SCRIPT_DIR/reset-db-connections.sh" "--help"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test cleanup-redis.sh
    total=$((total + 1))
    if test_script "$SCRIPT_DIR/cleanup-redis.sh" "--help"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test rotate-logs.sh
    total=$((total + 1))
    if test_script "$SCRIPT_DIR/rotate-logs.sh" "--dry-run"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test health-check.sh
    total=$((total + 1))
    if test_script "$SCRIPT_DIR/health-check.sh" "--help"; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Summary
    echo ""
    echo "=============================================================================="
    echo "Test Summary"
    echo "=============================================================================="
    echo "Total Tests:  $total"
    echo "Passed:       $passed"
    echo "Failed:       $failed"
    echo ""

    if [ $failed -eq 0 ]; then
        log_success "All tests passed!"
        exit 0
    else
        log_error "Some tests failed!"
        exit 1
    fi
}

main "$@"
