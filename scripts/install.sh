#!/usr/bin/env bash
set -euo pipefail

# JohnDeere VM Bootstrap - Master Installer
# Run this script to set up a complete Claude Code development environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "  JohnDeere VM Bootstrap Installer"
echo "=========================================="
echo ""
echo "This will install:"
echo "  - System dependencies (apt packages)"
echo "  - Homebrew (Linuxbrew)"
echo "  - Bun (JavaScript runtime)"
echo "  - bd (beads CLI)"
echo "  - bv (beads-viewer)"
echo "  - qmd (markdown search)"
echo "  - Ollama + embedding models"
echo "  - MCP Agent Mail server"
echo "  - Claude Code CLI"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "[1/6] Installing system dependencies..."
"$SCRIPT_DIR/01-system-deps.sh"

echo ""
echo "[2/6] Installing tools (bd, bv, qmd)..."
"$SCRIPT_DIR/02-tools.sh"

echo ""
echo "[3/6] Installing Ollama..."
"$SCRIPT_DIR/03-ollama.sh"

echo ""
echo "[4/6] Installing MCP Agent Mail..."
"$SCRIPT_DIR/04-mcp-agent-mail.sh"

echo ""
echo "[5/6] Configuring Claude Code..."
"$SCRIPT_DIR/05-claude-config.sh"

echo ""
echo "[6/6] Setting up systemd services..."
"$SCRIPT_DIR/06-services.sh"

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart your shell: exec bash -l"
echo "  2. Start Claude Code: claude"
echo "  3. Verify: ~/JohnDeere/scripts/verify.sh"
echo ""
echo "Services running:"
echo "  - MCP Agent Mail: http://127.0.0.1:8765"
echo "  - Ollama: http://127.0.0.1:11434"
echo ""
