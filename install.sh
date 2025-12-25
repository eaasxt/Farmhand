#!/usr/bin/env bash
#
# Farmhand v2.0.0 - Agentic VM Setup Installer
#
# Transforms a fresh Ubuntu VPS into a fully-configured
# multi-agent AI coding environment.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/eaasxt/Farmhand/main/install.sh | bash
#
#   Or with options:
#   ./install.sh --force          # Reinstall everything
#   ./install.sh --dry-run        # Show what would be done
#   ./install.sh --minimal        # Skip cloud CLIs
#   ./install.sh --skip-ollama    # Skip Ollama installation
#

set -euo pipefail

FARMHAND_VERSION="2.2.1"
FARMHAND_HOME="$HOME/.farmhand"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
FORCE=false
DRY_RUN=false
MINIMAL=false
SKIP_OLLAMA=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force) FORCE=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --minimal) MINIMAL=true; shift ;;
        --skip-ollama) SKIP_OLLAMA=true; shift ;;
        --help|-h)
            echo "Farmhand v$FARMHAND_VERSION - Agentic VM Setup"
            echo ""
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --force        Reinstall all components"
            echo "  --dry-run      Show what would be done"
            echo "  --minimal      Skip cloud CLIs (vault, wrangler, etc.)"
            echo "  --skip-ollama  Skip Ollama installation"
            echo "  --help         Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ASCII Art Banner
echo -e "${YELLOW}"
cat << 'SUNRISE'
                                    .  *  .
                             *  .    \  |  /    .  *
                         *      ' -- -☀- -- '      *
                             .     /  |  \     .
                         *       .'   |   '.       *
SUNRISE
echo -e "${RED}"
cat << 'BARNS'
            __             _.-'  ____|____  '-._             __
           /  \        _.-'     |        |     '-._        /  \
          |    |   _.-'    _    |   __   |    _    '-._   |    |
          |    |.-'       |_|   |  |__|  |   |_|       '-.|    |
BARNS
echo -e "${GREEN}"
cat << 'FIELD'
       ___|____|__________|_|___|________|___|_|__________|____|___
      |                                                            |
      |   \|/  \|/  \|/  \|/  \|/  \|/  \|/  \|/  \|/  \|/  \|/   |
      |    |    |    |    |    |    |    |    |    |    |    |    |
      |============================================================|
FIELD
echo -e "${BLUE}"
cat << 'FARMHAND_TEXT'
       ______                         _   _                  _
      |  ____|                       | | | |                | |
      | |__    __ _  _ __  _ __ ___  | |_| | __ _  _ __   __| |
      |  __|  / _` || '__|| '_ ` _ \ |  _  |/ _` || '_ \ / _` |
      | |    | (_| || |   | | | | | || | | || (_| || | | || (_| |
      |_|     \__,_||_|   |_| |_| |_||_| |_| \__,_||_| |_| \__,_|
FARMHAND_TEXT
echo -e "${NC}"
echo -e "                   ${YELLOW}🚜${NC}  Agentic AI Coding VM Setup  ${GREEN}🌾${NC}"
echo -e "                             Version ${BLUE}$FARMHAND_VERSION${NC}"
echo ""

# Check for existing installation
if [[ -f "$FARMHAND_HOME/version" ]]; then
    INSTALLED_VERSION=$(cat "$FARMHAND_HOME/version")
    echo -e "${YELLOW}Existing installation detected: v$INSTALLED_VERSION${NC}"
    if [[ "$FORCE" != true ]]; then
        echo "Run with --force to reinstall, or use upgrade.sh to upgrade."
        echo ""
    fi
fi

# Pre-flight checks
echo -e "${BLUE}[Pre-flight] Checking system requirements...${NC}"

# Check OS
if [[ ! -f /etc/os-release ]]; then
    echo -e "${RED}ERROR: Cannot detect OS. Ubuntu 22.04+ required.${NC}"
    exit 1
fi
source /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
    echo -e "${RED}ERROR: Ubuntu required, found $ID${NC}"
    exit 1
fi
echo "    OS: $PRETTY_NAME"

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "x86_64" && "$ARCH" != "aarch64" ]]; then
    echo -e "${RED}ERROR: Unsupported architecture: $ARCH${NC}"
    exit 1
fi
echo "    Architecture: $ARCH"

# Check disk space (need at least 10GB free)
FREE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
if [[ "$FREE_SPACE" -lt 10 ]]; then
    echo -e "${YELLOW}WARNING: Less than 10GB free disk space${NC}"
fi
echo "    Free disk space: ${FREE_SPACE}GB"

# Check memory (recommend at least 8GB)
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
echo "    Total memory: ${TOTAL_MEM}GB"

if [[ "$DRY_RUN" == true ]]; then
    echo ""
    echo -e "${YELLOW}DRY RUN - Would execute the following phases:${NC}"
    echo "  [1/10] System dependencies (apt, homebrew, bun, uv)"
    echo "  [2/10] Core tools (bd, bv, qmd, claude)"
    echo "  [3/10] Stack tools (ubs, ntm, cm, caam, slb, cass)"
    [[ "$MINIMAL" != true ]] && echo "  [4/10] Cloud CLIs (vault, wrangler, supabase, vercel)"
    echo "  [5/10] AI agents (codex, gemini, node)"
    [[ "$SKIP_OLLAMA" != true ]] && echo "  [6/10] Ollama + models"
    echo "  [7/10] MCP Agent Mail"
    echo "  [8/10] Shell configuration (zsh, oh-my-zsh, p10k)"
    echo "  [9/10] Enforcement hooks"
    echo "  [10/10] Knowledge & Vibes workflow (18 skills, 7 commands)"
    exit 0
fi

echo ""

# Ensure ~/.local/bin exists and is in PATH
mkdir -p ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"

# Run installation phases
source "$SCRIPT_DIR/scripts/install/01-system-deps.sh"
source "$SCRIPT_DIR/scripts/install/02-core-tools.sh"
source "$SCRIPT_DIR/scripts/install/03-stack-tools.sh"

if [[ "$MINIMAL" != true ]]; then
    source "$SCRIPT_DIR/scripts/install/04-cloud-clis.sh"
fi

source "$SCRIPT_DIR/scripts/install/05-ai-agents.sh"

if [[ "$SKIP_OLLAMA" != true ]]; then
    source "$SCRIPT_DIR/scripts/install/06-ollama.sh"
fi

source "$SCRIPT_DIR/scripts/install/07-mcp-agent-mail.sh"
source "$SCRIPT_DIR/scripts/install/08-shell-config.sh"
source "$SCRIPT_DIR/scripts/install/09-hooks.sh"
source "$SCRIPT_DIR/scripts/install/10-knowledge-vibes.sh"

# Record installation
mkdir -p "$FARMHAND_HOME"
echo "$FARMHAND_VERSION" > "$FARMHAND_HOME/version"
date -Iseconds > "$FARMHAND_HOME/installed_at"

# Success Banner
echo ""
echo -e "${GREEN}"
cat << 'SUCCESS_ART'
      _.-~~~~~-._       _.-~~~~~-._       _.-~~~~~-._       _.-~~~~~-._
     /           \     /           \     /           \     /           \
    |    ) _ (    |   |    ) _ (    |   |    ) _ (    |   |    ) _ (    |
    |   ( (_) )   |   |   ( (_) )   |   |   ( (_) )   |   |   ( (_) )   |
    |    ) _ (    |   |    ) _ (    |   |    ) _ (    |   |    ) _ (    |
     \    \_/    /     \    \_/    /     \    \_/    /     \    \_/    /
      '-._____.-'       '-._____.-'       '-._____.-'       '-._____.-'
         |||               |||               |||               |||
    ~~~~~|||~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SUCCESS_ART
echo -e "${NC}"
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}║   🎉  HARVEST COMPLETE!  Farmhand v$FARMHAND_VERSION installed!       ║${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}║   Your VM is now a fully-equipped AI coding powerhouse.                 ║${NC}"
echo -e "${GREEN}║                                                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Run 'exec zsh' to switch to the new shell"
echo "  2. Run 'claude' to authenticate Claude Code"
echo "  3. Run 'codex login --device-auth' to authenticate Codex"
echo "  4. Run 'gemini' to authenticate Gemini"
echo ""
echo "Quick commands:"
echo "  cc      - Claude Code (dangerous mode)"
echo "  cod     - Codex CLI (full auto)"
echo "  gmi     - Gemini CLI (yolo mode)"
echo "  bd      - Beads issue tracking"
echo "  ntm     - Named Tmux Manager"
echo ""
echo "Slash commands (in Claude):"
echo "  /prime  - Start session, register agent, claim work"
echo "  /calibrate - Check alignment between phases"
echo "  /next-bead - Close current, UBS scan, claim next"
echo "  /release - End session, cleanup"
echo ""
echo "Verify installation:"
echo "  $SCRIPT_DIR/scripts/verify.sh"
