#!/usr/bin/env bash
set -euo pipefail

# Set up systemd services for MCP Agent Mail and Ollama

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Setting up systemd services..."

# MCP Agent Mail service
echo "    Installing mcp-agent-mail.service..."
sudo cp "$REPO_DIR/config/systemd/mcp-agent-mail.service" /etc/systemd/system/

# Ollama service (usually installed by ollama install script, but ensure it exists)
if [[ ! -f /etc/systemd/system/ollama.service ]]; then
    echo "    Installing ollama.service..."
    sudo cp "$REPO_DIR/config/systemd/ollama.service" /etc/systemd/system/
fi

# Reload systemd
echo "    Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "    Enabling services..."
sudo systemctl enable mcp-agent-mail ollama

# Start services
echo "    Starting services..."
sudo systemctl start ollama
sleep 2
sudo systemctl start mcp-agent-mail

# Check status
echo ""
echo "==> Service status:"
sudo systemctl status mcp-agent-mail --no-pager -l | head -10
echo ""
sudo systemctl status ollama --no-pager -l | head -10

echo ""
echo "==> Services configured and running"
