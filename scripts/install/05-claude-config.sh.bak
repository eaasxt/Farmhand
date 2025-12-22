#!/usr/bin/env bash
set -euo pipefail

# Configure Claude Code settings

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$HOME/.config/claude-code"

echo "==> Configuring Claude Code..."

# Create config directory
mkdir -p "$CONFIG_DIR"

# Get the MCP Agent Mail token
TOKEN=""
if [[ -f /tmp/mcp_agent_mail_token ]]; then
    TOKEN=$(cat /tmp/mcp_agent_mail_token)
elif [[ -f "$HOME/mcp_agent_mail/.env" ]]; then
    TOKEN=$(grep -E '^HTTP_BEARER_TOKEN=' "$HOME/mcp_agent_mail/.env" | sed -E 's/^HTTP_BEARER_TOKEN=//')
fi

if [[ -z "$TOKEN" ]]; then
    echo "    WARNING: No MCP Agent Mail token found."
    echo "    You'll need to configure the MCP server manually in Claude Code."
    TOKEN="REPLACE_WITH_YOUR_TOKEN"
fi

# Create settings.json with MCP server configuration
cat > "$CONFIG_DIR/settings.json" << EOF
{
  "enabledPlugins": {
    "commit-commands@claude-plugins-official": true,
    "feature-dev@claude-plugins-official": true,
    "frontend-design@claude-plugins-official": true,
    "github@claude-plugins-official": true,
    "ralph-wiggum@claude-plugins-official": true,
    "vercel@claude-plugins-official": true
  },
  "mcpServers": {
    "mcp-agent-mail": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp/",
      "headers": {
        "Authorization": "Bearer $TOKEN"
      }
    }
  }
}
EOF

echo "    Created $CONFIG_DIR/settings.json"

# Copy CLAUDE.md to home directory
if [[ -f "$REPO_DIR/config/CLAUDE.md" ]]; then
    cp "$REPO_DIR/config/CLAUDE.md" ~/CLAUDE.md
    echo "    Copied CLAUDE.md to ~/"
fi

# Update bashrc with environment variables
if ! grep -q 'BEADS_DB' ~/.bashrc; then
    cat >> ~/.bashrc << 'EOF'

# JohnDeere Development Environment
export PATH="/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/home/linuxbrew/.linuxbrew/bin:$PATH"
export BUN_INSTALL="$HOME/.bun"
export BEADS_DB=/home/ubuntu/.beads/beads.db

# MCP Agent Mail alias
alias am='cd "$HOME/mcp_agent_mail" && scripts/run_server_with_token.sh'
EOF
    echo "    Updated ~/.bashrc with environment variables"
else
    echo "    ~/.bashrc already configured"
fi

echo "==> Claude Code configured"
