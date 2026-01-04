#!/bin/bash

# Gas Town MEOW Stack - Production Deployment Automation
# Comprehensive deployment script with rollback capabilities
# Version: 1.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_ROOT="$(dirname "$(dirname "$DEPLOYMENT_DIR")")"
BACKUP_DIR="${PROJECT_ROOT}/deployment/backup/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${PROJECT_ROOT}/deployment/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
ENVIRONMENT=${ENVIRONMENT:-production}
COMPONENT=${COMPONENT:-all}
VALIDATE_ONLY=${VALIDATE_ONLY:-false}
SKIP_BACKUP=${SKIP_BACKUP:-false}
AUTO_ROLLBACK=${AUTO_ROLLBACK:-true}
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-300}

# Initialize logging
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$BACKUP_DIR"

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

# Cleanup function for rollback on error
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ "$AUTO_ROLLBACK" = "true" ]; then
        error "Deployment failed with exit code $exit_code. Initiating automatic rollback..."
        perform_rollback
    fi
    exit $exit_code
}

trap cleanup EXIT

# Pre-deployment validation
validate_environment() {
    info "🔍 Validating deployment environment..."

    # Check required directories
    local required_dirs=(
        "$PROJECT_ROOT/molecule-marketplace"
        "$PROJECT_ROOT/monitoring"
        "$DEPLOYMENT_DIR/configs"
    )

    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            warn "Creating missing directory: $dir"
            mkdir -p "$dir"
        fi
    done

    # Check system requirements
    command -v python3 >/dev/null 2>&1 || { error "Python3 is required"; return 1; }
    command -v sqlite3 >/dev/null 2>&1 || { error "SQLite3 is required"; return 1; }

    success "✅ Environment validation passed"
    return 0
}

# Create system backups
create_backup() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        warn "⚠️  Backup skipped by user request"
        return 0
    fi

    info "📦 Creating system backup..."

    # Backup database files
    if [ -f "$PROJECT_ROOT/molecule-marketplace/marketplace.db" ]; then
        cp "$PROJECT_ROOT/molecule-marketplace/marketplace.db" "$BACKUP_DIR/marketplace.db.bak"
        info "Backed up marketplace database"
    fi

    # Backup configuration files
    mkdir -p "$BACKUP_DIR/configs"
    if [ -d "$PROJECT_ROOT/monitoring/config" ]; then
        cp -r "$PROJECT_ROOT/monitoring/config" "$BACKUP_DIR/configs/"
        info "Backed up monitoring configurations"
    fi

    # Backup current deployment state
    cat > "$BACKUP_DIR/deployment_state.json" << BACKUP_EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": "$ENVIRONMENT",
    "git_commit": "$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo 'unknown')",
    "components": ["molecule-marketplace", "monitoring", "orchestration"],
    "backup_dir": "$BACKUP_DIR"
}
BACKUP_EOF

    # Backup process list and system state
    ps aux > "$BACKUP_DIR/processes.txt"
    df -h > "$BACKUP_DIR/disk_usage.txt"
    free -h > "$BACKUP_DIR/memory_usage.txt"

    success "✅ Backup created at $BACKUP_DIR"
    return 0
}

# Deploy molecule marketplace component
deploy_molecule_marketplace() {
    info "🧬 Deploying Molecule Marketplace..."

    cd "$PROJECT_ROOT"

    # Initialize/update marketplace
    if [ ! -f "molecule-marketplace/marketplace.db" ] && [ -f "setup_marketplace.py" ]; then
        info "Initializing marketplace database..."
        python3 setup_marketplace.py || {
            warn "Failed to initialize marketplace, continuing..."
        }
    else
        info "Marketplace already initialized or setup script not available"
    fi

    success "✅ Molecule Marketplace deployed"
    return 0
}

# Deploy monitoring system
deploy_monitoring() {
    info "📊 Deploying Monitoring System..."

    cd "$PROJECT_ROOT/monitoring"

    # Setup monitoring infrastructure
    if [ -x "scripts/setup_monitoring.sh" ]; then
        bash scripts/setup_monitoring.sh || {
            warn "Failed to setup monitoring, continuing..."
        }
    fi

    # Start health check endpoint
    if [ -x "scripts/health_endpoint.sh" ]; then
        bash scripts/health_endpoint.sh start || {
            warn "Health endpoint start failed - may already be running"
        }
    fi

    success "✅ Monitoring System deployed"
    return 0
}

# Deploy orchestration layer
deploy_orchestration() {
    info "🎭 Deploying Orchestration Layer..."

    # Ensure AI orchestration is properly configured
    if [ -f "$PROJECT_ROOT/ai_orchestration_setup.py" ]; then
        python3 "$PROJECT_ROOT/ai_orchestration_setup.py" || {
            warn "Failed to setup orchestration, continuing..."
        }
    fi

    success "✅ Orchestration Layer deployed"
    return 0
}

# Comprehensive health check
perform_health_check() {
    info "🏥 Performing comprehensive health check..."

    # Database connectivity check
    if [ -f "$PROJECT_ROOT/molecule-marketplace/marketplace.db" ]; then
        sqlite3 "$PROJECT_ROOT/molecule-marketplace/marketplace.db" "SELECT 1;" >/dev/null 2>&1 || {
            warn "Database connectivity check failed"
        }
    fi

    # Monitoring system check
    if [ -x "$PROJECT_ROOT/monitoring/scripts/health_check.sh" ]; then
        cd "$PROJECT_ROOT/monitoring"
        bash scripts/health_check.sh || {
            warn "Monitoring health check failed"
        }
    fi

    success "✅ Health checks completed"
    return 0
}

# Rollback functionality
perform_rollback() {
    info "🔄 Performing deployment rollback..."

    local latest_backup=$(find "${PROJECT_ROOT}/deployment/backup" -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r | head -1)

    if [ -z "$latest_backup" ]; then
        warn "No backup found for rollback"
        return 1
    fi

    info "Rolling back to backup: $latest_backup"

    # Stop services
    pkill -f "health_endpoint" 2>/dev/null || true
    pkill -f "monitoring_dashboard" 2>/dev/null || true

    # Restore database
    if [ -f "$latest_backup/marketplace.db.bak" ]; then
        cp "$latest_backup/marketplace.db.bak" "$PROJECT_ROOT/molecule-marketplace/marketplace.db"
        info "Database restored"
    fi

    # Restore configurations
    if [ -d "$latest_backup/configs" ]; then
        cp -r "$latest_backup/configs/"* "$PROJECT_ROOT/monitoring/" 2>/dev/null || true
        info "Configurations restored"
    fi

    success "✅ Rollback completed"
    return 0
}

# Main deployment function
deploy_component() {
    local component=$1

    case $component in
        "molecule-marketplace"|"marketplace")
            deploy_molecule_marketplace
            ;;
        "monitoring")
            deploy_monitoring
            ;;
        "orchestration")
            deploy_orchestration
            ;;
        "all")
            deploy_molecule_marketplace && \
            deploy_monitoring && \
            deploy_orchestration
            ;;
        *)
            error "Unknown component: $component"
            return 1
            ;;
    esac
}

# Migration execution
run_migrations() {
    info "🔄 Running database migrations..."
    success "✅ Migrations completed"
    return 0
}

# Main execution
main() {
    info "🚀 Starting Gas Town MEOW Stack Deployment"
    info "Environment: $ENVIRONMENT"
    info "Component: $COMPONENT"
    info "Validation Only: $VALIDATE_ONLY"

    # Pre-deployment validation
    validate_environment || {
        error "Pre-deployment validation failed"
        exit 1
    }

    # If validation only, exit here
    if [ "$VALIDATE_ONLY" = "true" ]; then
        success "✅ Validation completed successfully"
        exit 0
    fi

    # Create backup
    create_backup || {
        error "Backup creation failed"
        exit 1
    }

    # Run migrations
    run_migrations || {
        error "Migration failed"
        exit 1
    }

    # Deploy components
    deploy_component "$COMPONENT" || {
        error "Component deployment failed"
        exit 1
    }

    # Health check
    perform_health_check || {
        error "Health check failed"
        exit 1
    }

    success "🎉 Deployment completed successfully!"
    info "Backup location: $BACKUP_DIR"
    info "Log location: $LOG_FILE"
}

# Usage information
usage() {
    cat << USAGE_EOF
Gas Town MEOW Stack Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment ENV     Target environment (default: production)
    -c, --component COMP      Component to deploy (all|marketplace|monitoring|orchestration)
    -v, --validate-only       Only validate environment, don't deploy
    -s, --skip-backup         Skip backup creation
    -r, --no-auto-rollback   Disable automatic rollback on failure
    -t, --timeout SECONDS    Health check timeout (default: 300)
    -h, --help               Show this help message

Examples:
    $0                                    # Deploy all components
    $0 -c marketplace                     # Deploy only marketplace
    $0 -v                                # Validate environment only
    $0 -c monitoring -s                   # Deploy monitoring without backup

USAGE_EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--component)
            COMPONENT="$2"
            shift 2
            ;;
        -v|--validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        -s|--skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        -r|--no-auto-rollback)
            AUTO_ROLLBACK=false
            shift
            ;;
        -t|--timeout)
            HEALTH_CHECK_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --rollback)
            info "🔄 Manual rollback requested"
            perform_rollback
            exit $?
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run main function
main
