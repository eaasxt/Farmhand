#!/bin/bash
#
# Unified Deployment Script
# -------------------------
# Handles git→build→deploy→verify pipeline with profile support.
#
# Profiles:
# - dev: Local testing with tunnel
# - staging: Full pipeline to staging environment
# - production: Full pipeline with maximum safety checks
#
# Usage:
#   ./deploy.sh <project_path> <profile> <mode>
#
# Examples:
#   ./deploy.sh /home/ubuntu/myproject dev automatic
#   ./deploy.sh /home/ubuntu/myproject production manual

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FARMHAND_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="/tmp/farmhand-deploy-$(date +%s).log"

# Default values
PROJECT_PATH="${1:-$(pwd)}"
PROFILE="${2:-dev}"
MODE="${3:-automatic}"

# Logging
log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# Validation functions
validate_environment() {
    log_info "Validating environment for profile: $PROFILE"

    # Check required tools
    local required_tools=("git" "node" "npm")
    if [[ "$PROFILE" == "production" ]]; then
        required_tools+=("vercel")
    fi

    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found: $tool"
            return 1
        fi
    done

    # Check git status
    if [[ -d "$PROJECT_PATH/.git" ]]; then
        cd "$PROJECT_PATH"
        if ! git status --porcelain | grep -q "^$"; then
            if [[ "$PROFILE" == "production" ]]; then
                log_error "Working tree not clean for production deployment"
                return 1
            else
                log_warn "Working tree not clean - proceeding for $PROFILE profile"
            fi
        fi
    fi

    log_info "Environment validation passed"
}

validate_security() {
    log_info "Running security validation"
    cd "$PROJECT_PATH"

    # UBS scan if available
    if command -v ubs >/dev/null 2>&1; then
        log_info "Running UBS security scan"
        local changed_files
        changed_files=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "")

        if [[ -n "$changed_files" ]]; then
            if ! ubs $changed_files; then
                log_error "UBS security scan failed"
                return 1
            fi
        fi
    else
        log_warn "UBS not available - skipping security scan"
    fi

    # Check for secrets
    local secret_patterns=("password" "secret" "key" "token" "api_key")
    for pattern in "${secret_patterns[@]}"; do
        if git diff --cached | grep -i "$pattern" >/dev/null; then
            log_warn "Potential secret detected in staged changes: $pattern"
        fi
    done

    log_info "Security validation completed"
}

run_tests() {
    log_info "Running tests for $PROFILE profile"
    cd "$PROJECT_PATH"

    # Detect and run tests
    if [[ -f "package.json" ]] && grep -q '"test"' package.json; then
        log_info "Running npm tests"
        npm test || {
            if [[ "$PROFILE" == "production" ]]; then
                log_error "Tests failed - blocking production deployment"
                return 1
            else
                log_warn "Tests failed - continuing for $PROFILE profile"
            fi
        }
    elif [[ -f "pyproject.toml" ]] || [[ -f "requirements.txt" ]]; then
        if command -v pytest >/dev/null 2>&1; then
            log_info "Running pytest"
            pytest || {
                if [[ "$PROFILE" == "production" ]]; then
                    log_error "Tests failed - blocking production deployment"
                    return 1
                else
                    log_warn "Tests failed - continuing for $PROFILE profile"
                fi
            }
        fi
    else
        log_info "No tests detected"
    fi

    log_info "Test execution completed"
}

build_application() {
    log_info "Building application for $PROFILE profile"
    cd "$PROJECT_PATH"

    # Clean previous builds
    rm -rf dist/ build/ .next/ out/ 2>/dev/null || true

    if [[ -f "package.json" ]]; then
        # Node.js application
        if grep -q '"build"' package.json; then
            log_info "Running npm build"
            npm run build

            # Verify build artifacts
            local build_dirs=("dist" "build" ".next" "out")
            local found_build=false
            for dir in "${build_dirs[@]}"; do
                if [[ -d "$dir" ]]; then
                    local size
                    size=$(du -sh "$dir" | cut -f1)
                    log_info "Build artifact: $dir ($size)"
                    found_build=true
                fi
            done

            if [[ "$found_build" == "false" ]]; then
                log_warn "No build artifacts found after build"
            fi
        fi
    elif [[ -f "pyproject.toml" ]]; then
        # Python application
        if command -v uv >/dev/null 2>&1; then
            log_info "Building Python package with uv"
            uv build
        elif command -v python >/dev/null 2>&1; then
            log_info "Building Python package"
            python -m build
        fi
    fi

    log_info "Build completed"
}

deploy_application() {
    log_info "Deploying application using $PROFILE profile"
    cd "$PROJECT_PATH"

    case "$PROFILE" in
        "dev")
            deploy_dev
            ;;
        "staging")
            deploy_staging
            ;;
        "production")
            deploy_production
            ;;
        *)
            log_error "Unknown deployment profile: $PROFILE"
            return 1
            ;;
    esac
}

deploy_dev() {
    log_info "Starting development deployment"

    # Start local server if package.json exists
    if [[ -f "package.json" ]]; then
        if grep -q '"dev"' package.json; then
            log_info "Starting development server"
            # Start in background for testing
            npm run dev &
            local dev_pid=$!
            sleep 5  # Give server time to start

            # Test connectivity
            if curl -f http://localhost:3000 >/dev/null 2>&1; then
                log_info "Development server accessible at http://localhost:3000"
                kill $dev_pid 2>/dev/null || true
            else
                log_warn "Development server may not be accessible"
                kill $dev_pid 2>/dev/null || true
            fi
        fi
    fi

    log_info "Development deployment completed"
}

deploy_staging() {
    log_info "Starting staging deployment"

    # Use Vercel preview deployment
    if command -v vercel >/dev/null 2>&1; then
        log_info "Deploying to Vercel staging"
        vercel --confirm --scope team 2>&1 | tee -a "$LOG_FILE"

        # Get preview URL
        local preview_url
        preview_url=$(vercel ls --scope team --json | jq -r '.[0].url' 2>/dev/null || echo "")
        if [[ -n "$preview_url" ]]; then
            log_info "Staging deployment available at: https://$preview_url"
            echo "https://$preview_url" > /tmp/farmhand-staging-url.txt
        fi
    else
        log_warn "Vercel not available - manual staging deployment required"
    fi

    log_info "Staging deployment completed"
}

deploy_production() {
    log_info "Starting production deployment"

    # Production safety checks
    if [[ "$MODE" == "manual" ]]; then
        echo "Production deployment requires manual confirmation."
        echo "Project: $PROJECT_PATH"
        echo "Profile: $PROFILE"
        echo -n "Proceed? [y/N] "
        read -r response
        if [[ "$response" != "y" && "$response" != "Y" ]]; then
            log_info "Production deployment cancelled by user"
            return 0
        fi
    fi

    # Deploy to production
    if command -v vercel >/dev/null 2>&1; then
        log_info "Deploying to Vercel production"
        vercel --prod --confirm --scope team 2>&1 | tee -a "$LOG_FILE"

        # Get production URL
        local prod_url
        prod_url=$(vercel ls --scope team --prod --json | jq -r '.[0].url' 2>/dev/null || echo "")
        if [[ -n "$prod_url" ]]; then
            log_info "Production deployment available at: https://$prod_url"
            echo "https://$prod_url" > /tmp/farmhand-production-url.txt
        fi
    else
        log_warn "Vercel not available - manual production deployment required"
    fi

    log_info "Production deployment completed"
}

verify_deployment() {
    log_info "Verifying deployment for $PROFILE profile"

    local url_file="/tmp/farmhand-${PROFILE}-url.txt"
    local deploy_url=""

    if [[ -f "$url_file" ]]; then
        deploy_url=$(cat "$url_file")
    elif [[ "$PROFILE" == "dev" ]]; then
        deploy_url="http://localhost:3000"
    fi

    if [[ -n "$deploy_url" ]]; then
        log_info "Testing deployment at: $deploy_url"

        # Basic connectivity test
        if curl -f "$deploy_url" >/dev/null 2>&1; then
            log_info "✓ Deployment accessible"
        else
            log_warn "✗ Deployment not accessible"
            return 1
        fi

        # Response time test
        local response_time
        response_time=$(curl -o /dev/null -s -w '%{time_total}' "$deploy_url" 2>/dev/null || echo "0")
        log_info "Response time: ${response_time}s"

        # Health check if endpoint exists
        if curl -f "$deploy_url/api/health" >/dev/null 2>&1; then
            log_info "✓ Health endpoint accessible"
        else
            log_info "○ No health endpoint found"
        fi

        echo "Manual verification required:"
        echo "1. Open $deploy_url in browser"
        echo "2. Test main functionality"
        echo "3. Verify no console errors"

    else
        log_warn "No deployment URL available for verification"
    fi

    log_info "Deployment verification completed"
}

record_deployment() {
    log_info "Recording deployment metadata"

    local deployment_record="/tmp/farmhand-deployment-$(date +%s).json"

    cd "$PROJECT_PATH"

    cat > "$deployment_record" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "project_path": "$PROJECT_PATH",
  "profile": "$PROFILE",
  "mode": "$MODE",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
  "deployment_id": "$(date +%s)",
  "log_file": "$LOG_FILE",
  "success": true
}
EOF

    log_info "Deployment record saved: $deployment_record"

    # Update deployment state if orchestrator database exists
    if [[ -f "$HOME/.farmhand/deployment-state.db" ]]; then
        python3 << EOF
import sqlite3
import json
from pathlib import Path

try:
    with open('$deployment_record') as f:
        record = json.load(f)

    with sqlite3.connect('$HOME/.farmhand/deployment-state.db') as conn:
        conn.execute('''
            INSERT INTO deployment_state
            (project_path, agent_name, phase, status, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            record['project_path'],
            'deployment-script',
            'deploy_complete',
            'success',
            json.dumps(record)
        ))
        conn.commit()
        print("Updated deployment state database")
except Exception as e:
    print(f"Failed to update deployment state: {e}")
EOF
    fi
}

cleanup() {
    log_info "Cleaning up deployment artifacts"

    # Remove temporary URLs
    rm -f /tmp/farmhand-*-url.txt 2>/dev/null || true

    # Archive log file
    local log_archive="$HOME/.farmhand/logs/deploy-$(date +%Y%m%d).log"
    mkdir -p "$(dirname "$log_archive")"
    cp "$LOG_FILE" "$log_archive" 2>/dev/null || true

    log_info "Deployment completed - log archived to: $log_archive"
}

main() {
    log_info "Starting Farmhand deployment ceremony"
    log_info "Project: $PROJECT_PATH"
    log_info "Profile: $PROFILE"
    log_info "Mode: $MODE"
    log_info "Log: $LOG_FILE"

    # Ensure we're in project directory
    if [[ ! -d "$PROJECT_PATH" ]]; then
        log_error "Project path not found: $PROJECT_PATH"
        exit 1
    fi

    # Execute deployment phases
    validate_environment || exit 1
    validate_security || exit 1

    if [[ "$PROFILE" != "dev" ]]; then
        run_tests || exit 1
    fi

    build_application || exit 1
    deploy_application || exit 1
    verify_deployment || exit 1
    record_deployment || exit 1

    cleanup

    log_info "🎉 Deployment ceremony completed successfully!"
    echo
    echo "📋 Deployment Summary:"
    echo "   Project: $PROJECT_PATH"
    echo "   Profile: $PROFILE"
    echo "   Mode: $MODE"
    echo "   Log: $LOG_FILE"
    echo
    echo "✅ All deployment phases completed"

    if [[ -f "/tmp/farmhand-${PROFILE}-url.txt" ]]; then
        local url
        url=$(cat "/tmp/farmhand-${PROFILE}-url.txt")
        echo "🔗 Deployment URL: $url"
    fi
}

# Handle script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Direct execution
    main "$@"
else
    # Sourced - just define functions
    log_info "Deployment functions loaded"
fi
