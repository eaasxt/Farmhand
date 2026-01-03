#!/usr/bin/env bash
#
# Farmhand Path Manager
#
# Intelligent PATH management for dependency installation phases.
# Fixes Node.js/fnm PATH not refreshed between phases causing silent failures.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Comprehensive PATH refresh handling all tool dependencies
refresh_all_paths() {
    local verbose=${1:-false}
    
    if [[ "$verbose" == "true" ]]; then
        echo -e "${BLUE}Refreshing all PATH environments...${NC}"
    fi
    
    # Standard Farmhand paths
    export PATH="$HOME/.local/bin:$HOME/.bun/bin:$HOME/.cargo/bin:$PATH"
    
    # Homebrew (Linux) - with fallback detection
    if [[ -f /home/linuxbrew/.linuxbrew/bin/brew ]]; then
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        if [[ "$verbose" == "true" ]]; then
            echo "  ✓ Homebrew environment loaded"
        fi
    elif [[ -d /home/linuxbrew/.linuxbrew/bin ]]; then
        export PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH"
        if [[ "$verbose" == "true" ]]; then
            echo "  ✓ Homebrew PATH added"
        fi
    fi
    
    # Node.js via fnm - CRITICAL FIX
    # This was the missing piece causing phase 3/4 failures
    if [[ -f "$HOME/.local/share/fnm/fnm" ]]; then
        export PATH="$HOME/.local/share/fnm:$PATH"
        
        # Load fnm environment if available
        if command -v fnm >/dev/null 2>&1; then
            eval "$(fnm env --shell bash 2>/dev/null)" || true
            if [[ "$verbose" == "true" ]]; then
                echo "  ✓ fnm environment loaded"
            fi
        fi
    fi
    
    # Manual Node.js detection (if fnm installed but not in PATH)
    if [[ -d "$HOME/.local/share/fnm/installations" ]]; then
        # Find the most recent Node installation
        local latest_node=$(find "$HOME/.local/share/fnm/installations" -maxdepth 1 -type d -name "node-v*" | sort -V | tail -1)
        if [[ -n "$latest_node" && -d "$latest_node/bin" ]]; then
            export PATH="$latest_node/bin:$PATH"
            if [[ "$verbose" == "true" ]]; then
                echo "  ✓ Node.js added: $(basename "$latest_node")"
            fi
        fi
    fi
    
    # Rust/Cargo environment
    if [[ -f "$HOME/.cargo/env" ]]; then
        source "$HOME/.cargo/env" 2>/dev/null || true
        if [[ "$verbose" == "true" ]]; then
            echo "  ✓ Cargo environment loaded"
        fi
    fi
    
    # Python/uv environment
    if [[ -d "$HOME/.local/bin" ]]; then
        export PATH="$HOME/.local/bin:$PATH"
        if [[ "$verbose" == "true" ]]; then
            echo "  ✓ Python/uv PATH added"
        fi
    fi
    
    # Go environment (if installed)
    if [[ -d "$HOME/go/bin" ]]; then
        export PATH="$HOME/go/bin:$PATH"
        if [[ "$verbose" == "true" ]]; then
            echo "  ✓ Go PATH added"
        fi
    fi
    
    # Clear bash command cache to pick up new tools
    hash -r 2>/dev/null || true
    
    if [[ "$verbose" == "true" ]]; then
        echo -e "${GREEN}PATH refresh complete${NC}"
    fi
}

# Verify a tool is accessible in PATH - CRITICAL for dependency checks
require_tool() {
    local tool=$1
    local phase=${2:-"unknown"}
    local timeout=${3:-5}
    
    # Quick check with timeout (sometimes tools hang)
    if timeout "$timeout" command -v "$tool" &>/dev/null; then
        return 0
    else
        echo -e "${RED}FATAL: Required tool '$tool' not found in PATH${NC}" >&2
        echo -e "  Phase: $phase" >&2
        echo -e "  Current PATH:" >&2
        echo -e "    $PATH" | tr ':' '\n' | sed 's/^/    /' >&2
        echo "" >&2
        echo -e "  Troubleshooting:" >&2
        echo -e "    1. Check if $tool was installed in previous phase" >&2
        echo -e "    2. Run: refresh_all_paths true" >&2
        echo -e "    3. Verify manually: which $tool" >&2
        return 1
    fi
}

# Verify multiple tools at once
require_tools() {
    local phase=${1:-"unknown"}
    shift
    local tools=("$@")
    local failed_tools=()
    
    for tool in "${tools[@]}"; do
        if ! require_tool "$tool" "$phase" 2>/dev/null; then
            failed_tools+=("$tool")
        fi
    done
    
    if [[ ${#failed_tools[@]} -gt 0 ]]; then
        echo -e "${RED}FATAL: Missing required tools in phase '$phase':${NC}" >&2
        printf "  - %s\n" "${failed_tools[@]}" >&2
        echo "" >&2
        echo -e "Run: refresh_all_paths true" >&2
        return 1
    fi
    
    return 0
}

# Show current PATH status for debugging
show_path_status() {
    echo -e "${BLUE}Current PATH Status:${NC}"
    echo ""
    echo "PATH directories:"
    echo "$PATH" | tr ':' '\n' | nl -w2 -s': '
    echo ""
    echo "Key tool locations:"
    
    local tools=("node" "npm" "bun" "cargo" "brew" "python3" "uv" "fnm" "go")
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo -e "  ✓ $tool: $(command -v "$tool")"
        else
            echo -e "  ✗ $tool: not found"
        fi
    done
    echo ""
}

# Debug specific PATH issue
debug_tool_path() {
    local tool=$1
    
    echo -e "${BLUE}Debugging PATH for: $tool${NC}"
    echo ""
    
    # Check if tool exists anywhere
    local found_paths=($(find "$HOME" -name "$tool" -type f -executable 2>/dev/null | head -5))
    
    if [[ ${#found_paths[@]} -gt 0 ]]; then
        echo "Found $tool installations:"
        for path in "${found_paths[@]}"; do
            echo "  $(ls -la "$path")"
        done
        echo ""
        
        # Check if any are in PATH
        echo "PATH analysis:"
        local in_path=false
        for path in "${found_paths[@]}"; do
            local dir=$(dirname "$path")
            if [[ ":$PATH:" == *":$dir:"* ]]; then
                echo -e "  ✓ $dir (in PATH)"
                in_path=true
            else
                echo -e "  ✗ $dir (not in PATH)"
            fi
        done
        
        if [[ "$in_path" == "false" ]]; then
            echo ""
            echo -e "${YELLOW}Solution: Add directory to PATH or run refresh_all_paths${NC}"
        fi
    else
        echo -e "${RED}$tool not found anywhere in $HOME${NC}"
        echo "  Tool may not be installed"
    fi
}

# Export functions for use in phase scripts
