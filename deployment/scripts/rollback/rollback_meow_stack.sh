#!/bin/bash

# Gas Town MEOW Stack - Production Rollback System
# Comprehensive rollback script with safety checks
# Version: 1.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_ROOT="$(dirname "$(dirname "$DEPLOYMENT_DIR")")"
LOG_FILE="${PROJECT_ROOT}/deployment/logs/rollback_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
BACKUP_ID=""
FORCE_ROLLBACK=${FORCE_ROLLBACK:-false}
COMPONENT=${COMPONENT:-all}
CONFIRM_ROLLBACK=${CONFIRM_ROLLBACK:-true}

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

# List available backups
list_backups() {
    info "📋 Available backups:"
    local backup_dir="${PROJECT_ROOT}/deployment/backup"
    
    if [ ! -d "$backup_dir" ]; then
        error "No backup directory found"
        return 1
    fi

    local backups=($(find "$backup_dir" -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r))
    
    if [ ${#backups[@]} -eq 0 ]; then
        error "No backups found"
        return 1
    fi

    for i in "${!backups[@]}"; do
        local backup_path="${backups[$i]}"
        local backup_name=$(basename "$backup_path")
        local state_file="$backup_path/deployment_state.json"
        
        echo "[$((i+1))] $backup_name"
        
        if [ -f "$state_file" ]; then
            local timestamp=$(python3 -c "import json; print(json.load(open('$state_file'))['timestamp'])" 2>/dev/null || echo "unknown")
            local git_commit=$(python3 -c "import json; print(json.load(open('$state_file'))['git_commit'])" 2>/dev/null || echo "unknown")
            local git_branch=$(python3 -c "import json; print(json.load(open('$state_file'))['git_branch'])" 2>/dev/null || echo "unknown")
            local environment=$(python3 -c "import json; print(json.load(open('$state_file'))['environment'])" 2>/dev/null || echo "unknown")
            
            echo "    Time: $timestamp"
            echo "    Environment: $environment"
            echo "    Git: $git_branch @ ${git_commit:0:8}"
        fi
        echo
    done
}

# Get backup path by ID or auto-detect latest
get_backup_path() {
    local backup_dir="${PROJECT_ROOT}/deployment/backup"
    
    if [ -n "$BACKUP_ID" ]; then
        # Use specified backup ID
        local backup_path="$backup_dir/$BACKUP_ID"
        if [ -d "$backup_path" ]; then
            echo "$backup_path"
        else
            error "Backup ID not found: $BACKUP_ID"
            return 1
        fi
    else
        # Use latest backup
        local latest_backup=$(find "$backup_dir" -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r | head -1)
        if [ -n "$latest_backup" ]; then
            echo "$latest_backup"
        else
            error "No backups available"
            return 1
        fi
    fi
}

# Validate backup integrity
validate_backup() {
    local backup_path=$1
    info "🔍 Validating backup: $(basename "$backup_path")"
    
    # Check required files
    local required_files=(
        "deployment_state.json"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$backup_path/$file" ]; then
            error "Missing backup file: $file"
            return 1
        fi
    done
    
    # Check backup state
    local state_file="$backup_path/deployment_state.json"
    if ! python3 -c "import json; json.load(open('$state_file'))" >/dev/null 2>&1; then
        error "Invalid backup state file"
        return 1
    fi
    
    success "✅ Backup validation passed"
    return 0
}

# Confirm rollback action
confirm_action() {
    local backup_path=$1
    
    if [ "$CONFIRM_ROLLBACK" != "true" ] || [ "$FORCE_ROLLBACK" = "true" ]; then
        return 0
    fi
    
    local backup_name=$(basename "$backup_path")
    
    echo
    warn "⚠️  ROLLBACK WARNING ⚠️"
    echo "You are about to rollback to backup: $backup_name"
    echo "This will:"
    echo "  - Stop current services"
    echo "  - Restore database and configurations"
    echo "  - Potentially lose recent changes"
    echo
    
    read -p "Are you sure you want to proceed? (yes/no): " -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        info "Rollback cancelled by user"
        exit 0
    fi
}

# Stop running services
stop_services() {
    info "🛑 Stopping running services..."
    
    # Stop MEOW stack services
    local services=(
        "health_endpoint"
        "monitoring_dashboard"
        "marketplace_api"
        "orchestration_engine"
    )
    
    for service in "${services[@]}"; do
        if pgrep -f "$service" >/dev/null 2>&1; then
            info "Stopping $service..."
            pkill -f "$service" 2>/dev/null || true
            sleep 2
        fi
    done
    
    success "✅ Services stopped"
}

# Rollback database
rollback_database() {
    local backup_path=$1
    info "🗄️  Rolling back database..."
    
    # Rollback marketplace database
    if [ -f "$backup_path/marketplace.db.bak" ]; then
        local target_db="$PROJECT_ROOT/molecule-marketplace/marketplace.db"
        
        # Create current backup before rollback
        if [ -f "$target_db" ]; then
            cp "$target_db" "${target_db}.pre-rollback.$(date +%Y%m%d_%H%M%S)"
        fi
        
        cp "$backup_path/marketplace.db.bak" "$target_db"
        info "Marketplace database restored"
    fi
    
    success "✅ Database rollback completed"
}

# Rollback configurations
rollback_configurations() {
    local backup_path=$1
    info "⚙️  Rolling back configurations..."
    
    # Rollback monitoring configurations
    if [ -d "$backup_path/configs" ]; then
        # Backup current configs before rollback
        local current_config_backup="${PROJECT_ROOT}/monitoring/config.pre-rollback.$(date +%Y%m%d_%H%M%S)"
        if [ -d "$PROJECT_ROOT/monitoring/config" ]; then
            cp -r "$PROJECT_ROOT/monitoring/config" "$current_config_backup"
        fi
        
        # Restore from backup
        rm -rf "$PROJECT_ROOT/monitoring/config"
        cp -r "$backup_path/configs/config" "$PROJECT_ROOT/monitoring/"
        info "Monitoring configurations restored"
    fi
    
    success "✅ Configuration rollback completed"
}

# Rollback component-specific items
rollback_component() {
    local component=$1
    local backup_path=$2
    
    case $component in
        "molecule-marketplace"|"marketplace")
            rollback_database "$backup_path"
            ;;
        "monitoring")
            rollback_configurations "$backup_path"
            ;;
        "orchestration")
            info "Orchestration rollback completed (no persistent state)"
            ;;
        "all")
            rollback_database "$backup_path"
            rollback_configurations "$backup_path"
            ;;
        *)
            error "Unknown component: $component"
            return 1
            ;;
    esac
}

# Post-rollback health check
post_rollback_health_check() {
    info "🏥 Running post-rollback health check..."
    
    # Database connectivity
    if [ -f "$PROJECT_ROOT/molecule-marketplace/marketplace.db" ]; then
        sqlite3 "$PROJECT_ROOT/molecule-marketplace/marketplace.db" "SELECT 1;" >/dev/null 2>&1 || {
            warn "Database connectivity check failed"
        }
    fi
    
    # Configuration files
    if [ -f "$PROJECT_ROOT/monitoring/config/health_config.yaml" ]; then
        info "Monitoring configuration file exists"
    fi
    
    success "✅ Post-rollback health check completed"
}

# Restart services after rollback
restart_services() {
    info "🔄 Restarting services..."
    
    # Restart monitoring services
    if [ -x "$PROJECT_ROOT/monitoring/scripts/health_endpoint.sh" ]; then
        cd "$PROJECT_ROOT/monitoring"
        bash scripts/health_endpoint.sh start || {
            warn "Failed to restart health endpoint"
        }
    fi
    
    success "✅ Services restarted"
}

# Create rollback report
create_rollback_report() {
    local backup_path=$1
    local backup_name=$(basename "$backup_path")
    local report_file="${PROJECT_ROOT}/deployment/logs/rollback_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << REPORT_EOF
{
    "rollback_timestamp": "$(date -Iseconds)",
    "backup_used": "$backup_name",
    "backup_path": "$backup_path",
    "component": "$COMPONENT",
    "force_rollback": $FORCE_ROLLBACK,
    "rollback_successful": true,
    "git_state_after_rollback": {
        "commit": "$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
        "branch": "$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo 'unknown')"
    }
}
REPORT_EOF
    
    info "Rollback report created: $report_file"
}

# Main rollback execution
perform_rollback() {
    local backup_path
    backup_path=$(get_backup_path) || return 1
    
    info "🔄 Starting rollback process"
    info "Backup: $(basename "$backup_path")"
    info "Component: $COMPONENT"
    
    # Validate backup
    validate_backup "$backup_path" || return 1
    
    # Confirm action
    confirm_action "$backup_path"
    
    # Stop services
    stop_services
    
    # Perform component rollback
    rollback_component "$COMPONENT" "$backup_path" || return 1
    
    # Post-rollback health check
    post_rollback_health_check
    
    # Restart services
    restart_services
    
    # Create report
    create_rollback_report "$backup_path"
    
    success "🎉 Rollback completed successfully!"
    info "Log file: $LOG_FILE"
}

# Usage information
usage() {
    cat << USAGE_EOF
Gas Town MEOW Stack Rollback Script

Usage: $0 [OPTIONS]

Options:
    -b, --backup-id ID        Specific backup ID to rollback to (default: latest)
    -c, --component COMP      Component to rollback (all|marketplace|monitoring|orchestration)
    -f, --force              Force rollback without confirmation
    -n, --no-confirm         Skip confirmation prompt
    -l, --list               List available backups
    -h, --help               Show this help message

Examples:
    $0 -l                           # List available backups
    $0                              # Rollback all components to latest backup
    $0 -b 20241203_143022          # Rollback to specific backup
    $0 -c marketplace -f           # Force rollback marketplace only

USAGE_EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backup-id)
            BACKUP_ID="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_ROLLBACK=true
            CONFIRM_ROLLBACK=false
            shift
            ;;
        -n|--no-confirm)
            CONFIRM_ROLLBACK=false
            shift
            ;;
        -l|--list)
            list_backups
            exit 0
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

# Main execution
perform_rollback
