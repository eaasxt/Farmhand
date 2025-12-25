#!/usr/bin/env bash
set -euo pipefail

# Install enforcement hooks for Claude Code
# This script is called by install.sh

# Use local variables to avoid clobbering parent's SCRIPT_DIR when sourced
_SCRIPT_DIR_09="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_DIR_09="$(dirname "$(dirname "$_SCRIPT_DIR_09")")"
INSTALL_HOME="${INSTALL_HOME:-$HOME}"

echo "Installing enforcement hooks..."

# Create directories
mkdir -p "$INSTALL_HOME/.claude/hooks"
mkdir -p "$INSTALL_HOME/.local/bin"

# Copy hooks
cp "$_REPO_DIR_09/hooks/"*.py "$INSTALL_HOME/.claude/hooks/"
chmod +x "$INSTALL_HOME/.claude/hooks/"*.py

# Copy bd-cleanup utility
cp "$_REPO_DIR_09/bin/bd-cleanup" "$INSTALL_HOME/.local/bin/"
chmod +x "$INSTALL_HOME/.local/bin/bd-cleanup"

# Install settings.json from template with __HOME__ substitution
SETTINGS_FILE="$INSTALL_HOME/.claude/settings.json"
TEMPLATE_FILE="$_REPO_DIR_09/config/claude-settings.json"

if [ -f "$SETTINGS_FILE" ]; then
    echo "  Backing up existing settings.json"
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
fi

if [ -f "$TEMPLATE_FILE" ]; then
    # Use template file with __HOME__ substitution
    sed "s|__HOME__|$INSTALL_HOME|g" "$TEMPLATE_FILE" > "$SETTINGS_FILE"
    echo "  Installed settings.json from template with HOME=$INSTALL_HOME"
else
    echo "  Warning: Template not found at $TEMPLATE_FILE"
    echo "  Generating settings.json inline..."
    # Fallback: generate inline (for backwards compatibility)
    cat > "$SETTINGS_FILE" << SETTINGS
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "$INSTALL_HOME/.claude/hooks/todowrite-interceptor.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "$INSTALL_HOME/.claude/hooks/reservation-checker.py",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$INSTALL_HOME/.claude/hooks/git_safety_guard.py",
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
            "command": "$INSTALL_HOME/.claude/hooks/mcp-state-tracker.py",
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
            "command": "$INSTALL_HOME/.claude/hooks/session-init.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
SETTINGS
fi

echo "  Installed hooks to $INSTALL_HOME/.claude/hooks/"
echo "  Installed bd-cleanup to $INSTALL_HOME/.local/bin/"
echo "  Configured $SETTINGS_FILE"

# Install git pre-commit hook for UBS scanning
GIT_HOOKS_SRC="$_REPO_DIR_09/config/git-hooks"
if [[ -f "$GIT_HOOKS_SRC/pre-commit" ]]; then
    # Create global git hooks directory
    mkdir -p "$INSTALL_HOME/.config/git/hooks"
    cp "$GIT_HOOKS_SRC/pre-commit" "$INSTALL_HOME/.config/git/hooks/"
    chmod +x "$INSTALL_HOME/.config/git/hooks/pre-commit"

    # Configure git to use the global hooks directory
    git config --global core.hooksPath "$INSTALL_HOME/.config/git/hooks"
    echo "  Installed UBS pre-commit hook to $INSTALL_HOME/.config/git/hooks/"
    echo "  Configured global git hooks path"
fi

echo "Enforcement hooks installed."
