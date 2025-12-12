#!/usr/bin/env bash
set -euo pipefail

# Update JohnDeere tools to latest versions

echo "=== Updating JohnDeere Tools ==="

# Update this repo first
echo ""
echo "==> Pulling latest JohnDeere repo..."
cd ~/JohnDeere
git pull origin main 2>/dev/null || git pull https://github.com/eaasxt/JohnDeere.git main

# Update bd
echo ""
echo "==> Checking bd for updates..."
CURRENT_BD=$(~/.local/bin/bd --version 2>/dev/null | grep -oP 'v?\d+\.\d+\.\d+' | head -1 || echo "unknown")
echo "    Current: $CURRENT_BD"
echo "    Check https://github.com/steveyegge/beads/releases for latest"

# Update bv
echo ""
echo "==> Updating bv via Homebrew..."
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" 2>/dev/null || true
brew upgrade beads-viewer 2>/dev/null || echo "    bv already up to date (or not installed via brew)"

# Update qmd
echo ""
echo "==> Updating qmd..."
bun install -g https://github.com/tobi/qmd 2>/dev/null || echo "    qmd update skipped"

# Update MCP Agent Mail
echo ""
echo "==> Updating MCP Agent Mail..."
cd ~/mcp_agent_mail
git pull origin main 2>/dev/null || true
uv sync 2>/dev/null || true
sudo systemctl restart mcp-agent-mail

# Re-copy hooks (in case they were updated)
echo ""
echo "==> Updating hooks..."
mkdir -p ~/.claude/hooks
cp ~/JohnDeere/hooks/*.py ~/.claude/hooks/
cp ~/JohnDeere/bin/bd-cleanup ~/.local/bin/
chmod +x ~/.claude/hooks/*.py ~/.local/bin/bd-cleanup

# Regenerate settings.json with hook config
echo ""
echo "==> Updating hook configuration..."
cat > ~/.claude/settings.json << EOF
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "TodoWrite", "hooks": [{"type": "command", "command": "$HOME/.claude/hooks/todowrite-interceptor.py", "timeout": 5}]},
      {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "$HOME/.claude/hooks/reservation-checker.py", "timeout": 5}]}
    ],
    "PostToolUse": [
      {"matcher": "mcp__mcp-agent-mail__.*|register_agent|file_reservation_paths|release_file_reservations|macro_start_session", "hooks": [{"type": "command", "command": "$HOME/.claude/hooks/mcp-state-tracker.py", "timeout": 5}]}
    ],
    "SessionStart": [
      {"matcher": "startup|resume|clear", "hooks": [{"type": "command", "command": "$HOME/.claude/hooks/session-init.py", "timeout": 10}]}
    ]
  }
}
EOF

# Update CLAUDE.md
echo ""
echo "==> Updating CLAUDE.md..."
cp ~/JohnDeere/config/CLAUDE.md ~/CLAUDE.md
# Re-add bearer token
TOKEN=$(grep 'HTTP_BEARER_TOKEN=' ~/mcp_agent_mail/.env 2>/dev/null | cut -d'=' -f2)
if [ -n "$TOKEN" ]; then
    echo "" >> ~/CLAUDE.md
    echo "## Bearer Token (remote access)" >> ~/CLAUDE.md
    echo "" >> ~/CLAUDE.md
    echo '```' >> ~/CLAUDE.md
    echo "$TOKEN" >> ~/CLAUDE.md
    echo '```' >> ~/CLAUDE.md
    echo "" >> ~/CLAUDE.md
    echo "Localhost bypasses auth." >> ~/CLAUDE.md
fi

echo ""
echo "=== Update Complete ==="
echo "Run './scripts/verify.sh' to verify"
