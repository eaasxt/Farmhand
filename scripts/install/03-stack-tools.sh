#!/usr/bin/env bash
# 03-stack-tools.sh - Dicklesworthstone Stack (8 tools)
# ubs, ntm, cm, caam, slb, cass

set -euo pipefail

echo "[3/9] Installing Dicklesworthstone Stack..."

# UBS (Ultimate Bug Scanner)
if ! command -v ubs &>/dev/null; then
    echo "    Installing ubs..."
    curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/main/install.sh | bash
else
    echo "    ubs already installed: $(ubs --version 2>&1 | head -1)"
fi

# NTM (Named Tmux Manager)
if ! command -v ntm &>/dev/null; then
    echo "    Installing ntm..."
    curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/named_tmux_manager/main/install.sh | bash -s -- --easy-mode
else
    echo "    ntm already installed"
fi

# CM (CASS Memory System)
if ! command -v cm &>/dev/null; then
    echo "    Installing cm..."
    curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/cass_memory_system/main/install.sh | bash -s -- --easy-mode
else
    echo "    cm already installed: $(cm --version 2>&1 | head -1)"
fi

# CAAM (Coding Agent Account Manager)
if ! command -v caam &>/dev/null; then
    echo "    Installing caam..."
    curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_account_manager/main/install.sh | bash -s -- --easy-mode
else
    echo "    caam already installed"
fi

# SLB (Simultaneous Launch Button)
if ! command -v slb &>/dev/null; then
    echo "    Installing slb (building from source)..."
    if command -v go &>/dev/null; then
        TEMP_DIR=$(mktemp -d)
        git clone --depth 1 https://github.com/Dicklesworthstone/simultaneous_launch_button.git "$TEMP_DIR/slb" 2>/dev/null
        cd "$TEMP_DIR/slb"
        make build 2>/dev/null || go build -o slb ./cmd/slb
        mkdir -p ~/.local/bin
        cp slb ~/.local/bin/
        cd - >/dev/null
        rm -rf "$TEMP_DIR"
        echo "    slb built and installed"
    else
        echo "    WARNING: Go not installed, skipping slb"
    fi
else
    echo "    slb already installed"
fi

# CASS (Coding Agent Session Search) - Docker wrapper for GLIBC compatibility
if ! command -v cass &>/dev/null; then
    echo "    Installing cass (Docker wrapper for Ubuntu 22.04 compatibility)..."

    # Download binary to /opt/cass
    sudo mkdir -p /opt/cass
    TEMP_FILE=$(mktemp)
    curl -fsSL "https://github.com/Dicklesworthstone/coding_agent_session_search/releases/latest/download/coding-agent-search-x86_64-unknown-linux-gnu.tar.xz" -o "$TEMP_FILE"
    tar -xf "$TEMP_FILE" -C /tmp
    sudo cp /tmp/cass /opt/cass/cass 2>/dev/null || sudo cp /tmp/coding-agent-search-x86_64-unknown-linux-gnu/cass /opt/cass/cass
    sudo chmod +x /opt/cass/cass
    rm -f "$TEMP_FILE"

    # Copy wrapper script from repo
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    mkdir -p ~/.local/bin
    cp "$SCRIPT_DIR/../../bin/cass" ~/.local/bin/cass
    chmod +x ~/.local/bin/cass

    # Create data directory
    mkdir -p ~/.local/share/coding-agent-search

    echo "    cass installed with Docker wrapper"
else
    echo "    cass already installed: $(cass --version 2>&1 | head -1)"
fi

echo "    Stack tools complete"
