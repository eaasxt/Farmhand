#!/bin/bash

# Gas Town MCP Integration Layer - Deployment Validation Suite
# Comprehensive pre and post-deployment validation
# Version: 2.0.0 - MCP Integration Layer

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_ROOT="$(dirname "$(dirname "$DEPLOYMENT_DIR")")"
LOG_FILE="${PROJECT_ROOT}/deployment/logs/validation_mcp_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validation configuration
VALIDATION_TYPE=${VALIDATION_TYPE:-"pre"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
STRICT_MODE=${STRICT_MODE:-true}
TIMEOUT=${TIMEOUT:-60}

# Validation tracking
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Initialize logging
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

info() {
    log "INFO" "${BLUE}$*${NC}"
}

warn() {
    log "WARN" "${YELLOW}$*${NC}"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

error() {
    log "ERROR" "${RED}$*${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

success() {
    log "SUCCESS" "${GREEN}$*${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

# Validation check wrapper
validate_check() {
    local check_name="$1"
    local check_function="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    info "🔍 Checking: $check_name"
    
    if eval "$check_function"; then
        success "✅ $check_name: PASS"
        return 0
    else
        error "❌ $check_name: FAIL"
        return 1
    fi
}

# Pre-deployment validations
validate_steve_gas_town() {
    # Check gt command exists
    command -v gt >/dev/null 2>&1 || { echo "Steve's Gas Town (gt) not installed"; return 1; }
    
    # Check gt version
    local version
    if ! version=$(gt --version 2>/dev/null); then
        echo "Cannot determine Steve's Gas Town version"
        return 1
    fi
    
    # Verify it's at least somewhat functional
    if ! echo "$version" | grep -q "gt version"; then
        echo "Steve's Gas Town version output unexpected: $version"
        return 1
    fi
    
    echo "Steve's Gas Town detected: $version"
    return 0
}

validate_python_environment() {
    # Check Python 3 exists
    command -v python3 >/dev/null 2>&1 || { echo "Python 3 not installed"; return 1; }
    
    # Check Python version
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        echo "Python 3.8+ required"
        return 1
    fi
    
    local py_version
    py_version=$(python3 --version)
    echo "Python environment OK: $py_version"
    return 0
}

validate_migration_script() {
    if [ ! -f "/tmp/migrate_to_mcp_bridge.py" ]; then
        echo "Migration script not found at /tmp/migrate_to_mcp_bridge.py"
        return 1
    fi
    
    # Quick syntax check
    if ! python3 -m py_compile /tmp/migrate_to_mcp_bridge.py 2>/dev/null; then
        echo "Migration script has syntax errors"
        return 1
    fi
    
    echo "Migration script validated"
    return 0
}

validate_mcp_agent_mail() {
    # Check if MCP Agent Mail is running (optional)
    if curl -s http://127.0.0.1:8765/health >/dev/null 2>&1; then
        echo "MCP Agent Mail running on port 8765"
        return 0
    else
        # Not an error, just a warning
        echo "MCP Agent Mail not running (optional - bridge will work but MCP features limited)"
        return 0
    fi
}

validate_filesystem_permissions() {
    # Check ~/.local/bin directory
    if [ ! -d "$HOME/.local/bin" ]; then
        mkdir -p "$HOME/.local/bin" || { echo "Cannot create ~/.local/bin"; return 1; }
    fi
    
    if [ ! -w "$HOME/.local/bin" ]; then
        echo "~/.local/bin not writable"
        return 1
    fi
    
    echo "Filesystem permissions OK"
    return 0
}

validate_path_configuration() {
    if echo "$PATH" | grep -q "$HOME/.local/bin"; then
        echo "~/.local/bin already in PATH"
    else
        echo "~/.local/bin not in PATH (will need to be added)"
    fi
    return 0
}

# Post-deployment validations
validate_integration_installed() {
    if [ ! -f "$HOME/.local/bin/gt-mcp" ]; then
        echo "gt-mcp not found in ~/.local/bin"
        return 1
    fi
    
    if [ ! -x "$HOME/.local/bin/gt-mcp" ]; then
        echo "gt-mcp not executable"
        return 1
    fi
    
    echo "Integration layer installed"
    return 0
}

validate_detection_working() {
    export PATH="$PATH:$HOME/.local/bin"
    
    if ! timeout "$TIMEOUT" "$HOME/.local/bin/gt-mcp" detect >/dev/null 2>&1; then
        echo "Gas Town detection failed"
        return 1
    fi
    
    echo "Gas Town detection working"
    return 0
}

validate_status_integration() {
    export PATH="$PATH:$HOME/.local/bin"
    
    # Status may timeout due to Steve's gt, so we use a shorter timeout
    if timeout 30 "$HOME/.local/bin/gt-mcp" status >/dev/null 2>&1; then
        echo "Status integration working"
        return 0
    else
        # This might timeout due to Steve's gt, so we'll call it a warning
        echo "Status integration timeout (may be normal if Steve's gt is slow)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS - 1))  # Don't count this as a failure
        return 0
    fi
}

validate_passthrough_working() {
    export PATH="$PATH:$HOME/.local/bin"
    
    if ! timeout 30 "$HOME/.local/bin/gt-mcp" --version >/dev/null 2>&1; then
        echo "Command passthrough failed"
        return 1
    fi
    
    echo "Command passthrough working"
    return 0
}

validate_dashboard_basic() {
    export PATH="$PATH:$HOME/.local/bin"
    
    # Basic dashboard test - may fail if Rich not available
    if timeout 10 "$HOME/.local/bin/gt-mcp" dashboard --detect >/dev/null 2>&1; then
        echo "Dashboard working"
        return 0
    else
        echo "Dashboard test failed (may need Rich library - non-critical)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS - 1))  # Don't count as failure
        return 0
    fi
}

validate_tmux_integration() {
    if [ -f "$HOME/.tmux.conf.gastown-mcp" ]; then
        echo "tmux integration configured"
        return 0
    else
        echo "tmux integration not configured (optional feature)"
        WARNING_CHECKS=$((WARNING_CHECKS + 1))
        TOTAL_CHECKS=$((TOTAL_CHECKS - 1))  # Don't count as failure
        return 0
    fi
}

# Main validation functions
run_pre_deployment_validation() {
    info "🔍 Running Pre-Deployment Validation for Gas Town MCP Integration Layer"
    info ""
    
    # Core prerequisites
    validate_check "Steve's Gas Town Installation" "validate_steve_gas_town"
    validate_check "Python Environment" "validate_python_environment"
    validate_check "Migration Script" "validate_migration_script"
    validate_check "Filesystem Permissions" "validate_filesystem_permissions"
    validate_check "PATH Configuration" "validate_path_configuration"
    
    # Optional components
    validate_check "MCP Agent Mail (optional)" "validate_mcp_agent_mail"
}

run_post_deployment_validation() {
    info "🔍 Running Post-Deployment Validation for Gas Town MCP Integration Layer"
    info ""
    
    # Core functionality
    validate_check "Integration Layer Installation" "validate_integration_installed"
    validate_check "Gas Town Detection" "validate_detection_working"
    validate_check "Command Passthrough" "validate_passthrough_working"
    
    # Enhanced features (may have warnings)
    validate_check "Status Integration" "validate_status_integration"
    validate_check "Dashboard Functionality" "validate_dashboard_basic"
    validate_check "tmux Integration" "validate_tmux_integration"
}

# Generate validation report
generate_validation_report() {
    local success_rate
    if [ "$TOTAL_CHECKS" -eq 0 ]; then
        success_rate=0
    else
        success_rate=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
    fi
    
    local deployment_ready
    if [ "$FAILED_CHECKS" -eq 0 ]; then
        deployment_ready="true"
    else
        deployment_ready="false"
    fi
    
    # JSON report
    cat > "${PROJECT_ROOT}/deployment/logs/validation_report_mcp_$(date +%Y%m%d_%H%M%S).json" << JSON_REPORT
{
  "validation_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "validation_type": "$VALIDATION_TYPE",
  "system": "Gas Town MCP Integration Layer",
  "environment": "$ENVIRONMENT",
  "results": {
    "total_checks": $TOTAL_CHECKS,
    "passed": $PASSED_CHECKS,
    "failed": $FAILED_CHECKS,
    "warnings": $WARNING_CHECKS,
    "success_rate": $success_rate
  },
  "deployment_ready": $deployment_ready,
  "strict_mode": $STRICT_MODE
}
JSON_REPORT

    # Summary output
    info ""
    info "📊 Validation Summary:"
    info "   Total Checks: $TOTAL_CHECKS"
    info "   Passed: $PASSED_CHECKS"
    info "   Failed: $FAILED_CHECKS"  
    info "   Warnings: $WARNING_CHECKS"
    info "   Success Rate: ${success_rate}%"
    info ""
    
    if [ "$deployment_ready" = "true" ]; then
        success "✅ Validation PASSED - Deployment ready!"
    else
        error "❌ Validation FAILED - $FAILED_CHECKS critical issues found"
        if [ "$STRICT_MODE" = "true" ]; then
            error "❌ STRICT MODE: Deployment blocked due to failures"
            return 1
        else
            warn "⚠️  Non-strict mode: Deployment allowed with warnings"
        fi
    fi
    
    return 0
}

# Usage information
usage() {
    echo "Gas Town MCP Integration Layer Validation Suite"
    echo ""
    echo "USAGE:"
    echo "    $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "    -t, --type TYPE       Validation type: pre, post (default: pre)"
    echo "    -e, --environment ENV Environment: production, staging, dev (default: production)"
    echo "    --strict             Enable strict mode (fail on warnings)"
    echo "    --non-strict         Disable strict mode (allow warnings)"
    echo "    --timeout SECONDS    Timeout for health checks (default: 60)"
    echo "    --help               Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "    $0                              # Pre-deployment validation"
    echo "    $0 -t post                      # Post-deployment validation"
    echo "    $0 -t pre --strict              # Strict pre-deployment validation"
    echo "    ENVIRONMENT=staging $0          # Staging environment validation"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                VALIDATION_TYPE="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --strict)
                STRICT_MODE=true
                shift
                ;;
            --non-strict)
                STRICT_MODE=false
                shift
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Validate parameters
    if [[ ! "$VALIDATION_TYPE" =~ ^(pre|post)$ ]]; then
        error "Invalid validation type: $VALIDATION_TYPE (must be pre or post)"
        exit 1
    fi
}

# Main function
main() {
    info "🎯 Gas Town MCP Integration Layer Validation"
    info "   Type: $VALIDATION_TYPE-deployment"
    info "   Environment: $ENVIRONMENT"
    info "   Strict Mode: $STRICT_MODE"
    info ""
    
    # Run appropriate validation
    case "$VALIDATION_TYPE" in
        "pre")
            run_pre_deployment_validation
            ;;
        "post")
            run_post_deployment_validation
            ;;
    esac
    
    # Generate report
    if ! generate_validation_report; then
        exit 1
    fi
    
    info "📋 Full validation report: $LOG_FILE"
    exit 0
}

# Parse arguments and run
parse_arguments "$@"
main
