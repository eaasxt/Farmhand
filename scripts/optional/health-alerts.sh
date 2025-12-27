#!/usr/bin/env bash
# health-alerts.sh - Farmhand Health Monitoring with Alerts
# Part of Farmhand optional utilities (bolt-on, opt-in)
#
# Usage:
#   ./health-alerts.sh              # Run once, output to terminal
#   ./health-alerts.sh --watch      # Continuous monitoring (Ctrl+C to stop)
#   ./health-alerts.sh --cron       # Silent unless issues found (for cron)
#   ./health-alerts.sh --json       # JSON output for automation

set -uo pipefail

# Configuration (override via environment)
ALERT_THRESHOLD_STALE_HOURS="${ALERT_THRESHOLD_STALE_HOURS:-4}"
ALERT_THRESHOLD_TTL_MINUTES="${ALERT_THRESHOLD_TTL_MINUTES:-10}"
WATCH_INTERVAL="${WATCH_INTERVAL:-60}"

# Colors (disabled in cron mode)
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# State
ISSUES_FOUND=0
WARNINGS_FOUND=0
OUTPUT_MODE="terminal"
declare -a ISSUES=()
declare -a WARNINGS=()

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --watch    Continuous monitoring (every ${WATCH_INTERVAL}s)"
    echo "  --cron     Silent unless issues found (for cron jobs)"
    echo "  --json     Output in JSON format"
    echo "  --help     Show this help"
}

log_issue() { ISSUES+=("$1"); ((ISSUES_FOUND++)); }
log_warning() { WARNINGS+=("$1"); ((WARNINGS_FOUND++)); }

send_notification() {
    local title="$1" message="$2" urgency="${3:-normal}"
    command -v notify-send &>/dev/null && notify-send -u "$urgency" "$title" "$message" 2>/dev/null || true
    command -v osascript &>/dev/null && osascript -e "display notification \"$message\" with title \"$title\"" 2>/dev/null || true
}

check_mcp_agent_mail() {
    if systemctl is-active --quiet mcp-agent-mail 2>/dev/null; then
        curl -s --max-time 2 http://localhost:8765/health &>/dev/null || { log_issue "MCP Agent Mail: Not responding on port 8765"; return 1; }
    elif ! pgrep -f "mcp_agent_mail" &>/dev/null; then
        log_issue "MCP Agent Mail: Service not running"
        return 1
    fi
}

check_ollama() {
    if systemctl is-active --quiet ollama 2>/dev/null; then
        curl -s --max-time 2 http://localhost:11434/api/tags &>/dev/null || log_warning "Ollama: API not responding"
    elif command -v ollama &>/dev/null; then
        log_warning "Ollama: Installed but service not running"
    fi
}

check_beads_db() {
    local db="${BEADS_DB:-$HOME/.beads/beads.db}"
    [[ -f "$db" ]] || { log_warning "Beads database: Not found at $db"; return 1; }
    sqlite3 "$db" "SELECT 1" &>/dev/null || { log_issue "Beads database: Not readable"; return 1; }
}

check_hooks_installed() {
    local hooks_dir="$HOME/.claude/hooks" missing=()
    [[ -d "$hooks_dir" ]] || { log_issue "Hooks directory missing: $hooks_dir"; return 1; }
    for hook in reservation-checker.py todowrite-interceptor.py mcp-state-tracker.py; do
        [[ -f "$hooks_dir/$hook" ]] || missing+=("$hook")
    done
    [[ ${#missing[@]} -gt 0 ]] && log_issue "Missing hooks: ${missing[*]}"
    [[ -f "$HOME/.claude/settings.json" ]] || log_issue "Settings file missing"
}

check_stale_reservations() {
    local state_file="$HOME/.claude/agent-state.json" now threshold
    [[ -f "$state_file" ]] || return 0
    now=$(date +%s); threshold=$((ALERT_THRESHOLD_STALE_HOURS * 3600))
    command -v jq &>/dev/null || return 0
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local created_at=$(echo "$line" | awk '{print $1}' | cut -d. -f1)
        local paths=$(echo "$line" | cut -d' ' -f2-)
        if [[ -n "$created_at" && "$created_at" =~ ^[0-9]+$ ]]; then
            local age=$((now - created_at))
            [[ $age -gt $threshold ]] && log_warning "Stale reservation ($((age/3600))h old): $paths"
        fi
    done < <(jq -r '.reservations[]? | "\(.created_at) \(.paths | join(","))"' "$state_file" 2>/dev/null)
}

check_expiring_reservations() {
    local state_file="$HOME/.claude/agent-state.json" now threshold
    [[ -f "$state_file" ]] || return 0
    now=$(date +%s); threshold=$((ALERT_THRESHOLD_TTL_MINUTES * 60))
    command -v jq &>/dev/null || return 0
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local expires_at=$(echo "$line" | awk '{print $1}' | cut -d. -f1)
        local paths=$(echo "$line" | cut -d' ' -f2-)
        if [[ -n "$expires_at" && "$expires_at" =~ ^[0-9]+$ ]]; then
            local remaining=$((expires_at - now))
            [[ $remaining -gt 0 && $remaining -lt $threshold ]] && log_warning "Reservation expiring in $((remaining/60))m: $paths"
        fi
    done < <(jq -r '.reservations[]? | "\(.expires_at) \(.paths | join(","))"' "$state_file" 2>/dev/null)
}

check_disk_space() {
    local usage=$(df -h "$HOME" | awk 'NR==2 {print $5}' | tr -d '%')
    [[ "$usage" -gt 95 ]] && { log_issue "Disk space critical: ${usage}% used"; return 1; }
    [[ "$usage" -gt 85 ]] && log_warning "Disk space warning: ${usage}% used"
}

run_checks() {
    ISSUES_FOUND=0; WARNINGS_FOUND=0; ISSUES=(); WARNINGS=()
    check_mcp_agent_mail; check_ollama; check_beads_db
    check_hooks_installed; check_stale_reservations
    check_expiring_reservations; check_disk_space
}

output_terminal() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Farmhand Health Check - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
    if [[ $ISSUES_FOUND -eq 0 && $WARNINGS_FOUND -eq 0 ]]; then
        echo -e "  ${GREEN}✓ All systems healthy${NC}"
    else
        [[ $ISSUES_FOUND -gt 0 ]] && { echo -e "  ${RED}✗ Issues: $ISSUES_FOUND${NC}"; printf "    ${RED}• %s${NC}\n" "${ISSUES[@]}"; }
        [[ $WARNINGS_FOUND -gt 0 ]] && { echo -e "  ${YELLOW}⚠ Warnings: $WARNINGS_FOUND${NC}"; printf "    ${YELLOW}• %s${NC}\n" "${WARNINGS[@]}"; }
    fi
    echo ""
}

output_json() {
    local status="healthy"
    [[ $WARNINGS_FOUND -gt 0 ]] && status="warning"
    [[ $ISSUES_FOUND -gt 0 ]] && status="critical"
    printf '{"timestamp":"%s","status":"%s","issues_count":%d,"warnings_count":%d,"issues":[%s],"warnings":[%s]}\n' \
        "$(date -Iseconds)" "$status" "$ISSUES_FOUND" "$WARNINGS_FOUND" \
        "$(printf '"%s",' "${ISSUES[@]}" | sed 's/,$//')" \
        "$(printf '"%s",' "${WARNINGS[@]}" | sed 's/,$//')"
}

output_cron() {
    if [[ $ISSUES_FOUND -gt 0 || $WARNINGS_FOUND -gt 0 ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Issues: $ISSUES_FOUND, Warnings: $WARNINGS_FOUND"
        printf "  ERROR: %s\n" "${ISSUES[@]}"
        printf "  WARN: %s\n" "${WARNINGS[@]}"
        [[ $ISSUES_FOUND -gt 0 ]] && send_notification "Farmhand Alert" "$ISSUES_FOUND issue(s) detected" "critical"
    fi
}

main() {
    local mode="once"
    while [[ $# -gt 0 ]]; do
        case $1 in
            --watch) mode="watch"; shift ;;
            --cron) OUTPUT_MODE="cron"; RED="" YELLOW="" GREEN="" BLUE="" NC=""; shift ;;
            --json) OUTPUT_MODE="json"; shift ;;
            --help|-h) usage; exit 0 ;;
            *) echo "Unknown option: $1"; usage; exit 1 ;;
        esac
    done

    if [[ "$mode" == "watch" ]]; then
        echo "Watching Farmhand health (Ctrl+C to stop)..."
        while true; do run_checks; output_$OUTPUT_MODE; sleep "$WATCH_INTERVAL"; done
    else
        run_checks
        case $OUTPUT_MODE in json) output_json ;; cron) output_cron ;; *) output_terminal ;; esac
    fi
    [[ $ISSUES_FOUND -gt 0 ]] && exit 2
    [[ $WARNINGS_FOUND -gt 0 ]] && exit 1
    exit 0
}

main "$@"
