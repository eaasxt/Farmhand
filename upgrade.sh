#!/usr/bin/env bash
#
# JohnDeere Upgrade Script
# Upgrades an existing JohnDeere installation to the latest version
#

set -euo pipefail

VERSION="2.1.0"
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

echo "[1/5] Creating backup..."
cp ~/.claude/settings.json "$BACKUP_DIR/" 2>/dev/null || true
cp ~/.zshrc "$BACKUP_DIR/" 2>/dev/null || true
cp ~/CLAUDE.md "$BACKUP_DIR/" 2>/dev/null || true
cp -r ~/.claude/hooks "$BACKUP_DIR/" 2>/dev/null || true
cp -r ~/.claude/skills "$BACKUP_DIR/" 2>/dev/null || true
cp -r ~/.claude/commands "$BACKUP_DIR/" 2>/dev/null || true
echo "    Backup saved to $BACKUP_DIR"

echo "[2/5] Updating git submodules..."
cd "$SCRIPT_DIR"
git submodule update --init --recursive
git submodule update --remote
echo "    Submodules updated"

echo "[3/5] Updating hooks..."
cp "$SCRIPT_DIR/hooks/"*.py ~/.claude/hooks/
cp "$SCRIPT_DIR/hooks/"*.sh ~/.claude/hooks/
echo "    Hooks updated"

echo "[4/5] Updating configurations..."
cp "$SCRIPT_DIR/config/CLAUDE.md" ~/CLAUDE.md
cp "$SCRIPT_DIR/config/claude-settings.json" ~/.claude/settings.json
cp "$SCRIPT_DIR/config/ntm/command_palette.md" ~/.config/ntm/ 2>/dev/null || mkdir -p ~/.config/ntm && cp "$SCRIPT_DIR/config/ntm/command_palette.md" ~/.config/ntm/
echo "    Configurations updated"

echo "[5/5] Installing Knowledge & Vibes..."
source "$SCRIPT_DIR/scripts/install/10-knowledge-vibes.sh"

# Update version
echo "$VERSION" > "$JOHNDEERE_HOME/version"
date -Iseconds > "$JOHNDEERE_HOME/upgraded_at"

echo ""
echo -e "${GREEN}Upgrade complete! v$INSTALLED_VERSION → v$VERSION${NC}"
echo ""
echo "Changes in v$VERSION:"
echo "  - Added Knowledge & Vibes workflow layer (git submodule)"
echo "  - 18 skills for common development patterns"
echo "  - 7 slash commands (/prime, /calibrate, /execute, etc.)"
echo "  - 3 behavior rules (beads, multi-agent, safety)"
echo "  - 8 documentation templates"
echo "  - 19 formalized protocols with research backing"
echo ""
echo "New slash commands:"
echo "  /prime      - Start session, register agent, claim work"
echo "  /calibrate  - 5-phase alignment check between phases"
echo "  /next-bead  - Close current task, UBS scan, claim next"
echo "  /release    - End session, cleanup"
echo ""
echo "Backup location: $BACKUP_DIR"
