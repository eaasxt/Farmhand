#!/usr/bin/env bash
# NOTE: Don't use set -e here - we're sourced by install.sh and want graceful failures
# set -euo pipefail

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

# Copy bin utilities to ~/.local/bin
for tool in bd-cleanup obs-mask farmhand-doctor mcp-query agent-cleanup; do
    if [[ -f "$_REPO_DIR_09/bin/$tool" ]]; then
        cp "$_REPO_DIR_09/bin/$tool" "$INSTALL_HOME/.local/bin/"
        chmod +x "$INSTALL_HOME/.local/bin/$tool"
    fi
done

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
    chmod 600 "$SETTINGS_FILE"  # Secure permissions - may contain sensitive hook config
    echo "  Installed settings.json from template with HOME=$INSTALL_HOME"
else
    echo "  Warning: Template not found at $TEMPLATE_FILE"
    echo "  Generating settings.json inline..."
    # Fallback: generate inline (for backwards compatibility)
    cat > "$SETTINGS_FILE" << SETTINGS
{
  "env": {
    "CLAUDE_CODE_DISABLE_TERMINAL_TITLE": "1"
  },
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
    chmod 600 "$SETTINGS_FILE"  # Secure permissions
fi

echo "  Installed hooks to $INSTALL_HOME/.claude/hooks/"
echo "  Installed bin tools to $INSTALL_HOME/.local/bin/"
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

# Set secure file permissions
echo "  Setting secure file permissions..."

# Hooks directory - executable by owner only
chmod 700 "$INSTALL_HOME/.claude/hooks"

# State files - read/write by owner only
if [ -f "$INSTALL_HOME/.claude/agent-state.json" ]; then
    chmod 600 "$INSTALL_HOME/.claude/agent-state.json"
fi

# Credentials file (if exists) - read/write by owner only
if [ -f "$INSTALL_HOME/.claude/.credentials.json" ]; then
    chmod 600 "$INSTALL_HOME/.claude/.credentials.json"
fi

# MCP Agent Mail env file (if exists)
if [ -f "$INSTALL_HOME/mcp_agent_mail/.env" ]; then
    chmod 600 "$INSTALL_HOME/mcp_agent_mail/.env"
fi

# Beads database (if exists)
if [ -f "$INSTALL_HOME/.beads/beads.db" ]; then
    chmod 600 "$INSTALL_HOME/.beads/beads.db"
fi

# Install CLAUDE.md to home directory
echo "  Installing CLAUDE.md..."
if [ -f "$_REPO_DIR_09/config/CLAUDE.md" ]; then
    cp "$_REPO_DIR_09/config/CLAUDE.md" "$INSTALL_HOME/CLAUDE.md"
    echo "  Installed ~/CLAUDE.md"
else
    echo "  Warning: CLAUDE.md not found in repo"
fi

# Install NTM command palette
echo "  Installing NTM command palette..."
mkdir -p "$INSTALL_HOME/.config/ntm"
if [ -f "$_REPO_DIR_09/config/ntm/command_palette.md" ]; then
    cp "$_REPO_DIR_09/config/ntm/command_palette.md" "$INSTALL_HOME/.config/ntm/"
    echo "  Installed ~/.config/ntm/command_palette.md"
else
    echo "  Warning: NTM command palette not found in repo"
fi

# Start beads daemon for fast bd commands (232x speedup vs auto-start timeout)
if command -v bd &>/dev/null; then
    echo "  Starting beads daemon..."
    bd daemon --start 2>/dev/null && echo "  Beads daemon started" || echo "  Warning: Could not start beads daemon"
fi

echo "Enforcement hooks installed."
