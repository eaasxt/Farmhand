#!/usr/bin/env bash
#
# JohnDeere Upgrade Script
# Upgrades an existing JohnDeere installation to the latest version
#

set -euo pipefail

VERSION="2.0.0"
JOHNDEERE_HOME="$HOME/.johndeere"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}JohnDeere Upgrade Script${NC}"
echo ""

# Check for existing installation
if [[ ! -f "$JOHNDEERE_HOME/version" ]]; then
    echo -e "${YELLOW}No existing installation found.${NC}"
    echo "Run ./install.sh for a fresh installation."
    exit 1
fi

INSTALLED_VERSION=$(cat "$JOHNDEERE_HOME/version")
echo "Installed version: v$INSTALLED_VERSION"
echo "Available version: v$VERSION"

# Compare versions
if [[ "$INSTALLED_VERSION" == "$VERSION" ]]; then
    echo -e "${GREEN}Already at latest version!${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Upgrading from v$INSTALLED_VERSION to v$VERSION...${NC}"
echo ""

# Create backup
BACKUP_DIR="$JOHNDEERE_HOME/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "[1/4] Creating backup..."
cp ~/.claude/settings.json "$BACKUP_DIR/" 2>/dev/null || true
cp ~/.zshrc "$BACKUP_DIR/" 2>/dev/null || true
cp ~/CLAUDE.md "$BACKUP_DIR/" 2>/dev/null || true
cp -r ~/.claude/hooks "$BACKUP_DIR/" 2>/dev/null || true
echo "    Backup saved to $BACKUP_DIR"

echo "[2/4] Updating hooks..."
cp "$SCRIPT_DIR/hooks/"*.py ~/.claude/hooks/
cp "$SCRIPT_DIR/hooks/"*.sh ~/.claude/hooks/
echo "    Hooks updated"

echo "[3/4] Updating configurations..."
cp "$SCRIPT_DIR/config/CLAUDE.md" ~/CLAUDE.md
cp "$SCRIPT_DIR/config/claude-settings.json" ~/.claude/settings.json
cp "$SCRIPT_DIR/config/ntm/command_palette.md" ~/.config/ntm/ 2>/dev/null || mkdir -p ~/.config/ntm && cp "$SCRIPT_DIR/config/ntm/command_palette.md" ~/.config/ntm/
echo "    Configurations updated"

echo "[4/4] Updating utilities..."
cp "$SCRIPT_DIR/bin/bd-cleanup" ~/.local/bin/
cp "$SCRIPT_DIR/bin/cass" ~/.local/bin/
chmod +x ~/.local/bin/bd-cleanup ~/.local/bin/cass
echo "    Utilities updated"

# Update version
echo "$VERSION" > "$JOHNDEERE_HOME/version"
date -Iseconds > "$JOHNDEERE_HOME/upgraded_at"

echo ""
echo -e "${GREEN}Upgrade complete! v$INSTALLED_VERSION → v$VERSION${NC}"
echo ""
echo "Changes in v$VERSION:"
echo "  - Updated hooks with improved file reservation logic"
echo "  - Enhanced CLAUDE.md with comprehensive workflow docs"
echo "  - Added UBS integration hook (on-file-write.sh)"
echo "  - Added cass Docker wrapper for Ubuntu 22.04 compatibility"
echo "  - Added NTM command palette with 40+ prompts"
echo "  - Full zsh configuration with powerlevel10k"
echo ""
echo "Backup location: $BACKUP_DIR"
