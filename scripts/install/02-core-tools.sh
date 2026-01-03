#!/usr/bin/env bash
# NOTE: Dont use set -e - sourced by install.sh
# set -euo pipefail

# Install bd (beads), bv (beads-viewer), qmd

# Use local variable to avoid clobbering parent's SCRIPT_DIR when sourced
_SCRIPT_DIR_02="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_DIR_02="$(dirname "$_SCRIPT_DIR_02")"

# Ensure PATH includes required directories
export PATH="/home/linuxbrew/.linuxbrew/bin:$HOME/.bun/bin:$HOME/.local/bin:$PATH"
export BUN_INSTALL="$HOME/.bun"

# Create directories
mkdir -p ~/.local/bin ~/.beads

# ============================================
# bd (beads CLI) - from steveyegge/beads
# ============================================
if ! command -v bd &>/dev/null; then
    echo "==> Installing bd..."

    # Download the latest bd binary from GitHub releases
    # Source: https://github.com/steveyegge/beads
    # v0.33+ introduces molecular bonding system (bd mol, bd cook, bd ship, etc.)
    BD_VERSION="0.36.0"
    BD_URL="https://github.com/steveyegge/beads/releases/download/v${BD_VERSION}/beads_${BD_VERSION}_linux_amd64.tar.gz"

    if curl -fsSL "$BD_URL" | tar -xz -C /tmp 2>/dev/null && [[ -f /tmp/bd ]]; then
        mv /tmp/bd ~/.local/bin/bd
        chmod +x ~/.local/bin/bd
        echo "    Downloaded bd v${BD_VERSION}"
    elif curl -fsSL -o ~/.local/bin/bd "https://github.com/steveyegge/beads/releases/download/v${BD_VERSION}/bd_linux_amd64" 2>/dev/null; then
        # Fallback to old naming convention
        chmod +x ~/.local/bin/bd
        echo "    Downloaded bd v${BD_VERSION} (alt URL)"
    else
        echo "    WARNING: Could not download bd automatically."
        echo "    Please download manually from: https://github.com/steveyegge/beads/releases"
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
    if [[ -f "$_REPO_DIR_02/config/beads/config.yaml" ]]; then
        cp "$_REPO_DIR_02/config/beads/config.yaml" ~/.beads/config.yaml
    fi

    # Initialize if bd is available
    if command -v bd &>/dev/null; then
        bd init 2>/dev/null || true
    fi
fi

# ============================================
# bv (beads-viewer) - from Dicklesworthstone/beads_viewer
# ============================================
if ! command -v bv &>/dev/null; then
    echo "==> Installing bv..."
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

    # Try Homebrew first
    if brew tap dicklesworthstone/beads 2>/dev/null && brew install beads-viewer 2>/dev/null; then
        echo "    Installed bv via Homebrew"
    else
        # Fallback: download binary from releases
        echo "    Homebrew failed, downloading binary..."
        # v0.11.0+ adds hybrid search with graph-aware ranking
        BV_VERSION="0.11.2"
        BV_URL="https://github.com/Dicklesworthstone/beads_viewer/releases/download/v${BV_VERSION}/bv_${BV_VERSION}_linux_amd64.tar.gz"

        if curl -fsSL "$BV_URL" | tar -xz -C /tmp 2>/dev/null && [[ -f /tmp/bv ]]; then
            mv /tmp/bv ~/.local/bin/bv
            chmod +x ~/.local/bin/bv
            echo "    Downloaded bv v${BV_VERSION}"
        elif curl -fsSL "https://github.com/Dicklesworthstone/beads_viewer/releases/download/v${BV_VERSION}/beads_viewer_linux_amd64.tar.gz" | tar -xz -C /tmp 2>/dev/null && [[ -f /tmp/bv ]]; then
            # Fallback to old naming convention
            mv /tmp/bv ~/.local/bin/bv
            chmod +x ~/.local/bin/bv
            echo "    Downloaded bv v${BV_VERSION} (alt URL)"
        else
            echo "    WARNING: Could not install bv automatically."
            echo "    Please download from: https://github.com/Dicklesworthstone/beads_viewer/releases"
        fi
    fi
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
    cat > ~/.local/bin/qmd << EOF
#!/bin/bash
# qmd - Quick Markdown Search
exec "$HOME/.bun/install/global/node_modules/qmd/qmd" "\$@"
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

    # Ensure claude is in ~/.local/bin for consistent PATH handling (ACFS backport)
    if [[ -x "/home/linuxbrew/.linuxbrew/bin/claude" ]] && [[ ! -L ~/.local/bin/claude ]]; then
        ln -sf "/home/linuxbrew/.linuxbrew/bin/claude" ~/.local/bin/claude
        echo "    Symlinked claude to ~/.local/bin"
    fi
else
    echo "==> Claude Code already installed"
fi

# ============================================
# Node.js via fnm (needed for cloud CLIs and Codex)
# ============================================
if ! command -v node &>/dev/null; then
    echo "==> Installing Node.js via fnm..."
    # Install fnm
    curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell

    # Setup fnm and install node
    export PATH="$HOME/.local/share/fnm:$PATH"
    eval "$(fnm env --shell bash)"
    fnm install --lts
    fnm default lts-latest

    # Create symlinks in ~/.local/bin for easy access
    ln -sf "$HOME/.local/share/fnm/node-versions/$(fnm current)/installation/bin/node" ~/.local/bin/node
    ln -sf "$HOME/.local/share/fnm/node-versions/$(fnm current)/installation/bin/npm" ~/.local/bin/npm
    ln -sf "$HOME/.local/share/fnm/node-versions/$(fnm current)/installation/bin/npx" ~/.local/bin/npx

    echo "    Node.js installed: $(~/.local/bin/node --version)"
else
    echo "==> Node.js already installed: $(node --version)"
fi

# ============================================
# Go (needed for slb - Simultaneous Launch Button)
# ============================================
if ! command -v go &>/dev/null; then
    echo "==> Installing Go..."
    if command -v brew &>/dev/null; then
        brew install go
        echo "    Go installed via Homebrew: $(go version)"
    else
        # Install from official tarball
        GO_VERSION="1.23.4"
        curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" | sudo tar -C /usr/local -xzf -
        export PATH=$PATH:/usr/local/go/bin
        echo "    Go installed: $(go version)"
    fi
else
    echo "==> Go already installed: $(go version)"
fi

echo "==> Tools installed"
