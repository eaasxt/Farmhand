#!/usr/bin/env bash
# 05-ai-agents.sh - AI Coding Agents
# Claude Code (via homebrew), Codex CLI, Gemini CLI
# Node.js is installed earlier in 02-core-tools.sh

set -euo pipefail

echo "[5/9] Installing AI Coding Agents..."

# Verify Node.js is available (installed in 02-core-tools.sh)
if ! command -v node &>/dev/null; then
    echo "    ERROR: Node.js not found. Should have been installed in 02-core-tools.sh"
    exit 1
else
    echo "    Node.js available: $(node --version)"
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
    bun install -g @google/gemini-cli
    echo "    Gemini installed: $(gemini --version 2>&1 | head -1)"
else
    echo "    Gemini already installed: $(gemini --version 2>&1 | head -1)"
fi

echo "    AI Agents complete"
