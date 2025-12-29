#!/usr/bin/env bash
# NOTE: Dont use set -e - sourced by install.sh
# set -euo pipefail

# Install MCP Agent Mail server

# IMPORTANT: Capture script directory BEFORE any cd commands
# BASH_SOURCE may be relative, so resolve it while we're still in the right directory
_SCRIPT_DIR_07="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_REPO_ROOT_07="$(dirname "$(dirname "$_SCRIPT_DIR_07")")"

INSTALL_DIR="$HOME/mcp_agent_mail"

echo "==> Installing MCP Agent Mail..."

# Clone the repository
if [[ ! -d "$INSTALL_DIR" ]]; then
    git clone https://github.com/Dicklesworthstone/mcp_agent_mail.git "$INSTALL_DIR"
else
    echo "    Repository already exists, pulling latest..."
    cd "$INSTALL_DIR"
    git pull origin main || true
fi

cd "$INSTALL_DIR"

# Ensure uv is available
export PATH="$HOME/.local/bin:$PATH"

# Install Python 3.14 via uv if needed
echo "==> Setting up Python environment..."
uv python install 3.14 2>/dev/null || true

# Create virtual environment and install dependencies
echo "==> Installing dependencies..."
uv sync

# Generate bearer token for authentication
echo "==> Generating authentication token..."
if [[ ! -f .env ]] || ! grep -q 'HTTP_BEARER_TOKEN=' .env; then
    TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
            openssl rand -hex 32)
    echo "HTTP_BEARER_TOKEN=$TOKEN" > .env
    echo "    Token generated and saved to .env"
else
    TOKEN=$(grep -E '^HTTP_BEARER_TOKEN=' .env | sed -E 's/^HTTP_BEARER_TOKEN=//')
    echo "    Using existing token from .env"
fi

# Store token for later use in Claude Code config
echo "$TOKEN" > /tmp/mcp_agent_mail_token

echo "==> MCP Agent Mail installed at $INSTALL_DIR"

# Set up systemd service (using _SCRIPT_DIR_07 and _REPO_ROOT_07 defined at top)

# Install run_server_with_token.sh script
echo "    Installing server startup script..."
mkdir -p "$INSTALL_DIR/scripts"
if [[ -f "$_REPO_ROOT_07/scripts/run_server_with_token.sh" ]]; then
    cp "$_REPO_ROOT_07/scripts/run_server_with_token.sh" "$INSTALL_DIR/scripts/"
    chmod +x "$INSTALL_DIR/scripts/run_server_with_token.sh"
    echo "    Installed run_server_with_token.sh"
else
    echo "    WARNING: run_server_with_token.sh not found in repo"
fi

echo "    Setting up systemd service..."
INSTALL_USER="${SUDO_USER:-$(whoami)}"
INSTALL_HOME="$HOME"

if [[ -f "$_REPO_ROOT_07/config/systemd/mcp-agent-mail.service" ]]; then
    # Substitute placeholders with actual user and home directory
    sed -e "s|__USER__|$INSTALL_USER|g" \
        -e "s|__HOME__|$INSTALL_HOME|g" \
        "$_REPO_ROOT_07/config/systemd/mcp-agent-mail.service" | \
        sudo tee /etc/systemd/system/mcp-agent-mail.service > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable mcp-agent-mail
    sudo systemctl start mcp-agent-mail 2>/dev/null || true
    echo "    MCP Agent Mail service enabled"
else
    echo "    WARNING: systemd service file not found"
fi

# Install health check script and systemd timer
echo "    Setting up health monitoring..."
if [[ -f "$_REPO_ROOT_07/bin/mcp-health-check" ]]; then
    cp "$_REPO_ROOT_07/bin/mcp-health-check" "$HOME/.local/bin/"
    chmod +x "$HOME/.local/bin/mcp-health-check"

    if [[ -f "$_REPO_ROOT_07/config/systemd/mcp-health-check.service" ]]; then
        sed -e "s|__USER__|$INSTALL_USER|g" \
            -e "s|__HOME__|$INSTALL_HOME|g" \
            "$_REPO_ROOT_07/config/systemd/mcp-health-check.service" | \
            sudo tee /etc/systemd/system/mcp-health-check.service > /dev/null
    fi

    if [[ -f "$_REPO_ROOT_07/config/systemd/mcp-health-check.timer" ]]; then
        sudo cp "$_REPO_ROOT_07/config/systemd/mcp-health-check.timer" /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable mcp-health-check.timer
        sudo systemctl start mcp-health-check.timer 2>/dev/null || true
        echo "    Health check timer enabled (runs every 5 min)"
    fi
fi

# Configure Claude Code to use MCP Agent Mail
echo "==> Configuring Claude Code MCP integration..."

# Use the claude mcp add command for proper configuration
# This writes to ~/.claude.json which Claude Code actually reads
# Note: ~/.claude/mcp.json is NOT read by Claude Code!
if command -v claude &> /dev/null; then
    echo "    Adding MCP server via 'claude mcp add'..."
    claude mcp add --transport http mcp-agent-mail "http://127.0.0.1:8765/mcp/" \
        --header "Authorization: Bearer $TOKEN" 2>/dev/null && {
        echo "    MCP Agent Mail configured successfully"
    } || {
        echo "    WARNING: 'claude mcp add' failed. Manual configuration may be needed."
        echo "    Run: claude mcp add --transport http mcp-agent-mail http://127.0.0.1:8765/mcp/ --header \"Authorization: Bearer \$TOKEN\""
    }
else
    echo "    WARNING: 'claude' command not found."
    echo "    After installing Claude Code, run:"
    echo "    claude mcp add --transport http mcp-agent-mail http://127.0.0.1:8765/mcp/ --header \"Authorization: Bearer $TOKEN\""
fi

# Also create a reference file (not used by Claude Code, just for documentation)
mkdir -p "$HOME/.claude"
cat > "$HOME/.claude/mcp-reference.json" << EOF
{
  "_comment": "This file is for REFERENCE ONLY. Claude Code reads ~/.claude.json, not this file.",
  "_instructions": "Run: claude mcp add --transport http mcp-agent-mail http://127.0.0.1:8765/mcp/ --header 'Authorization: Bearer TOKEN'",
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
chmod 600 "$HOME/.claude/mcp-reference.json"

# Configure Codex to use MCP Agent Mail
echo "==> Configuring Codex MCP integration..."
if command -v codex &> /dev/null; then
    echo "    Adding MCP server via 'codex mcp add'..."
    # Codex uses bearer token from environment variable
    codex mcp add mcp-agent-mail --url "http://127.0.0.1:8765/mcp/" \
        --bearer-token-env-var HTTP_BEARER_TOKEN 2>/dev/null && {
        echo "    Codex MCP Agent Mail configured successfully"
        echo "    Note: HTTP_BEARER_TOKEN env var set in ~/.zshrc"
    } || {
        echo "    WARNING: 'codex mcp add' failed. Manual configuration may be needed."
    }
else
    echo "    Codex not installed, skipping MCP config"
fi

# Configure Gemini to use MCP Agent Mail
echo "==> Configuring Gemini MCP integration..."
if command -v gemini &> /dev/null; then
    echo "    Adding MCP server to Gemini settings..."
    mkdir -p "$HOME/.gemini"
    # Gemini uses httpUrl (not url) for HTTP transport
    if [[ -f "$HOME/.gemini/settings.json" ]]; then
        # Merge with existing settings using jq if available
        if command -v jq &>/dev/null; then
            jq --arg token "$TOKEN" '.mcpServers["mcp-agent-mail"] = {
                "httpUrl": "http://127.0.0.1:8765/mcp/",
                "headers": {"Authorization": ("Bearer " + $token)},
                "trust": true
            }' "$HOME/.gemini/settings.json" > "$HOME/.gemini/settings.json.tmp" && \
            mv "$HOME/.gemini/settings.json.tmp" "$HOME/.gemini/settings.json"
            echo "    Gemini MCP Agent Mail configured successfully"
        else
            echo "    WARNING: jq not available, creating new Gemini settings"
            cat > "$HOME/.gemini/settings.json" << GEMINI_EOF
{
  "ui": {"hideWindowTitle": true},
  "mcpServers": {
    "mcp-agent-mail": {
      "httpUrl": "http://127.0.0.1:8765/mcp/",
      "headers": {"Authorization": "Bearer $TOKEN"},
      "trust": true
    }
  }
}
GEMINI_EOF
        fi
    else
        cat > "$HOME/.gemini/settings.json" << GEMINI_EOF
{
  "ui": {"hideWindowTitle": true},
  "mcpServers": {
    "mcp-agent-mail": {
      "httpUrl": "http://127.0.0.1:8765/mcp/",
      "headers": {"Authorization": "Bearer $TOKEN"},
      "trust": true
    }
  }
}
GEMINI_EOF
        echo "    Gemini MCP Agent Mail configured successfully"
    fi
else
    echo "    Gemini not installed, skipping MCP config"
fi
