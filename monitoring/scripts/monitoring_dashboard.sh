#!/bin/bash

# Gas Town MEOW Stack - Monitoring Dashboard
# Real-time monitoring dashboard for production environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_SCRIPT="$SCRIPT_DIR/health_check.sh"
METRICS_DIR="$MONITORING_ROOT/metrics"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m'

# Dashboard refresh interval (seconds)
REFRESH_INTERVAL=5

# Clear screen function
clear_screen() {
    clear
    tput cup 0 0
}

# Get terminal dimensions
get_terminal_size() {
    TERM_COLS=$(tput cols)
    TERM_ROWS=$(tput lines)
}

# Draw header
draw_header() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${WHITE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${WHITE}║                    ${CYAN}GAS TOWN MEOW STACK${WHITE} - Production Monitor                   ║${NC}"
    echo -e "${WHITE}║                              ${timestamp}                              ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
}

# Get system metrics
get_system_metrics() {
    # CPU usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | head -1)
    [[ -z "$CPU_USAGE" ]] && CPU_USAGE=$(vmstat 1 2 | tail -1 | awk '{print 100-$15}')

    # Memory usage
    MEM_TOTAL=$(free | grep '^Mem:' | awk '{print $2}')
    MEM_USED=$(free | grep '^Mem:' | awk '{print $3}')
    MEM_USAGE=$(echo "scale=1; $MEM_USED * 100 / $MEM_TOTAL" | bc)

    # Disk usage
    DISK_USAGE=$(df / | grep -v Filesystem | awk '{print $5}' | sed 's/%//g')

    # Load average
    LOAD_AVG=$(uptime | awk -F'load average:' '{ print $2 }' | awk -F',' '{ print $1 }' | tr -d ' ')

    # Network connections
    NET_CONNECTIONS=$(netstat -an 2>/dev/null | wc -l || echo "N/A")

    # Uptime
    UPTIME=$(uptime | awk -F'up ' '{ print $2 }' | awk -F',' '{ print $1 }')
}

# Check service status
check_service_status() {
    local service_name="$1"
    local url="$2"

    if curl -s --max-time 3 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}●${NC} $service_name"
    else
        echo -e "${RED}●${NC} $service_name"
    fi
}

# Check systemd service
check_systemd_service() {
    local service="$1"

    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo -e "${GREEN}●${NC} $service"
    else
        echo -e "${RED}●${NC} $service"
    fi
}

# Check database status
check_database_status() {
    local db_name="$1"
    local db_path="$2"

    if [[ -f "$db_path" ]] && sqlite3 "$db_path" "SELECT 1;" > /dev/null 2>&1; then
        local size_mb=$(echo "scale=1; $(stat -f%z "$db_path" 2>/dev/null || stat -c%s "$db_path") / 1024 / 1024" | bc)
        echo -e "${GREEN}●${NC} $db_name (${size_mb}MB)"
    else
        echo -e "${RED}●${NC} $db_name"
    fi
}

# Get color for percentage value
get_percentage_color() {
    local value=$1
    local critical=${2:-90}
    local warning=${3:-70}

    if (( $(echo "$value >= $critical" | bc -l) )); then
        echo "$RED"
    elif (( $(echo "$value >= $warning" | bc -l) )); then
        echo "$YELLOW"
    else
        echo "$GREEN"
    fi
}

# Draw progress bar
draw_progress_bar() {
    local value=$1
    local max_value=${2:-100}
    local width=${3:-20}
    local color=${4:-$GREEN}

    local percentage=$(echo "scale=0; $value * 100 / $max_value" | bc)
    local filled=$(echo "scale=0; $width * $value / $max_value" | bc)

    echo -n -e "${color}["
    for ((i=0; i<filled; i++)); do echo -n "█"; done
    for ((i=filled; i<width; i++)); do echo -n "░"; done
    echo -e "] ${percentage}%${NC}"
}

# Draw system overview
draw_system_overview() {
    echo -e "${WHITE}┌─ SYSTEM OVERVIEW ─────────────────────────────────────────────────────────┐${NC}"

    # CPU
    local cpu_color=$(get_percentage_color "$CPU_USAGE" 90 70)
    echo -n -e "${WHITE}│${NC} CPU Usage:    "
    draw_progress_bar "$CPU_USAGE" 100 20 "$cpu_color"

    # Memory
    local mem_color=$(get_percentage_color "$MEM_USAGE" 95 80)
    echo -n -e "${WHITE}│${NC} Memory Usage: "
    draw_progress_bar "$MEM_USAGE" 100 20 "$mem_color"

    # Disk
    local disk_color=$(get_percentage_color "$DISK_USAGE" 95 85)
    echo -n -e "${WHITE}│${NC} Disk Usage:   "
    draw_progress_bar "$DISK_USAGE" 100 20 "$disk_color"

    echo -e "${WHITE}│${NC} Load Average: ${CYAN}${LOAD_AVG}${NC}"
    echo -e "${WHITE}│${NC} Uptime:       ${CYAN}${UPTIME}${NC}"
    echo -e "${WHITE}│${NC} Connections:  ${CYAN}${NET_CONNECTIONS}${NC}"
    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# Draw services status
draw_services_status() {
    echo -e "${WHITE}┌─ SERVICES STATUS ─────────────────────────────────────────────────────────┐${NC}"
    echo -e "${WHITE}│${NC} System Services:"
    echo -n -e "${WHITE}│${NC}   "
    check_systemd_service "mcp-agent-mail"
    echo -n -e "${WHITE}│${NC}   "
    check_systemd_service "ollama"
    echo -e "${WHITE}│${NC}"
    echo -e "${WHITE}│${NC} Web Services:"
    echo -n -e "${WHITE}│${NC}   "
    check_service_status "MCP Agent Mail" "http://localhost:8765/health"
    echo -n -e "${WHITE}│${NC}   "
    check_service_status "Ollama AI" "http://localhost:11434/api/tags"
    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# Draw databases status
draw_databases_status() {
    echo -e "${WHITE}┌─ DATABASES STATUS ────────────────────────────────────────────────────────┐${NC}"
    echo -n -e "${WHITE}│${NC}   "
    check_database_status "Beads" "/home/ubuntu/.beads/beads.db"
    echo -n -e "${WHITE}│${NC}   "
    check_database_status "Agent Mail" "/home/ubuntu/mcp_agent_mail/storage.sqlite3"
    echo -n -e "${WHITE}│${NC}   "
    check_database_status "Marketplace" "/home/ubuntu/projects/deere/molecule-marketplace/marketplace.db"
    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# Draw MEOW stack status
draw_meow_stack_status() {
    echo -e "${WHITE}┌─ MEOW STACK STATUS ───────────────────────────────────────────────────────┐${NC}"

    # Check beads
    local beads_status="${RED}●${NC}"
    if command -v bd &> /dev/null && bd ready --json > /dev/null 2>&1; then
        beads_status="${GREEN}●${NC}"
    fi
    echo -e "${WHITE}│${NC}   $beads_status Beads (Task Management)"

    # Check molecule marketplace
    local marketplace_status="${RED}●${NC}"
    if [[ -f "/home/ubuntu/projects/deere/molecule-marketplace/marketplace.db" ]]; then
        marketplace_status="${GREEN}●${NC}"
    fi
    echo -e "${WHITE}│${NC}   $marketplace_status Molecule Marketplace"

    # Check hooks
    local hooks_status="${RED}●${NC}"
    if [[ -d "/home/ubuntu/.claude/hooks" ]] && [[ $(find /home/ubuntu/.claude/hooks -name "*.py" | wc -l) -gt 0 ]]; then
        hooks_status="${GREEN}●${NC}"
    fi
    echo -e "${WHITE}│${NC}   $hooks_status Claude Hooks"

    # Check orchestration
    local orchestration_status="${GREEN}●${NC}"
    if [[ ! -f "/home/ubuntu/projects/deere/molecule-marketplace/orchestration/orchestration_engine.py" ]]; then
        orchestration_status="${YELLOW}●${NC}"
    fi
    echo -e "${WHITE}│${NC}   $orchestration_status AI Orchestration"

    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# Draw recent alerts
draw_recent_alerts() {
    echo -e "${WHITE}┌─ RECENT ALERTS ───────────────────────────────────────────────────────────┐${NC}"

    local alert_file="$MONITORING_ROOT/logging/alerts.log"
    if [[ -f "$alert_file" ]]; then
        local alert_count=$(tail -10 "$alert_file" 2>/dev/null | wc -l)
        if [[ $alert_count -gt 0 ]]; then
            tail -5 "$alert_file" 2>/dev/null | while IFS= read -r line; do
                if [[ "$line" == *"CRITICAL"* ]]; then
                    echo -e "${WHITE}│${NC} ${RED}● CRITICAL${NC} ${line}"
                elif [[ "$line" == *"WARNING"* ]]; then
                    echo -e "${WHITE}│${NC} ${YELLOW}● WARNING${NC} ${line}"
                else
                    echo -e "${WHITE}│${NC} ${BLUE}● INFO${NC} ${line}"
                fi
            done
        else
            echo -e "${WHITE}│${NC} ${GREEN}No recent alerts${NC}"
        fi
    else
        echo -e "${WHITE}│${NC} ${GREEN}No alerts logged${NC}"
    fi

    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# Draw performance metrics
draw_performance_metrics() {
    echo -e "${WHITE}┌─ PERFORMANCE METRICS ─────────────────────────────────────────────────────┐${NC}"

    # Get latest metrics if available
    local service_metrics="$METRICS_DIR/service_metrics.csv"
    local db_metrics="$METRICS_DIR/database_metrics.csv"

    if [[ -f "$service_metrics" ]]; then
        echo -e "${WHITE}│${NC} Recent Service Response Times:"
        tail -3 "$service_metrics" 2>/dev/null | while IFS=',' read -r service status_code response_time timestamp; do
            [[ "$service" == "service" ]] && continue  # Skip header
            local color="$GREEN"
            [[ $response_time -gt 2000 ]] && color="$YELLOW"
            [[ $response_time -gt 5000 ]] && color="$RED"
            echo -e "${WHITE}│${NC}   ${color}●${NC} $service: ${response_time}ms"
        done
    fi

    if [[ -f "$db_metrics" ]]; then
        echo -e "${WHITE}│${NC} Database Performance:"
        tail -3 "$db_metrics" 2>/dev/null | while IFS=',' read -r database table_count size_mb response_time timestamp; do
            [[ "$database" == "database" ]] && continue  # Skip header
            local color="$GREEN"
            [[ $(echo "$response_time > 1000" | bc -l) == 1 ]] && color="$YELLOW"
            [[ $(echo "$response_time > 5000" | bc -l) == 1 ]] && color="$RED"
            echo -e "${WHITE}│${NC}   ${color}●${NC} $database: ${response_time}ms (${size_mb}MB)"
        done
    fi

    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
}

# Draw footer
draw_footer() {
    echo -e "${WHITE}┌─ CONTROLS ────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${WHITE}│${NC} ${CYAN}Press Ctrl+C to exit${NC} | ${CYAN}Refresh every ${REFRESH_INTERVAL}s${NC} | ${CYAN}Run manual health check: $HEALTH_SCRIPT${NC}"
    echo -e "${WHITE}└───────────────────────────────────────────────────────────────────────────┘${NC}"
}

# Main dashboard loop
main_dashboard() {
    # Check if health check script exists
    if [[ ! -x "$HEALTH_SCRIPT" ]]; then
        echo "Health check script not found or not executable: $HEALTH_SCRIPT"
        exit 1
    fi

    # Trap Ctrl+C
    trap 'echo -e "\n${CYAN}Dashboard stopped.${NC}"; exit 0' INT

    echo -e "${CYAN}Starting Gas Town MEOW Stack Monitoring Dashboard...${NC}"
    sleep 2

    while true; do
        get_terminal_size
        clear_screen

        get_system_metrics

        draw_header
        draw_system_overview
        draw_services_status
        draw_databases_status
        draw_meow_stack_status
        draw_recent_alerts
        draw_performance_metrics
        draw_footer

        sleep "$REFRESH_INTERVAL"
    done
}

# Command line options
case "${1:-dashboard}" in
    "dashboard"|"")
        main_dashboard
        ;;
    "health")
        echo "Running health check..."
        "$HEALTH_SCRIPT"
        ;;
    "metrics")
        echo "Collecting current metrics..."
        get_system_metrics
        echo "CPU: ${CPU_USAGE}%"
        echo "Memory: ${MEM_USAGE}%"
        echo "Disk: ${DISK_USAGE}%"
        echo "Load: ${LOAD_AVG}"
        ;;
    "status")
        echo "=== Gas Town MEOW Stack Status ==="
        echo
        echo "System Services:"
        systemctl is-active mcp-agent-mail && echo "  ✓ MCP Agent Mail" || echo "  ✗ MCP Agent Mail"
        systemctl is-active ollama && echo "  ✓ Ollama" || echo "  ✗ Ollama"
        echo
        echo "Web Services:"
        curl -s --max-time 3 http://localhost:8765/health > /dev/null && echo "  ✓ MCP Agent Mail Web" || echo "  ✗ MCP Agent Mail Web"
        curl -s --max-time 3 http://localhost:11434/api/tags > /dev/null && echo "  ✓ Ollama API" || echo "  ✗ Ollama API"
        echo
        echo "Databases:"
        [[ -f "/home/ubuntu/.beads/beads.db" ]] && echo "  ✓ Beads Database" || echo "  ✗ Beads Database"
        [[ -f "/home/ubuntu/mcp_agent_mail/storage.sqlite3" ]] && echo "  ✓ Agent Mail Database" || echo "  ✗ Agent Mail Database"
        [[ -f "/home/ubuntu/projects/deere/molecule-marketplace/marketplace.db" ]] && echo "  ✓ Marketplace Database" || echo "  ✗ Marketplace Database"
        ;;
    "--help"|"-h")
        echo "Gas Town MEOW Stack Monitoring Dashboard"
        echo
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  dashboard    Start the interactive dashboard (default)"
        echo "  health       Run a single health check"
        echo "  metrics      Show current system metrics"
        echo "  status       Show quick status overview"
        echo "  --help       Show this help message"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac