#!/usr/bin/env bash
# 05-ai-agents.sh - AI Coding Agents
# Claude Code (via homebrew), Codex CLI, Gemini CLI
# Node.js is installed earlier in 02-core-tools.sh

# NOTE: Don't use set -e here - we're sourced by install.sh and want graceful failures
# set -euo pipefail

echo "[5/9] Installing AI Coding Agents..."

# Refresh PATH to pick up Node.js from 02-core-tools.sh
export PATH="$HOME/.local/bin:$HOME/.local/share/fnm:$PATH"
if command -v fnm &>/dev/null; then
    eval "$(fnm env --shell bash 2>/dev/null)" || true
fi

# Check Node.js availability
if ! command -v node &>/dev/null; then
    echo "    WARNING: Node.js not found in PATH. Some tools may not install."
    echo "    Try running: source ~/.zshrc && rerun this script"
else
    echo "    Node.js available: $(node --version)"
fi

# Claude Code
if ! command -v claude &>/dev/null; then
    echo "    Installing Claude Code..."
    if command -v brew &>/dev/null; then
        brew install claude-code 2>/dev/null || echo "    WARNING: Claude Code install failed"
    else
        # Fallback to bun
        bun install -g @anthropic-ai/claude-code 2>/dev/null || echo "    WARNING: Claude Code install failed"
    fi
    if command -v claude &>/dev/null; then
        echo "    Claude Code installed: $(claude --version 2>&1 | head -1)"
    fi
else
    echo "    Claude Code already installed: $(claude --version 2>&1 | head -1)"
fi

# Codex CLI - optional, don't fail if unavailable
if ! command -v codex &>/dev/null; then
    echo "    Installing Codex CLI..."
    if bun install -g @openai/codex 2>/dev/null; then
        echo "    Codex installed: $(codex --version 2>&1 | head -1)"
    else
        echo "    WARNING: Codex install failed (optional tool, continuing)"
    fi
else
    echo "    Codex already installed: $(codex --version 2>&1 | head -1)"
fi

# Gemini CLI - optional, don't fail if unavailable
if ! command -v gemini &>/dev/null; then
    echo "    Installing Gemini CLI..."
    if bun install -g @google/gemini-cli 2>/dev/null; then
        echo "    Gemini installed: $(gemini --version 2>&1 | head -1)"
    else
        echo "    WARNING: Gemini install failed (optional tool, continuing)"
    fi
else
    echo "    Gemini already installed: $(gemini --version 2>&1 | head -1)"
fi

# Configure Gemini settings (hideWindowTitle prevents NTM pane title conflicts)
GEMINI_SETTINGS="$HOME/.gemini/settings.json"
if command -v gemini &>/dev/null; then
    mkdir -p "$HOME/.gemini"
    if [[ -f "$GEMINI_SETTINGS" ]]; then
        # Check if hideWindowTitle is already set
        if ! grep -q "hideWindowTitle" "$GEMINI_SETTINGS" 2>/dev/null; then
            # Add ui.hideWindowTitle to existing settings
            if command -v jq &>/dev/null; then
                jq '. + {"ui": {"hideWindowTitle": true}}' "$GEMINI_SETTINGS" > "$GEMINI_SETTINGS.tmp" && \
                    mv "$GEMINI_SETTINGS.tmp" "$GEMINI_SETTINGS"
                echo "    Configured Gemini: hideWindowTitle=true"
            else
                echo "    WARNING: jq not available, Gemini hideWindowTitle not set"
            fi
        fi
    else
        # Create new settings file
        cat > "$GEMINI_SETTINGS" << 'EOF'
{
  "ui": {
    "hideWindowTitle": true
  }
}
EOF
        echo "    Created Gemini settings with hideWindowTitle=true"
    fi
fi

echo "    AI Agents complete"
