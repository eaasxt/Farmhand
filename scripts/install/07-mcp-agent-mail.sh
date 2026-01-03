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

# IMPROVED: Generate token using centralized token manager
echo "==> Generating authentication token..."

# Check if token manager is available
TOKEN_MANAGER="$_REPO_ROOT_07/bin/token-manager.sh"
if [[ -f "$TOKEN_MANAGER" ]]; then
    echo "    Using Farmhand Token Manager..."
    chmod +x "$TOKEN_MANAGER"
    
    # Generate token using centralized manager
    if "$TOKEN_MANAGER" generate; then
        TOKEN=$("$TOKEN_MANAGER" get)
        echo "    Token generated and stored securely"
    else
        echo "    ERROR: Failed to generate token with token manager"
        exit 1
    fi
else
    echo "    WARNING: Token manager not found, using fallback method"
    # Fallback to original method (but don't store in /tmp)
    TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || \
            openssl rand -hex 32)
    echo "    Generated fallback token"
fi

# Store token in MCP Agent Mail .env file
if [[ ! -f .env ]] || ! grep -q 'HTTP_BEARER_TOKEN=' .env; then
    echo "HTTP_BEARER_TOKEN=$TOKEN" > .env
    echo "    Token saved to MCP Agent Mail .env"
else
    # Update existing token
    if grep -q '^HTTP_BEARER_TOKEN=' .env; then
        sed -i "s/^HTTP_BEARER_TOKEN=.*/HTTP_BEARER_TOKEN=$TOKEN/" .env
        echo "    Updated existing token in .env"
    else
        echo "HTTP_BEARER_TOKEN=$TOKEN" >> .env
        echo "    Added token to existing .env"
    fi
fi

# REMOVED: No longer store token in /tmp (security vulnerability)
# OLD: echo "$TOKEN" > /tmp/mcp_agent_mail_token

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

# IMPROVED: Validate MCP installation with token
echo "    Validating MCP installation..."
if [[ -f "$TOKEN_MANAGER" ]]; then
    # Wait a moment for service to start
    sleep 3
    
    if "$TOKEN_MANAGER" validate; then
        echo "    ✓ MCP Agent Mail installation validated successfully"
    else
        echo "    WARNING: MCP validation failed - may need manual configuration"
        echo "    Try: sudo systemctl restart mcp-agent-mail"
    fi
else
    echo "    WARNING: Cannot validate installation - token manager not available"
fi

