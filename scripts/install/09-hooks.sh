#!/usr/bin/env bash
set -euo pipefail

# Install enforcement hooks for Claude Code
# This script is called by install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing enforcement hooks..."

# Create directories
mkdir -p "$HOME/.claude/hooks"
mkdir -p "$HOME/.local/bin"

# Copy hooks
cp "$REPO_DIR/hooks/"*.py "$HOME/.claude/hooks/"
chmod +x "$HOME/.claude/hooks/"*.py

# Copy bd-cleanup utility
cp "$REPO_DIR/bin/bd-cleanup" "$HOME/.local/bin/"
chmod +x "$HOME/.local/bin/bd-cleanup"

# Install settings.json (expand $HOME in paths)
SETTINGS_FILE="$HOME/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
    echo "  Backing up existing settings.json"
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
fi

# Create settings with expanded paths
cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/todowrite-interceptor.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/reservation-checker.py",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__mcp-agent-mail__.*|register_agent|file_reservation_paths|release_file_reservations|macro_start_session",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/mcp-state-tracker.py",
            "timeout": 5
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/session-init.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
EOF

echo "  Installed hooks to $HOME/.claude/hooks/"
echo "  Installed bd-cleanup to $HOME/.local/bin/"
echo "  Configured $SETTINGS_FILE"
echo "Enforcement hooks installed."
