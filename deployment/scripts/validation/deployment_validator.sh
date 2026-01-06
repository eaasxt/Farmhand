#!/bin/bash

# Gas Town MEOW Stack - Deployment Validation Suite
# Comprehensive pre and post-deployment validation
# Version: 1.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_ROOT="$(dirname "$(dirname "$DEPLOYMENT_DIR")")"
LOG_FILE="${PROJECT_ROOT}/deployment/logs/validation_$(date +%Y%m%d_%H%M%S).log"

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
}

error() {
    log "ERROR" "${RED}$*${NC}"
}

success() {
    log "SUCCESS" "${GREEN}$*${NC}"
}

# Track validation results
VALIDATION_PASSED=0
VALIDATION_FAILED=0
VALIDATION_WARNINGS=0

# Add validation result
add_result() {
    local status=$1
    case $status in
        "PASS")
            VALIDATION_PASSED=$((VALIDATION_PASSED + 1))
            ;;
        "FAIL")
            VALIDATION_FAILED=$((VALIDATION_FAILED + 1))
            ;;
        "WARN")
            VALIDATION_WARNINGS=$((VALIDATION_WARNINGS + 1))
            ;;
    esac
}

# Validate system requirements
validate_system_requirements() {
    info "🔧 Validating system requirements..."
    
    # Check required commands
    local required_commands=(
        "python3"
        "sqlite3"
        "curl"
        "jq"
        "git"
    )
    
    for cmd in "${required_commands[@]}"; do
        if command -v "$cmd" >/dev/null 2>&1; then
            success "✅ Command available: $cmd"
            add_result "PASS"
        else
            error "❌ Command missing: $cmd"
            add_result "FAIL"
        fi
    done
    
    # Check Python version
    if python3 --version | grep -qE "Python 3\.(9|1[0-9])"; then
        success "✅ Python version acceptable"
        add_result "PASS"
    else
        warn "⚠️  Python version may be incompatible"
        add_result "WARN"
    fi
    
    # Check disk space
    local available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local required_space=1048576  # 1GB in KB
    
    if [ "$available_space" -gt "$required_space" ]; then
        success "✅ Sufficient disk space available"
        add_result "PASS"
    else
        error "❌ Insufficient disk space"
        add_result "FAIL"
    fi
    
    # Check memory
    local available_memory=$(free | awk '/^Mem:/ {print $7}')
    local required_memory=524288  # 512MB in KB
    
    if [ "$available_memory" -gt "$required_memory" ]; then
        success "✅ Sufficient memory available"
        add_result "PASS"
    else
        warn "⚠️  Limited memory available"
        add_result "WARN"
    fi
}

# Validate file structure
validate_file_structure() {
    info "📁 Validating file structure..."
    
    # Check required directories
    local required_dirs=(
        "$PROJECT_ROOT/molecule-marketplace"
        "$PROJECT_ROOT/monitoring"
        "$PROJECT_ROOT/deployment/scripts"
        "$PROJECT_ROOT/deployment/configs"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            success "✅ Directory exists: $dir"
            add_result "PASS"
        else
            error "❌ Directory missing: $dir"
            add_result "FAIL"
        fi
    done
    
    # Check required files
    local required_files=(
        "$PROJECT_ROOT/requirements.txt"
        "$PROJECT_ROOT/setup_marketplace.py"
        "$PROJECT_ROOT/deployment/scripts/deploy/deploy_meow_stack.sh"
        "$PROJECT_ROOT/deployment/scripts/rollback/rollback_meow_stack.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            success "✅ File exists: $file"
            add_result "PASS"
            
            # Check if script files are executable
            if [[ "$file" == *.sh ]]; then
                if [ -x "$file" ]; then
                    success "✅ Script is executable: $file"
                    add_result "PASS"
                else
                    error "❌ Script not executable: $file"
                    add_result "FAIL"
                fi
            fi
        else
            error "❌ File missing: $file"
            add_result "FAIL"
        fi
    done
    
    # Check configuration files
    local config_files=(
        "$PROJECT_ROOT/monitoring/config/health_config.yaml"
        "$PROJECT_ROOT/monitoring/alerts/alert_rules.yaml"
    )
    
    for config in "${config_files[@]}"; do
        if [ -f "$config" ]; then
            success "✅ Configuration exists: $config"
            add_result "PASS"
            
            # Validate YAML syntax
            if python3 -c "import yaml; yaml.safe_load(open('$config'))" 2>/dev/null; then
                success "✅ Valid YAML syntax: $config"
                add_result "PASS"
            else
                error "❌ Invalid YAML syntax: $config"
                add_result "FAIL"
            fi
        else
            warn "⚠️  Configuration missing: $config"
            add_result "WARN"
        fi
    done
}

# Validate Python dependencies
validate_python_dependencies() {
    info "🐍 Validating Python dependencies..."
    
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        # Check if all dependencies can be imported
        while IFS= read -r requirement; do
            # Skip empty lines and comments
            [[ -z "$requirement" || "$requirement" == \#* ]] && continue
            
            # Extract package name (before ==, >=, etc.)
            package=$(echo "$requirement" | sed 's/[>=<].*//' | sed 's/\[.*//')
            
            if python3 -c "import $package" 2>/dev/null; then
                success "✅ Python package available: $package"
                add_result "PASS"
            else
                warn "⚠️  Python package missing: $package"
                add_result "WARN"
            fi
        done < "$PROJECT_ROOT/requirements.txt"
    else
        warn "⚠️  No requirements.txt found"
        add_result "WARN"
    fi
    
    # Test critical imports
    local critical_imports=(
        "sqlite3"
        "json"
        "yaml"
        "os"
        "sys"
    )
    
    for import in "${critical_imports[@]}"; do
        if python3 -c "import $import" 2>/dev/null; then
            success "✅ Critical import available: $import"
            add_result "PASS"
        else
            error "❌ Critical import missing: $import"
            add_result "FAIL"
        fi
    done
}

# Validate database connectivity
validate_database() {
    info "🗄️  Validating database connectivity..."
    
    local db_file="$PROJECT_ROOT/molecule-marketplace/marketplace.db"
    
    if [ -f "$db_file" ]; then
        # Test database connectivity
        if sqlite3 "$db_file" "SELECT 1;" >/dev/null 2>&1; then
            success "✅ Database connectivity OK"
            add_result "PASS"
            
            # Test basic queries
            local table_count=$(sqlite3 "$db_file" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
            if [ "$table_count" -gt 0 ]; then
                success "✅ Database has tables ($table_count)"
                add_result "PASS"
            else
                warn "⚠️  Database has no tables"
                add_result "WARN"
            fi
        else
            error "❌ Database connectivity failed"
            add_result "FAIL"
        fi
    else
        if [ "$VALIDATION_TYPE" = "pre" ]; then
            info "ℹ️  Database will be created during deployment"
            add_result "PASS"
        else
            error "❌ Database file missing after deployment"
            add_result "FAIL"
        fi
    fi
}

# Validate service health
validate_service_health() {
    info "🏥 Validating service health..."
    
    # Check for running processes
    local meow_processes=(
        "health_endpoint"
        "monitoring_dashboard" 
        "marketplace_api"
    )
    
    for process in "${meow_processes[@]}"; do
        if pgrep -f "$process" >/dev/null 2>&1; then
            success "✅ Service running: $process"
            add_result "PASS"
        else
            if [ "$VALIDATION_TYPE" = "post" ]; then
                warn "⚠️  Service not running: $process"
                add_result "WARN"
            else
                info "ℹ️  Service will be started during deployment: $process"
                add_result "PASS"
            fi
        fi
    done
    
    # Test health endpoints if this is post-deployment validation
    if [ "$VALIDATION_TYPE" = "post" ]; then
        local health_endpoints=(
            "http://localhost:8000/health"
            "http://localhost:8080/health"
            "http://localhost:9090/health"
        )
        
        for endpoint in "${health_endpoints[@]}"; do
            if curl -sf "$endpoint" >/dev/null 2>&1; then
                success "✅ Health endpoint responsive: $endpoint"
                add_result "PASS"
            else
                warn "⚠️  Health endpoint not responsive: $endpoint"
                add_result "WARN"
            fi
        done
    fi
}

# Validate network connectivity
validate_network() {
    info "🌐 Validating network connectivity..."
    
    # Test external connectivity (for updates, etc.)
    if curl -sf "https://httpbin.org/get" >/dev/null 2>&1; then
        success "✅ External network connectivity OK"
        add_result "PASS"
    else
        warn "⚠️  External network connectivity failed"
        add_result "WARN"
    fi
    
    # Test localhost connectivity
    if curl -sf "http://localhost" >/dev/null 2>&1; then
        success "✅ Localhost connectivity OK"
        add_result "PASS"
    else
        info "ℹ️  No localhost service running (expected for pre-deployment)"
        add_result "PASS"
    fi
    
    # Check for port conflicts
    local required_ports=(
        8000
        8001
        8080
        9090
    )
    
    for port in "${required_ports[@]}"; do
        if lsof -ti:$port >/dev/null 2>&1; then
            if [ "$VALIDATION_TYPE" = "pre" ]; then
                warn "⚠️  Port $port is already in use"
                add_result "WARN"
            else
                info "ℹ️  Port $port is in use (expected for post-deployment)"
                add_result "PASS"
            fi
        else
            if [ "$VALIDATION_TYPE" = "pre" ]; then
                success "✅ Port $port is available"
                add_result "PASS"
            else
                warn "⚠️  Port $port is not in use"
                add_result "WARN"
            fi
        fi
    done
}

# Validate security
validate_security() {
    info "🔒 Validating security configuration..."
    
    # Check file permissions
    local sensitive_files=(
        "$PROJECT_ROOT/deployment/scripts/deploy/deploy_meow_stack.sh"
        "$PROJECT_ROOT/deployment/scripts/rollback/rollback_meow_stack.sh"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [ -f "$file" ]; then
            local perms=$(stat -c "%a" "$file")
            if [[ "$perms" =~ ^[0-7][0-7]5$ ]]; then
                success "✅ Secure permissions on: $file ($perms)"
                add_result "PASS"
            else
                warn "⚠️  Potentially insecure permissions on: $file ($perms)"
                add_result "WARN"
            fi
        fi
    done
    
    # Check for sensitive data in logs
    if find "$PROJECT_ROOT" -name "*.log" -type f -exec grep -l -i "password\|secret\|key\|token" {} \; 2>/dev/null | head -1 | grep -q .; then
        error "❌ Sensitive data found in log files"
        add_result "FAIL"
    else
        success "✅ No sensitive data in log files"
        add_result "PASS"
    fi
    
    # Check environment variables for secrets
    if env | grep -qiE "(password|secret|key|token).*=" 2>/dev/null; then
        warn "⚠️  Potential secrets in environment variables"
        add_result "WARN"
    else
        success "✅ No obvious secrets in environment"
        add_result "PASS"
    fi
}

# Generate validation report
generate_report() {
    local total_checks=$((VALIDATION_PASSED + VALIDATION_FAILED + VALIDATION_WARNINGS))
    local report_file="${PROJECT_ROOT}/deployment/logs/validation_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << REPORT_EOF
{
    "validation_timestamp": "$(date -Iseconds)",
    "validation_type": "$VALIDATION_TYPE",
    "environment": "$ENVIRONMENT",
    "results": {
        "total_checks": $total_checks,
        "passed": $VALIDATION_PASSED,
        "failed": $VALIDATION_FAILED,
        "warnings": $VALIDATION_WARNINGS,
        "success_rate": $(( (VALIDATION_PASSED * 100) / (total_checks > 0 ? total_checks : 1) ))
    },
    "deployment_ready": $([ $VALIDATION_FAILED -eq 0 ] && echo "true" || echo "false"),
    "strict_mode": $STRICT_MODE
}
REPORT_EOF
    
    info "📋 Validation report created: $report_file"
}

# Print summary
print_summary() {
    local total_checks=$((VALIDATION_PASSED + VALIDATION_FAILED + VALIDATION_WARNINGS))
    
    echo
    info "📊 VALIDATION SUMMARY"
    info "===================="
    info "Total Checks: $total_checks"
    success "Passed: $VALIDATION_PASSED"
    error "Failed: $VALIDATION_FAILED"
    warn "Warnings: $VALIDATION_WARNINGS"
    
    if [ $VALIDATION_FAILED -eq 0 ]; then
        success "🎉 All critical validations passed!"
        if [ $VALIDATION_WARNINGS -gt 0 ]; then
            warn "⚠️  $VALIDATION_WARNINGS warnings detected - review recommended"
        fi
        echo
        success "✅ DEPLOYMENT READY"
        return 0
    else
        error "❌ $VALIDATION_FAILED critical validation(s) failed"
        echo
        error "🚫 DEPLOYMENT NOT READY"
        if [ "$STRICT_MODE" = "true" ]; then
            return 1
        else
            warn "Continuing due to non-strict mode"
            return 0
        fi
    fi
}

# Main validation execution
main() {
    info "🔍 Starting $VALIDATION_TYPE-deployment validation"
    info "Environment: $ENVIRONMENT"
    info "Strict Mode: $STRICT_MODE"
    echo
    
    validate_system_requirements
    validate_file_structure
    validate_python_dependencies
    validate_database
    validate_service_health
    validate_network
    validate_security
    
    generate_report
    print_summary
}

# Usage information
usage() {
    cat << USAGE_EOF
Gas Town MEOW Stack - Deployment Validator

Usage: $0 [OPTIONS]

Options:
    -t, --type TYPE           Validation type (pre|post) - default: pre
    -e, --environment ENV     Target environment - default: production
    -s, --strict             Enable strict mode (fail on warnings)
    --timeout SECONDS        Validation timeout - default: 60
    -h, --help               Show this help message

Examples:
    $0                                # Pre-deployment validation
    $0 -t post                        # Post-deployment validation
    $0 -t pre -e staging              # Staging pre-deployment validation
    $0 -t post -s                     # Strict post-deployment validation

USAGE_EOF
}

# Parse command line arguments
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
        -s|--strict)
            STRICT_MODE=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
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

# Validate arguments
if [[ ! "$VALIDATION_TYPE" =~ ^(pre|post)$ ]]; then
    error "Invalid validation type: $VALIDATION_TYPE"
    usage
    exit 1
fi

# Execute main function with timeout
timeout "$TIMEOUT" main || {
    error "Validation timed out after $TIMEOUT seconds"
    exit 1
}
