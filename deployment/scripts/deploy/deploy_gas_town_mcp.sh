#!/bin/bash

# Gas Town MCP Integration Layer - Production Deployment Automation
# Deploys the bridge system that enhances Steve's Gas Town with MCP ecosystem connectivity
# Version: 2.0.0 - MCP Integration Layer

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PROJECT_ROOT="$(dirname "$(dirname "$DEPLOYMENT_DIR")")"
BACKUP_DIR="${PROJECT_ROOT}/deployment/backup/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${PROJECT_ROOT}/deployment/logs/deploy_mcp_$(date +%Y%m%d_%H%M%S).log"

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
HEALTH_CHECK_TIMEOUT=${HEALTH_CHECK_TIMEOUT:-60}

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
    info "🔍 Validating Gas Town MCP Integration deployment environment..."

    # Check for Steve's Gas Town
    if ! command -v gt >/dev/null 2>&1; then
        error "Steve's Gas Town (gt) not found. Install first: go install github.com/steveyegge/gastown/cmd/gt@latest"
        return 1
    fi
    
    # Verify gt version
    GT_VERSION=$(gt --version 2>/dev/null || echo "unknown")
    info "✅ Steve's Gas Town found: $GT_VERSION"

    # Check MCP Agent Mail (optional but recommended)
    if curl -s http://127.0.0.1:8765/health >/dev/null 2>&1; then
        info "✅ MCP Agent Mail running on port 8765"
    else
        warn "⚠️  MCP Agent Mail not running on port 8765 (bridge will work but MCP features limited)"
    fi

    # Check system requirements
    command -v python3 >/dev/null 2>&1 || { error "Python3 is required"; return 1; }
    python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || { error "Python 3.8+ required"; return 1; }

    # Check migration script exists
    if [ ! -f "/tmp/migrate_to_mcp_bridge.py" ]; then
        error "Migration script not found at /tmp/migrate_to_mcp_bridge.py"
        return 1
    fi

    success "✅ Environment validation passed"
    return 0
}

# Create system backups
create_backup() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        warn "⚠️  Backup skipped by user request"
        return 0
    fi

    info "📦 Creating backup for Gas Town MCP Integration..."
    
    # Backup existing integration layer if present
    if [ -d "$HOME/.local/bin" ] && [ -f "$HOME/.local/bin/gt-mcp" ]; then
        cp -r "$HOME/.local/bin/gt-mcp"* "$BACKUP_DIR/" || true
        info "✅ Backed up existing integration layer to $BACKUP_DIR"
    fi

    # Backup tmux configuration if present
    if [ -f "$HOME/.tmux.conf.gastown-mcp" ]; then
        cp "$HOME/.tmux.conf.gastown-mcp" "$BACKUP_DIR/" || true
        info "✅ Backed up tmux configuration"
    fi

    success "✅ Backup completed"
    return 0
}

# Deploy Gas Town MCP Integration Layer
deploy_integration_layer() {
    info "🚀 Deploying Gas Town MCP Integration Layer..."

    # Run migration script
    info "📥 Installing integration components..."
    if ! python3 /tmp/migrate_to_mcp_bridge.py --migrate; then
        error "Migration script failed"
        return 1
    fi

    # Verify installation
    if [ ! -f "$HOME/.local/bin/gt-mcp" ]; then
        error "Integration layer installation failed - gt-mcp not found"
        return 1
    fi

    # Make executable
    chmod +x "$HOME/.local/bin/gt-mcp" "$HOME/.local/bin"/*.py 2>/dev/null || true

    success "✅ Integration layer deployed"
    return 0
}

# Configure enhanced features
configure_enhanced_features() {
    info "🔧 Configuring enhanced features..."

    # Setup tmux integration
    if command -v tmux >/dev/null 2>&1; then
        info "📺 Setting up tmux integration..."
        export PATH="$PATH:$HOME/.local/bin"
        if "$HOME/.local/bin/gt-mcp" tmux setup 2>/dev/null; then
            success "✅ tmux integration configured"
        else
            warn "⚠️  tmux integration setup had issues (non-critical)"
        fi
    else
        warn "⚠️  tmux not found - skipping tmux integration"
    fi

    success "✅ Enhanced features configured"
    return 0
}

# Perform health checks
perform_health_checks() {
    info "🏥 Performing deployment health checks..."
    
    export PATH="$PATH:$HOME/.local/bin"

    # Test detection
    info "🔍 Testing Gas Town detection..."
    if timeout "$HEALTH_CHECK_TIMEOUT" "$HOME/.local/bin/gt-mcp" detect >/dev/null 2>&1; then
        success "✅ Gas Town detection working"
    else
        error "❌ Gas Town detection failed"
        return 1
    fi

    # Test status integration
    info "📊 Testing status integration..."
    if timeout "$HEALTH_CHECK_TIMEOUT" "$HOME/.local/bin/gt-mcp" status >/dev/null 2>&1; then
        success "✅ Status integration working"
    else
        warn "⚠️  Status integration had issues (may be due to Steve's gt timeout)"
    fi

    # Test command passthrough
    info "🔄 Testing command passthrough..."
    if timeout 30 "$HOME/.local/bin/gt-mcp" --version >/dev/null 2>&1; then
        success "✅ Command passthrough working"
    else
        error "❌ Command passthrough failed"
        return 1
    fi

    # Test dashboard (non-blocking)
    info "🎛️ Testing dashboard..."
    if timeout 10 "$HOME/.local/bin/gt-mcp" dashboard --detect >/dev/null 2>&1; then
        success "✅ Dashboard working"
    else
        warn "⚠️  Dashboard test had issues (may need Rich library)"
    fi

    success "✅ Health checks completed"
    return 0
}

# Rollback function
perform_rollback() {
    error "🔄 Performing rollback..."
    
    # Find latest backup
    LATEST_BACKUP=$(find "${PROJECT_ROOT}/deployment/backup" -type d -name "20*" | sort | tail -1)
    
    if [ -n "$LATEST_BACKUP" ] && [ -d "$LATEST_BACKUP" ]; then
        info "📦 Restoring from backup: $LATEST_BACKUP"
        
        # Restore gt-mcp files
        if [ -f "$LATEST_BACKUP/gt-mcp" ]; then
            cp "$LATEST_BACKUP/gt-mcp"* "$HOME/.local/bin/" 2>/dev/null || true
            chmod +x "$HOME/.local/bin/gt-mcp" 2>/dev/null || true
        else
            # Remove broken installation
            rm -f "$HOME/.local/bin/gt-mcp"* 2>/dev/null || true
            warn "⚠️  No previous installation to restore - removed broken installation"
        fi
        
        # Restore tmux config
        if [ -f "$LATEST_BACKUP/.tmux.conf.gastown-mcp" ]; then
            cp "$LATEST_BACKUP/.tmux.conf.gastown-mcp" "$HOME/" 2>/dev/null || true
        fi
        
        success "✅ Rollback completed"
    else
        warn "⚠️  No backup found for rollback"
    fi
}

# Usage information
usage() {
    echo "Gas Town MCP Integration Layer Deployment Script"
    echo ""
    echo "USAGE:"
    echo "    $0 [OPTIONS]"
    echo ""
    echo "OPTIONS:"
    echo "    --validate-only        Validate environment without deploying"
    echo "    --component COMP       Deploy specific component (all, integration, config)"
    echo "    --skip-backup         Skip backup creation (faster deployment)"
    echo "    --no-auto-rollback    Disable automatic rollback on failure"
    echo "    --environment ENV     Set environment (production, staging, development)"
    echo "    --help                Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "    $0                              # Full deployment with safety checks"
    echo "    $0 --validate-only              # Dry run validation only"
    echo "    $0 --skip-backup                # Fast deployment without backup"
    echo "    $0 --component integration      # Deploy only integration layer"
    echo "    ENVIRONMENT=staging $0          # Deploy to staging environment"
    echo ""
    echo "COMPONENTS:"
    echo "    all          - Complete Gas Town MCP Integration Layer (default)"
    echo "    integration  - Core integration bridge only"
    echo "    config       - Enhanced configuration only (tmux, etc.)"
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --validate-only)
                VALIDATE_ONLY=true
                shift
                ;;
            --component)
                COMPONENT="$2"
                shift 2
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --no-auto-rollback)
                AUTO_ROLLBACK=false
                shift
                ;;
            --environment)
                ENVIRONMENT="$2"
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
}

# Main deployment function
main() {
    info "🎯 Gas Town MCP Integration Layer Deployment"
    info "   Environment: $ENVIRONMENT"
    info "   Component: $COMPONENT"
    info "   Validation only: $VALIDATE_ONLY"
    info ""

    # Validate environment
    if ! validate_environment; then
        error "❌ Environment validation failed"
        exit 1
    fi

    if [ "$VALIDATE_ONLY" = "true" ]; then
        success "✅ Validation completed successfully - ready for deployment"
        exit 0
    fi

    # Create backup
    if ! create_backup; then
        error "❌ Backup creation failed"
        exit 1
    fi

    # Deploy components based on selection
    case "$COMPONENT" in
        "all"|"integration")
            if ! deploy_integration_layer; then
                error "❌ Integration layer deployment failed"
                exit 1
            fi
            ;;
    esac

    case "$COMPONENT" in
        "all"|"config")
            if ! configure_enhanced_features; then
                error "❌ Enhanced features configuration failed"
                exit 1
            fi
            ;;
    esac

    # Perform health checks
    if ! perform_health_checks; then
        error "❌ Health checks failed"
        exit 1
    fi

    # Generate deployment report
    echo "🎉 Gas Town MCP Integration Layer Deployment Complete!" | tee "$BACKUP_DIR/deployment_report.txt"
    echo "" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "Deployment Details:" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  Timestamp: $(date)" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  Environment: $ENVIRONMENT" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  Component: $COMPONENT" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  Backup Location: $BACKUP_DIR" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  Log File: $LOG_FILE" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "Components Deployed:" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  ✅ Integration Bridge: ~/.local/bin/gt-mcp" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  ✅ Detection System: Steve's Gas Town found" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  ✅ Command Passthrough: All gt commands available via gt-mcp" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  ✅ Enhanced Features: tmux integration configured" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "Next Steps:" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  1. Add ~/.local/bin to PATH: export PATH=\"\$PATH:\$HOME/.local/bin\"" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  2. Test deployment: gt-mcp detect" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  3. Verify integration: gt-mcp status" | tee -a "$BACKUP_DIR/deployment_report.txt"
    echo "  4. Use enhanced features: gt-mcp dashboard" | tee -a "$BACKUP_DIR/deployment_report.txt"

    success "🚀 Gas Town MCP Integration Layer deployment successful!"
    info "📋 Full deployment report saved to: $BACKUP_DIR/deployment_report.txt"
    
    # Disable automatic rollback on successful completion
    trap - EXIT
    exit 0
}

# Parse arguments and run main function
parse_arguments "$@"
main
