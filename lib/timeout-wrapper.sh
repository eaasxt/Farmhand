#!/usr/bin/env bash
#
# Farmhand Timeout Wrapper
#
# Robust timeout handling with progress monitoring and retry logic.
# Fixes Ollama model downloads hanging indefinitely on slow connections.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Run command with timeout, progress monitoring, and retry logic
run_with_timeout() {
    local timeout_secs=$1
    local name=$2
    local max_retries=${3:-1}
    shift 3
    local cmd=("$@")
    
    local attempt=1
    local start_time
    local elapsed
    
    while [[ $attempt -le $max_retries ]]; do
        if [[ $max_retries -gt 1 ]]; then
            echo -e "${BLUE}Starting: $name (attempt $attempt/$max_retries, timeout: ${timeout_secs}s)${NC}"
        else
            echo -e "${BLUE}Starting: $name (timeout: ${timeout_secs}s)${NC}"
        fi
        
        start_time=$(date +%s)
        
        # Run command with timeout in background
        timeout "$timeout_secs" "${cmd[@]}" &
        local pid=$!
        
        # Monitor progress every 10 seconds
        while kill -0 $pid 2>/dev/null; do
            sleep 10
            elapsed=$(( $(date +%s) - start_time ))
            echo "  ... still running (${elapsed}s elapsed, timeout at ${timeout_secs}s)"
        done
        
        # Wait for process and get exit code
        wait $pid
        local rc=$?
        
        elapsed=$(( $(date +%s) - start_time ))
        
        case $rc in
            0)
                echo -e "${GREEN}✓ Completed: $name (${elapsed}s)${NC}"
                return 0
                ;;
            124)
                echo -e "${YELLOW}⏱ Timeout: $name exceeded ${timeout_secs}s limit${NC}"
                ;;
            *)
                echo -e "${YELLOW}⚠ Failed: $name (exit code: $rc, ${elapsed}s)${NC}"
                ;;
        esac
        
        # Check if we should retry
        if [[ $attempt -lt $max_retries ]]; then
            local wait_time=$(( attempt * 5 ))  # Exponential backoff
            echo -e "${YELLOW}  Retrying in ${wait_time}s...${NC}"
            sleep "$wait_time"
        fi
        
        ((attempt++))
    done
    
    echo -e "${RED}✗ Failed: $name after $max_retries attempts${NC}"
    return 1
}

# Specialized function for Ollama model downloads with progress tracking
ollama_pull_with_timeout() {
    local model=$1
    local timeout_secs=${2:-300}  # 5 minute default
    local progress_file="$HOME/.farmhand/ollama-progress-$model.log"
    
    # Ensure progress directory exists
    mkdir -p "$(dirname "$progress_file")"
    
    echo -e "${BLUE}Downloading Ollama model: $model${NC}"
    
    # Start ollama pull with output capture
    timeout "$timeout_secs" ollama pull "$model" 2>&1 | tee "$progress_file" &
    local pid=$!
    local start_time=$(date +%s)
    
    # Monitor progress with more detailed feedback
    while kill -0 $pid 2>/dev/null; do
        sleep 15
        local elapsed=$(( $(date +%s) - start_time ))
        
        # Try to extract progress from log if available
        local progress=""
        if [[ -f "$progress_file" ]]; then
            progress=$(tail -1 "$progress_file" 2>/dev/null | grep -o '[0-9]\+%' | tail -1)
        fi
        
        if [[ -n "$progress" ]]; then
            echo "  ... downloading $model: $progress (${elapsed}s elapsed)"
        else
            echo "  ... downloading $model (${elapsed}s elapsed, timeout at ${timeout_secs}s)"
        fi
    done
    
    wait $pid
    local rc=$?
    local elapsed=$(( $(date +%s) - start_time ))
    
    case $rc in
        0)
            echo -e "${GREEN}✓ Downloaded: $model (${elapsed}s)${NC}"
            # Clean up progress file on success
            rm -f "$progress_file"
            return 0
            ;;
        124)
            echo -e "${RED}✗ Timeout: $model download exceeded ${timeout_secs}s${NC}"
            echo -e "  Progress log: $progress_file"
            return 124
            ;;
        *)
            echo -e "${RED}✗ Failed: $model download (exit code: $rc)${NC}"
            echo -e "  Progress log: $progress_file"
            return $rc
            ;;
    esac
}

# Network operation with exponential backoff
network_retry() {
    local max_retries=${1:-3}
    local base_delay=${2:-2}
    shift 2
    local cmd=("$@")
    
    local attempt=1
    while [[ $attempt -le $max_retries ]]; do
        if [[ $attempt -gt 1 ]]; then
            local delay=$(( base_delay ** (attempt - 1) ))
            echo -e "${YELLOW}  Network retry $attempt/$max_retries after ${delay}s delay...${NC}"
            sleep "$delay"
        fi
        
        if "${cmd[@]}"; then
            return 0
        fi
        
        ((attempt++))
    done
    
    echo -e "${RED}✗ Network operation failed after $max_retries attempts${NC}"
    return 1
}

# Service startup with health check
wait_for_service() {
    local service_name=$1
    local health_check_cmd=$2
    local timeout_secs=${3:-120}
    local check_interval=${4:-5}
    
    echo -e "${BLUE}Waiting for $service_name to start...${NC}"
    
    local elapsed=0
    while [[ $elapsed -lt $timeout_secs ]]; do
        if eval "$health_check_cmd" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready (${elapsed}s)${NC}"
            return 0
        fi
        
        sleep "$check_interval"
        elapsed=$(( elapsed + check_interval ))
        
        if [[ $((elapsed % 30)) -eq 0 ]]; then
            echo "  ... waiting for $service_name (${elapsed}s elapsed)"
        fi
    done
    
    echo -e "${RED}✗ Timeout: $service_name did not start within ${timeout_secs}s${NC}"
    echo -e "  Health check: $health_check_cmd"
    return 1
}

# Download with progress and resume capability
download_with_progress() {
    local url=$1
    local output_file=$2
    local timeout_secs=${3:-300}
    local max_retries=${4:-3}
    
    echo -e "${BLUE}Downloading: $(basename "$url")${NC}"
    
    # Try curl first (with resume), then wget fallback
    if command -v curl >/dev/null; then
        run_with_timeout "$timeout_secs" "curl download" "$max_retries" \
            curl -L -C - --progress-bar -o "$output_file" "$url"
    elif command -v wget >/dev/null; then
        run_with_timeout "$timeout_secs" "wget download" "$max_retries" \
            wget --continue --progress=bar -O "$output_file" "$url"
    else
        echo -e "${RED}✗ No download tool available (curl or wget required)${NC}"
        return 1
    fi
}

# Show active timeouts for debugging
show_timeout_status() {
    echo -e "${BLUE}Active Timeouts and Long-Running Processes:${NC}"
    echo ""
    
    # Show any ollama processes
    if pgrep -f ollama >/dev/null; then
        echo "Ollama processes:"
        pgrep -f ollama | while read pid; do
            local cmd=$(ps -p "$pid" -o cmd= 2>/dev/null)
            echo "  PID $pid: $cmd"
        done
        echo ""
    fi
    
    # Show progress files
    if [[ -d "$HOME/.farmhand" ]]; then
        local progress_files=($(find "$HOME/.farmhand" -name "ollama-progress-*.log" 2>/dev/null))
        if [[ ${#progress_files[@]} -gt 0 ]]; then
            echo "Download progress files:"
            for file in "${progress_files[@]}"; do
                local model=$(basename "$file" | sed 's/ollama-progress-//' | sed 's/.log$//')
                local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
                echo "  $model: $file (${size} bytes)"
            done
            echo ""
        fi
    fi
    
    echo "For detailed monitoring, use: watch -n 5 'ps aux | grep -E \"(ollama|curl|wget)\"'"
}

# Export functions for use in phase scripts
export -f run_with_timeout
export -f ollama_pull_with_timeout
export -f network_retry
export -f wait_for_service
export -f download_with_progress
export -f show_timeout_status
