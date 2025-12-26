#!/usr/bin/env bash
# 03-stack-tools.sh - Dicklesworthstone Stack (8 tools)
# ubs, ntm, cm, caam, slb, cass, ast-grep

# NOTE: Don't use set -e here - we're sourced by install.sh and want graceful failures
# set -euo pipefail

echo "[3/9] Installing Dicklesworthstone Stack..."

# ast-grep (REQUIRED for UBS v5.0.0 JavaScript/TypeScript scanning)
if ! command -v ast-grep &>/dev/null && ! command -v sg &>/dev/null; then
    echo "    Installing ast-grep (required for UBS JS/TS scanning)..."

    # Try Homebrew first (most reliable - bun blocks postinstall scripts)
    if command -v brew &>/dev/null; then
        brew install ast-grep 2>/dev/null && echo "    ast-grep installed via Homebrew"
    # Try cargo
    elif command -v cargo &>/dev/null; then
        cargo install ast-grep --locked 2>/dev/null && echo "    ast-grep installed via cargo"
    # Try npm (bun blocks postinstall scripts which ast-grep needs)
    elif command -v npm &>/dev/null; then
        npm install -g @ast-grep/cli 2>/dev/null && echo "    ast-grep installed via npm"
    else
        echo "    ERROR: Cannot install ast-grep. Install brew, cargo, or npm first."
        echo "    ast-grep is REQUIRED for UBS v5.0.0 JavaScript/TypeScript scanning."
        exit 1
    fi
else
    echo "    ast-grep already installed"
fi

# UBS (Ultimate Bug Scanner) - v5.0.0+ requires ast-grep for JS/TS
if ! command -v ubs &>/dev/null; then
    echo "    Installing ubs..."
    curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/ultimate_bug_scanner/master/install.sh | bash -s -- --easy-mode
else
    echo "    ubs already installed: $(ubs --version 2>&1 | head -1)"
fi

# NTM (Named Tmux Manager)
if ! command -v ntm &>/dev/null; then
    echo "    Installing ntm..."
    curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/ntm/main/install.sh | bash -s -- --no-shell
else
    echo "    ntm already installed"
fi

# CM (CASS Memory System) - optional, don't fail install if unavailable
if ! command -v cm &>/dev/null; then
    echo "    Installing cm..."
    if curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/cass_memory_system/main/install.sh | bash -s -- --easy-mode 2>/dev/null; then
        echo "    cm installed"
    else
        echo "    WARNING: cm installation failed (optional tool, continuing)"
    fi
else
    echo "    cm already installed: $(cm --version 2>&1 | head -1)"
fi

# CAAM (Coding Agent Account Manager) - optional, don't fail install if unavailable
if ! command -v caam &>/dev/null; then
    echo "    Installing caam..."
    if curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_account_manager/main/install.sh | bash -s -- --easy-mode 2>/dev/null; then
        echo "    caam installed"
    else
        echo "    WARNING: caam installation failed (optional tool, continuing)"
    fi
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

# CASS (Coding Agent Session Search) - optional, requires GLIBC 2.39+
if ! command -v cass &>/dev/null; then
    echo "    Installing cass..."

    # Try to download and install binary
    if sudo mkdir -p /opt/cass 2>/dev/null; then
        TEMP_FILE=$(mktemp)
        if curl -fsSL "https://github.com/Dicklesworthstone/coding_agent_session_search/releases/latest/download/coding-agent-search-x86_64-unknown-linux-gnu.tar.xz" -o "$TEMP_FILE" 2>/dev/null; then
            tar -xf "$TEMP_FILE" -C /tmp 2>/dev/null || true
            if sudo cp /tmp/cass /opt/cass/cass 2>/dev/null || sudo cp /tmp/coding-agent-search-x86_64-unknown-linux-gnu/cass /opt/cass/cass 2>/dev/null; then
                sudo chmod +x /opt/cass/cass

                # Copy wrapper script from repo
                _SCRIPT_DIR_03="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
                mkdir -p ~/.local/bin
                if [ -f "$_SCRIPT_DIR_03/../../bin/cass" ]; then
                    cp "$_SCRIPT_DIR_03/../../bin/cass" ~/.local/bin/cass
                    chmod +x ~/.local/bin/cass
                fi

                # Create data directory
                mkdir -p ~/.local/share/coding-agent-search
                echo "    cass installed"
            else
                echo "    WARNING: cass binary extraction failed (optional tool, continuing)"
            fi
        else
            echo "    WARNING: cass download failed (optional tool, continuing)"
        fi
        rm -f "$TEMP_FILE"
    else
        echo "    WARNING: cass installation failed (optional tool, continuing)"
    fi
else
    echo "    cass already installed: $(cass --version 2>&1 | head -1)"
fi

echo "    Stack tools complete"
