#!/usr/bin/env bash
# MCP Agent Mail Server Startup Script
# Called by systemd service mcp-agent-mail.service
#
# This script:
# 1. Sources the .env file for HTTP_BEARER_TOKEN
# 2. Starts the MCP Agent Mail HTTP server

set -euo pipefail

# Get the script directory (should be mcp_agent_mail/scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Source .env file if it exists
if [[ -f ".env" ]]; then
    # Export variables from .env file
    set -a
    source .env
    set +a
fi

# Verify HTTP_BEARER_TOKEN is set
if [[ -z "${HTTP_BEARER_TOKEN:-}" ]]; then
    echo "ERROR: HTTP_BEARER_TOKEN is not set" >&2
    echo "Please create .env file with HTTP_BEARER_TOKEN=<your-token>" >&2
    exit 1
fi

# Start the server
exec uv run python -m mcp_agent_mail.cli serve-http
