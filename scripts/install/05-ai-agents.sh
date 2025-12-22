#!/usr/bin/env bash
# 05-ai-agents.sh - AI Coding Agents
# Claude Code (via homebrew), Codex CLI, Gemini CLI
# Also installs Node.js via fnm for Codex compatibility

set -euo pipefail

echo "[5/9] Installing AI Coding Agents..."

# Node.js via fnm (needed for Codex)
if ! command -v node &>/dev/null; then
    echo "    Installing Node.js via fnm..."
    # Install fnm
    curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell

    # Setup fnm and install node
    export PATH="$HOME/.local/share/fnm:$PATH"
    eval "$(fnm env --shell bash)"
    fnm install --lts
    fnm default lts-latest

    # Create symlinks in ~/.local/bin for easy access
    mkdir -p ~/.local/bin
    ln -sf "$HOME/.local/share/fnm/node-versions/$(fnm current)/installation/bin/node" ~/.local/bin/node
    ln -sf "$HOME/.local/share/fnm/node-versions/$(fnm current)/installation/bin/npm" ~/.local/bin/npm
    ln -sf "$HOME/.local/share/fnm/node-versions/$(fnm current)/installation/bin/npx" ~/.local/bin/npx

    echo "    Node.js installed: $(node --version)"
else
    echo "    Node.js already installed: $(node --version)"
fi

# Claude Code
if ! command -v claude &>/dev/null; then
    echo "    Installing Claude Code..."
    if command -v brew &>/dev/null; then
        brew install claude-code
    else
        # Fallback to bun
        bun install -g @anthropic-ai/claude-code
    fi
    echo "    Claude Code installed: $(claude --version 2>&1 | head -1)"
else
    echo "    Claude Code already installed: $(claude --version 2>&1 | head -1)"
fi

# Codex CLI
if ! command -v codex &>/dev/null; then
    echo "    Installing Codex CLI..."
    bun install -g @openai/codex
    echo "    Codex installed: $(codex --version 2>&1 | head -1)"
else
    echo "    Codex already installed: $(codex --version 2>&1 | head -1)"
fi

# Gemini CLI
if ! command -v gemini &>/dev/null; then
    echo "    Installing Gemini CLI..."
    bun install -g @anthropic-ai/gemini-cli 2>/dev/null || bun install -g gemini-cli
    echo "    Gemini installed: $(gemini --version 2>&1 | head -1)"
else
    echo "    Gemini already installed: $(gemini --version 2>&1 | head -1)"
fi

echo "    AI Agents complete"
