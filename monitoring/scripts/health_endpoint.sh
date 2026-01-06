#!/bin/bash

# Gas Town MEOW Stack - Health Check Endpoint
# HTTP health check endpoint for production monitoring

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_ROOT="$(dirname "$SCRIPT_DIR")"
HEALTH_SCRIPT="$SCRIPT_DIR/health_check.sh"
PORT="${1:-8766}"
LOG_FILE="$MONITORING_ROOT/logging/health_endpoint.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Generate JSON health response
generate_health_json() {
    local health_result

    # Run health check and capture output and exit code
    if health_result=$("$HEALTH_SCRIPT" --quiet 2>&1); then
        local status="healthy"
        local exit_code=0
    else
        local exit_code=$?
        case $exit_code in
            1) local status="degraded" ;;
            2) local status="critical" ;;
            *) local status="unknown" ;;
        esac
    fi

    # Get current timestamp
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')

    # Get basic system info
    local uptime_seconds=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo "0")
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | tr -d ' ')

    # Service checks
    local mcp_status="unknown"
    if curl -s --max-time 3 http://localhost:8765/health > /dev/null 2>&1; then
        mcp_status="healthy"
    else
        mcp_status="critical"
    fi

    local ollama_status="unknown"
    if curl -s --max-time 3 http://localhost:11434/api/tags > /dev/null 2>&1; then
        ollama_status="healthy"
    else
        ollama_status="critical"
    fi

    # Database checks
    local beads_status="unknown"
    if [[ -f "/home/ubuntu/.beads/beads.db" ]] && sqlite3 "/home/ubuntu/.beads/beads.db" "SELECT 1;" > /dev/null 2>&1; then
        beads_status="healthy"
    else
        beads_status="critical"
    fi

    local agent_mail_db_status="unknown"
    if [[ -f "/home/ubuntu/mcp_agent_mail/storage.sqlite3" ]] && sqlite3 "/home/ubuntu/mcp_agent_mail/storage.sqlite3" "SELECT 1;" > /dev/null 2>&1; then
        agent_mail_db_status="healthy"
    else
        agent_mail_db_status="critical"
    fi

    # Generate JSON response
    cat << EOF
{
  "timestamp": "$timestamp",
  "status": "$status",
  "exit_code": $exit_code,
  "version": "1.0.0",
  "uptime_seconds": $uptime_seconds,
  "load_average": "$load_avg",
  "services": {
    "mcp_agent_mail": {
      "status": "$mcp_status",
      "url": "http://localhost:8765"
    },
    "ollama": {
      "status": "$ollama_status",
      "url": "http://localhost:11434"
    }
  },
  "databases": {
    "beads": {
      "status": "$beads_status",
      "path": "/home/ubuntu/.beads/beads.db"
    },
    "agent_mail": {
      "status": "$agent_mail_db_status",
      "path": "/home/ubuntu/mcp_agent_mail/storage.sqlite3"
    }
  },
  "stack_components": {
    "beads_system": {
      "status": "$(command -v bd &> /dev/null && echo "healthy" || echo "critical")"
    },
    "claude_hooks": {
      "status": "$([[ -d "/home/ubuntu/.claude/hooks" ]] && echo "healthy" || echo "critical")"
    },
    "molecule_marketplace": {
      "status": "$([[ -f "/home/ubuntu/projects/deere/molecule-marketplace/marketplace.db" ]] && echo "healthy" || echo "degraded")"
    }
  },
  "production_readiness": {
    "score": $(calculate_readiness_score),
    "status": "$(get_readiness_status)"
  }
}
EOF
}

# Calculate production readiness score
calculate_readiness_score() {
    local score=0

    # Critical services (40 points)
    curl -s --max-time 3 http://localhost:8765/health > /dev/null 2>&1 && score=$((score + 20))
    curl -s --max-time 3 http://localhost:11434/api/tags > /dev/null 2>&1 && score=$((score + 20))

    # Critical databases (30 points)
    [[ -f "/home/ubuntu/.beads/beads.db" ]] && sqlite3 "/home/ubuntu/.beads/beads.db" "SELECT 1;" > /dev/null 2>&1 && score=$((score + 15))
    [[ -f "/home/ubuntu/mcp_agent_mail/storage.sqlite3" ]] && sqlite3 "/home/ubuntu/mcp_agent_mail/storage.sqlite3" "SELECT 1;" > /dev/null 2>&1 && score=$((score + 15))

    # MEOW stack components (20 points)
    command -v bd &> /dev/null && score=$((score + 5))
    [[ -d "/home/ubuntu/.claude/hooks" ]] && score=$((score + 5))
    [[ -f "/home/ubuntu/projects/deere/molecule-marketplace/marketplace.db" ]] && score=$((score + 5))
    [[ -f "/home/ubuntu/projects/deere/monitoring/scripts/health_check.sh" ]] && score=$((score + 5))

    # System health (10 points)
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | head -1)
    [[ -n "$cpu_usage" ]] && (( $(echo "$cpu_usage < 80" | bc -l) )) && score=$((score + 5))

    local mem_total=$(free | grep '^Mem:' | awk '{print $2}')
    local mem_used=$(free | grep '^Mem:' | awk '{print $3}')
    local mem_usage=$(echo "scale=1; $mem_used * 100 / $mem_total" | bc)
    (( $(echo "$mem_usage < 85" | bc -l) )) && score=$((score + 5))

    echo $score
}

# Get readiness status based on score
get_readiness_status() {
    local score=$(calculate_readiness_score)

    if [[ $score -ge 95 ]]; then
        echo "production_ready"
    elif [[ $score -ge 80 ]]; then
        echo "mostly_ready"
    elif [[ $score -ge 60 ]]; then
        echo "needs_attention"
    else
        echo "not_ready"
    fi
}

# Generate Prometheus metrics
generate_prometheus_metrics() {
    local timestamp=$(date +%s)

    # System metrics
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | head -1)
    [[ -z "$cpu_usage" ]] && cpu_usage=$(vmstat 1 2 | tail -1 | awk '{print 100-$15}')

    local mem_total=$(free | grep '^Mem:' | awk '{print $2}')
    local mem_used=$(free | grep '^Mem:' | awk '{print $3}')
    local mem_usage=$(echo "scale=2; $mem_used * 100 / $mem_total" | bc)

    local disk_usage=$(df / | grep -v Filesystem | awk '{print $5}' | sed 's/%//g')

    echo "# HELP meow_stack_cpu_usage_percent Current CPU usage percentage"
    echo "# TYPE meow_stack_cpu_usage_percent gauge"
    echo "meow_stack_cpu_usage_percent $cpu_usage"

    echo "# HELP meow_stack_memory_usage_percent Current memory usage percentage"
    echo "# TYPE meow_stack_memory_usage_percent gauge"
    echo "meow_stack_memory_usage_percent $mem_usage"

    echo "# HELP meow_stack_disk_usage_percent Current disk usage percentage"
    echo "# TYPE meow_stack_disk_usage_percent gauge"
    echo "meow_stack_disk_usage_percent $disk_usage"

    # Service status metrics (1 = healthy, 0 = unhealthy)
    local mcp_healthy=0
    curl -s --max-time 3 http://localhost:8765/health > /dev/null 2>&1 && mcp_healthy=1

    local ollama_healthy=0
    curl -s --max-time 3 http://localhost:11434/api/tags > /dev/null 2>&1 && ollama_healthy=1

    echo "# HELP meow_stack_service_healthy Service health status"
    echo "# TYPE meow_stack_service_healthy gauge"
    echo "meow_stack_service_healthy{service=\"mcp_agent_mail\"} $mcp_healthy"
    echo "meow_stack_service_healthy{service=\"ollama\"} $ollama_healthy"

    # Production readiness score
    local readiness_score=$(calculate_readiness_score)
    echo "# HELP meow_stack_production_readiness_score Production readiness score out of 100"
    echo "# TYPE meow_stack_production_readiness_score gauge"
    echo "meow_stack_production_readiness_score $readiness_score"

    # Database status
    local beads_healthy=0
    [[ -f "/home/ubuntu/.beads/beads.db" ]] && sqlite3 "/home/ubuntu/.beads/beads.db" "SELECT 1;" > /dev/null 2>&1 && beads_healthy=1

    local agent_mail_db_healthy=0
    [[ -f "/home/ubuntu/mcp_agent_mail/storage.sqlite3" ]] && sqlite3 "/home/ubuntu/mcp_agent_mail/storage.sqlite3" "SELECT 1;" > /dev/null 2>&1 && agent_mail_db_healthy=1

    echo "# HELP meow_stack_database_healthy Database health status"
    echo "# TYPE meow_stack_database_healthy gauge"
    echo "meow_stack_database_healthy{database=\"beads\"} $beads_healthy"
    echo "meow_stack_database_healthy{database=\"agent_mail\"} $agent_mail_db_healthy"
}

# Handle HTTP request
handle_request() {
    local method="$1"
    local path="$2"

    case "$path" in
        "/health")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo "Cache-Control: no-cache"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            generate_health_json
            ;;
        "/health/detailed")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: application/json"
            echo "Cache-Control: no-cache"
            echo "Access-Control-Allow-Origin: *"
            echo ""
            generate_health_json
            ;;
        "/metrics")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: text/plain; version=0.0.4"
            echo "Cache-Control: no-cache"
            echo ""
            generate_prometheus_metrics
            ;;
        "/ping")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: text/plain"
            echo ""
            echo "pong"
            ;;
        "/")
            echo "HTTP/1.1 200 OK"
            echo "Content-Type: text/html"
            echo ""
            cat << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Gas Town MEOW Stack Health</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { padding: 20px; margin: 10px 0; border-radius: 5px; }
        .healthy { background: #d4edda; color: #155724; }
        .degraded { background: #fff3cd; color: #856404; }
        .critical { background: #f8d7da; color: #721c24; }
    </style>
    <script>
        function refreshHealth() {
            fetch('/health')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status.toUpperCase();
                    document.getElementById('status').className = 'status ' + data.status;
                    document.getElementById('timestamp').textContent = data.timestamp;
                    document.getElementById('readiness').textContent = data.production_readiness.score + '%';
                })
                .catch(error => console.error('Error:', error));
        }
        setInterval(refreshHealth, 5000);
    </script>
</head>
<body onload="refreshHealth()">
    <h1>Gas Town MEOW Stack Health Monitor</h1>
    <div id="status" class="status">Loading...</div>
    <p>Last updated: <span id="timestamp">-</span></p>
    <p>Production readiness: <span id="readiness">-</span></p>
    <h2>Endpoints:</h2>
    <ul>
        <li><a href="/health">/health</a> - JSON health status</li>
        <li><a href="/metrics">/metrics</a> - Prometheus metrics</li>
        <li><a href="/ping">/ping</a> - Simple ping check</li>
    </ul>
</body>
</html>
EOF
            ;;
        *)
            echo "HTTP/1.1 404 Not Found"
            echo "Content-Type: text/plain"
            echo ""
            echo "404 Not Found"
            ;;
    esac
}

# Simple HTTP server
start_server() {
    log "Starting health check endpoint server on port $PORT"

    if command -v nc > /dev/null; then
        # Use netcat if available
        while true; do
            {
                read -r method path protocol
                while IFS= read -r header; do
                    [[ "$header" =~ ^[[:space:]]*$ ]] && break
                done
                handle_request "$method" "$path"
            } | nc -l -p "$PORT" -q 1
        done
    else
        # Fallback to socat
        if command -v socat > /dev/null; then
            while true; do
                echo "$(generate_health_json)" | socat TCP-LISTEN:$PORT,reuseaddr,fork SYSTEM:'cat; echo "HTTP/1.1 200 OK"; echo "Content-Type: application/json"; echo ""; cat'
            done
        else
            log "ERROR: Neither netcat nor socat available. Cannot start HTTP server."
            exit 1
        fi
    fi
}

# Main function
main() {
    case "${1:-server}" in
        "server")
            start_server
            ;;
        "test")
            echo "Testing health check endpoint..."
            generate_health_json | python3 -m json.tool
            ;;
        "metrics")
            echo "Testing Prometheus metrics..."
            generate_prometheus_metrics
            ;;
        *)
            echo "Usage: $0 [server|test|metrics]"
            exit 1
            ;;
    esac
}

main "$@"