#!/bin/bash

# Gas Town MEOW Stack - Health Check Script
# Production-grade monitoring for system health, services, and components

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$MONITORING_ROOT/logging/health_check.log"
METRICS_DIR="$MONITORING_ROOT/metrics"
CONFIG_FILE="$MONITORING_ROOT/config/health_config.yaml"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "$MONITORING_ROOT/logging"
mkdir -p "$METRICS_DIR"
mkdir -p "$(dirname "$CONFIG_FILE")"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Status tracking
declare -A COMPONENT_STATUS
OVERALL_STATUS="healthy"

# Update overall status based on component status
update_overall_status() {
    local component_status="$1"
    case "$component_status" in
        "critical")
            OVERALL_STATUS="critical"
            ;;
        "degraded")
            if [[ "$OVERALL_STATUS" == "healthy" ]]; then
                OVERALL_STATUS="degraded"
            fi
            ;;
    esac
}

# Check service health
check_service() {
    local service_name="$1"
    local url="$2"
    local timeout="${3:-5}"

    log "Checking service: $service_name"

    local start_time=$(date +%s%3N)
    local status_code
    local response_time

    if status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null); then
        local end_time=$(date +%s%3N)
        response_time=$((end_time - start_time))

        if [[ "$status_code" == "200" ]]; then
            if [[ $response_time -gt 5000 ]]; then
                COMPONENT_STATUS["$service_name"]="critical"
                update_overall_status "critical"
                log "❌ $service_name: CRITICAL (HTTP $status_code, ${response_time}ms - too slow)"
                echo -e "${RED}❌ $service_name: CRITICAL (${response_time}ms)${NC}"
            elif [[ $response_time -gt 2000 ]]; then
                COMPONENT_STATUS["$service_name"]="degraded"
                update_overall_status "degraded"
                log "⚠️  $service_name: DEGRADED (HTTP $status_code, ${response_time}ms - slow)"
                echo -e "${YELLOW}⚠️  $service_name: DEGRADED (${response_time}ms)${NC}"
            else
                COMPONENT_STATUS["$service_name"]="healthy"
                log "✅ $service_name: HEALTHY (HTTP $status_code, ${response_time}ms)"
                echo -e "${GREEN}✅ $service_name: HEALTHY (${response_time}ms)${NC}"
            fi
        else
            COMPONENT_STATUS["$service_name"]="critical"
            update_overall_status "critical"
            log "❌ $service_name: CRITICAL (HTTP $status_code)"
            echo -e "${RED}❌ $service_name: CRITICAL (HTTP $status_code)${NC}"
        fi

        # Save metrics
        echo "${service_name},${status_code},${response_time},$(date '+%Y-%m-%d %H:%M:%S')" >> "$METRICS_DIR/service_metrics.csv"
    else
        COMPONENT_STATUS["$service_name"]="critical"
        update_overall_status "critical"
        log "❌ $service_name: CRITICAL (Connection failed)"
        echo -e "${RED}❌ $service_name: CRITICAL (Connection failed)${NC}"
        echo "${service_name},0,0,$(date '+%Y-%m-%d %H:%M:%S')" >> "$METRICS_DIR/service_metrics.csv"
    fi
}

# Check database connectivity
check_database() {
    local db_name="$1"
    local db_path="$2"

    log "Checking database: $db_name"

    if [[ ! -f "$db_path" ]]; then
        COMPONENT_STATUS["db_$db_name"]="critical"
        update_overall_status "critical"
        log "❌ Database $db_name: CRITICAL (File not found: $db_path)"
        echo -e "${RED}❌ Database $db_name: CRITICAL (File not found)${NC}"
        return
    fi

    local start_time=$(date +%s%3N)

    if sqlite3 "$db_path" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" > /dev/null 2>&1; then
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))

        local table_count=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        local file_size_mb=$(echo "scale=2; $(stat -f%z "$db_path" 2>/dev/null || stat -c%s "$db_path") / 1024 / 1024" | bc)

        COMPONENT_STATUS["db_$db_name"]="healthy"
        log "✅ Database $db_name: HEALTHY (${table_count} tables, ${file_size_mb}MB, ${response_time}ms)"
        echo -e "${GREEN}✅ Database $db_name: HEALTHY (${table_count} tables, ${file_size_mb}MB)${NC}"

        echo "db_${db_name},${table_count},${file_size_mb},${response_time},$(date '+%Y-%m-%d %H:%M:%S')" >> "$METRICS_DIR/database_metrics.csv"
    else
        COMPONENT_STATUS["db_$db_name"]="critical"
        update_overall_status "critical"
        log "❌ Database $db_name: CRITICAL (Query failed)"
        echo -e "${RED}❌ Database $db_name: CRITICAL (Query failed)${NC}"
    fi
}

# Check system resources
check_system_resources() {
    log "Checking system resources"

    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | head -1)
    if [[ -z "$cpu_usage" ]]; then
        cpu_usage=$(vmstat 1 2 | tail -1 | awk '{print 100-$15}')
    fi

    # Memory usage
    local mem_total=$(free | grep '^Mem:' | awk '{print $2}')
    local mem_used=$(free | grep '^Mem:' | awk '{print $3}')
    local mem_percent=$(echo "scale=1; $mem_used * 100 / $mem_total" | bc)

    # Disk usage
    local disk_percent=$(df / | grep -v Filesystem | awk '{print $5}' | sed 's/%//g')

    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{ print $2 }' | awk -F',' '{ print $1 }' | tr -d ' ')

    # Check thresholds
    local system_status="healthy"

    if (( $(echo "$cpu_usage >= 90" | bc -l) )) || (( $(echo "$mem_percent >= 95" | bc -l) )) || [[ $disk_percent -ge 95 ]]; then
        system_status="critical"
        update_overall_status "critical"
    elif (( $(echo "$cpu_usage >= 70" | bc -l) )) || (( $(echo "$mem_percent >= 80" | bc -l) )) || [[ $disk_percent -ge 85 ]]; then
        system_status="degraded"
        update_overall_status "degraded"
    fi

    COMPONENT_STATUS["system"]="$system_status"

    case "$system_status" in
        "critical")
            echo -e "${RED}❌ System Resources: CRITICAL${NC}"
            ;;
        "degraded")
            echo -e "${YELLOW}⚠️  System Resources: DEGRADED${NC}"
            ;;
        *)
            echo -e "${GREEN}✅ System Resources: HEALTHY${NC}"
            ;;
    esac

    echo -e "   CPU: ${cpu_usage}% | Memory: ${mem_percent}% | Disk: ${disk_percent}% | Load: ${load_avg}"

    log "System resources: CPU=${cpu_usage}%, Memory=${mem_percent}%, Disk=${disk_percent}%, Load=${load_avg}, Status=${system_status}"

    # Save metrics
    echo "system,${cpu_usage},${mem_percent},${disk_percent},${load_avg},$(date '+%Y-%m-%d %H:%M:%S')" >> "$METRICS_DIR/system_metrics.csv"
}

# Check systemd services
check_systemd_services() {
    log "Checking systemd services"

    local services=("mcp-agent-mail" "ollama")

    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            COMPONENT_STATUS["service_$service"]="healthy"
            log "✅ Service $service: HEALTHY (active)"
            echo -e "${GREEN}✅ Service $service: HEALTHY (active)${NC}"
        elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
            COMPONENT_STATUS["service_$service"]="critical"
            update_overall_status "critical"
            log "❌ Service $service: CRITICAL (enabled but not active)"
            echo -e "${RED}❌ Service $service: CRITICAL (enabled but not active)${NC}"
        else
            COMPONENT_STATUS["service_$service"]="degraded"
            update_overall_status "degraded"
            log "⚠️  Service $service: DEGRADED (not enabled)"
            echo -e "${YELLOW}⚠️  Service $service: DEGRADED (not enabled)${NC}"
        fi
    done
}

# Check MEOW stack components
check_meow_components() {
    log "Checking MEOW stack components"

    # Check beads system
    if command -v bd &> /dev/null; then
        if bd ready --json > /dev/null 2>&1; then
            COMPONENT_STATUS["beads"]="healthy"
            log "✅ Beads system: HEALTHY"
            echo -e "${GREEN}✅ Beads system: HEALTHY${NC}"
        else
            COMPONENT_STATUS["beads"]="degraded"
            update_overall_status "degraded"
            log "⚠️  Beads system: DEGRADED (command failed)"
            echo -e "${YELLOW}⚠️  Beads system: DEGRADED${NC}"
        fi
    else
        COMPONENT_STATUS["beads"]="critical"
        update_overall_status "critical"
        log "❌ Beads system: CRITICAL (command not found)"
        echo -e "${RED}❌ Beads system: CRITICAL (not installed)${NC}"
    fi

    # Check molecule marketplace
    local marketplace_db="/home/ubuntu/projects/deere/molecule-marketplace/marketplace.db"
    if [[ -f "$marketplace_db" ]]; then
        check_database "marketplace" "$marketplace_db"
    else
        COMPONENT_STATUS["marketplace"]="degraded"
        update_overall_status "degraded"
        log "⚠️  Molecule marketplace: DEGRADED (database not found)"
        echo -e "${YELLOW}⚠️  Molecule marketplace: DEGRADED (not initialized)${NC}"
    fi
}

# Check hooks
check_hooks() {
    log "Checking hooks"

    local hook_dir="/home/ubuntu/.claude/hooks"

    if [[ ! -d "$hook_dir" ]]; then
        COMPONENT_STATUS["hooks"]="critical"
        update_overall_status "critical"
        log "❌ Hooks: CRITICAL (Hook directory not found)"
        echo -e "${RED}❌ Hooks: CRITICAL (Hook directory not found)${NC}"
        return
    fi

    local py_hook_count=$(find "$hook_dir" -name "*.py" | wc -l)
    local executable_count=$(find "$hook_dir" -name "*.py" -executable | wc -l)

    if [[ $py_hook_count -eq 0 ]]; then
        COMPONENT_STATUS["hooks"]="degraded"
        update_overall_status "degraded"
        log "⚠️  Hooks: DEGRADED (No hook files found)"
        echo -e "${YELLOW}⚠️  Hooks: DEGRADED (No hook files found)${NC}"
    elif [[ $executable_count -eq 0 ]]; then
        COMPONENT_STATUS["hooks"]="degraded"
        update_overall_status "degraded"
        log "⚠️  Hooks: DEGRADED (No executable hooks found)"
        echo -e "${YELLOW}⚠️  Hooks: DEGRADED (No executable hooks found)${NC}"
    else
        COMPONENT_STATUS["hooks"]="healthy"
        log "✅ Hooks: HEALTHY ($py_hook_count total, $executable_count executable)"
        echo -e "${GREEN}✅ Hooks: HEALTHY ($py_hook_count total, $executable_count executable)${NC}"
    fi
}

# Generate health report
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local report_file="$METRICS_DIR/health_report_$(date '+%Y%m%d_%H%M%S').yaml"

    cat > "$report_file" << EOF
timestamp: "$timestamp"
overall_status: "$OVERALL_STATUS"
components:
EOF

    for component in "${!COMPONENT_STATUS[@]}"; do
        echo "  $component: \"${COMPONENT_STATUS[$component]}\"" >> "$report_file"
    done

    cat >> "$report_file" << EOF
summary:
  healthy_count: $(printf '%s\n' "${COMPONENT_STATUS[@]}" | grep -c "healthy" || echo "0")
  degraded_count: $(printf '%s\n' "${COMPONENT_STATUS[@]}" | grep -c "degraded" || echo "0")
  critical_count: $(printf '%s\n' "${COMPONENT_STATUS[@]}" | grep -c "critical" || echo "0")
  total_count: ${#COMPONENT_STATUS[@]}
EOF

    echo
    echo -e "${BLUE}📊 Health Report Generated: $report_file${NC}"
}

# Main health check function
main() {
    echo "🔍 Gas Town MEOW Stack Health Check - $(date)"
    echo "=================================================="

    log "Starting comprehensive health check"

    # Initialize metrics files with headers
    [[ ! -f "$METRICS_DIR/service_metrics.csv" ]] && echo "service,status_code,response_time_ms,timestamp" > "$METRICS_DIR/service_metrics.csv"
    [[ ! -f "$METRICS_DIR/database_metrics.csv" ]] && echo "database,table_count,size_mb,response_time_ms,timestamp" > "$METRICS_DIR/database_metrics.csv"
    [[ ! -f "$METRICS_DIR/system_metrics.csv" ]] && echo "component,cpu_percent,memory_percent,disk_percent,load_avg,timestamp" > "$METRICS_DIR/system_metrics.csv"

    # Check systemd services first
    echo
    echo "🔧 System Services:"
    check_systemd_services

    # Check external services
    echo
    echo "🌐 External Services:"
    check_service "mcp-agent-mail" "http://localhost:8765/health" 5
    check_service "ollama" "http://localhost:11434/api/tags" 10

    # Check databases
    echo
    echo "🗄️  Databases:"
    check_database "beads" "/home/ubuntu/.beads/beads.db"
    check_database "agent_mail" "/home/ubuntu/mcp_agent_mail/storage.sqlite3"

    # Check MEOW stack components
    echo
    echo "🏗️  MEOW Stack Components:"
    check_meow_components

    # Check system resources
    echo
    echo "💻 System Resources:"
    check_system_resources

    # Check hooks
    echo
    echo "🔗 Hooks:"
    check_hooks

    # Generate report
    generate_report

    # Final status
    echo
    echo "=================================================="
    case "$OVERALL_STATUS" in
        "healthy")
            echo -e "${GREEN}🎉 Overall Status: HEALTHY${NC}"
            log "Health check completed - Overall status: HEALTHY"
            ;;
        "degraded")
            echo -e "${YELLOW}⚠️  Overall Status: DEGRADED${NC}"
            log "Health check completed - Overall status: DEGRADED"
            ;;
        "critical")
            echo -e "${RED}🚨 Overall Status: CRITICAL${NC}"
            log "Health check completed - Overall status: CRITICAL"
            ;;
    esac

    # Exit with appropriate code
    case "$OVERALL_STATUS" in
        "healthy") exit 0 ;;
        "degraded") exit 1 ;;
        "critical") exit 2 ;;
    esac
}

# Command line options
case "${1:-}" in
    "--json")
        # JSON output only (simulated)
        main 2>/dev/null
        ;;
    "--quiet")
        # Quiet mode - only log, no console output
        main > /dev/null
        ;;
    "--continuous")
        # Continuous monitoring mode
        interval="${2:-60}"
        echo "Starting continuous monitoring (interval: ${interval}s)"
        while true; do
            main
            sleep "$interval"
        done
        ;;
    *)
        # Normal mode
        main
        ;;
esac