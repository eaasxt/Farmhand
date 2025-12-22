#!/usr/bin/env bash
set -euo pipefail

# Install MCP Agent Mail server

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

# Set up systemd service
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR/../.."

echo "    Setting up systemd service..."
if [[ -f "$REPO_ROOT/config/systemd/mcp-agent-mail.service" ]]; then
    sudo cp "$REPO_ROOT/config/systemd/mcp-agent-mail.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mcp-agent-mail
    sudo systemctl start mcp-agent-mail 2>/dev/null || true
    echo "    MCP Agent Mail service enabled"
else
    echo "    WARNING: systemd service file not found"
fi
