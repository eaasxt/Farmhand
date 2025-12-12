#!/usr/bin/env bash
set -euo pipefail

# Install bd (beads), bv (beads-viewer), qmd

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Ensure PATH includes required directories
export PATH="/home/linuxbrew/.linuxbrew/bin:$HOME/.bun/bin:$HOME/.local/bin:$PATH"
export BUN_INSTALL="$HOME/.bun"

# Create directories
mkdir -p ~/.local/bin ~/.beads

# ============================================
# bd (beads CLI)
# ============================================
if ! command -v bd &>/dev/null; then
    echo "==> Installing bd..."

    # Download the latest bd binary from GitHub releases
    # Note: Update this URL when new versions are released
    BD_VERSION="0.2.0"
    BD_URL="https://github.com/Dicklesworthstone/beads/releases/download/v${BD_VERSION}/bd-linux-amd64"

    if curl -fsSL -o ~/.local/bin/bd "$BD_URL" 2>/dev/null; then
        chmod +x ~/.local/bin/bd
        echo "    Downloaded bd v${BD_VERSION}"
    else
        echo "    WARNING: Could not download bd automatically."
        echo "    Please download manually from: https://github.com/Dicklesworthstone/beads/releases"
        echo "    Place the binary at: ~/.local/bin/bd"
    fi
else
    echo "==> bd already installed"
fi

# Initialize beads database
if [[ ! -f ~/.beads/beads.db ]]; then
    echo "==> Initializing beads database..."
    export BEADS_DB=~/.beads/beads.db

    # Copy default config
    if [[ -f "$REPO_DIR/config/beads/config.yaml" ]]; then
        cp "$REPO_DIR/config/beads/config.yaml" ~/.beads/config.yaml
    fi

    # Initialize if bd is available
    if command -v bd &>/dev/null; then
        bd init 2>/dev/null || true
    fi
fi

# ============================================
# bv (beads-viewer)
# ============================================
if ! command -v bv &>/dev/null; then
    echo "==> Installing bv via Homebrew..."
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

    # bv is available via homebrew tap
    brew tap dicklesworthstone/beads 2>/dev/null || true
    brew install beads-viewer 2>/dev/null || {
        echo "    WARNING: Could not install bv via Homebrew."
        echo "    It may need to be installed manually."
    }
else
    echo "==> bv already installed"
fi

# ============================================
# qmd (markdown search)
# ============================================
if ! command -v qmd &>/dev/null; then
    echo "==> Installing qmd..."

    # Install via bun globally
    bun install -g https://github.com/tobi/qmd

    # Create wrapper script in ~/.local/bin
    cat > ~/.local/bin/qmd << 'EOF'
#!/bin/bash
# qmd - Quick Markdown Search
exec /home/ubuntu/.bun/bin/bun /home/ubuntu/.bun/install/global/node_modules/qmd/qmd.ts "$@"
EOF
    chmod +x ~/.local/bin/qmd
else
    echo "==> qmd already installed"
fi

# ============================================
# Claude Code (via Homebrew)
# ============================================
if ! command -v claude &>/dev/null; then
    echo "==> Installing Claude Code..."
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    brew install claude-code
else
    echo "==> Claude Code already installed"
fi

echo "==> Tools installed"
