#!/usr/bin/env bash
#
# Farmhand v2.2.1 - Agentic VM Setup Installer
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

FARMHAND_HOME="$HOME/.farmhand"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read version from VERSION file if available, otherwise use fallback
if [[ -f "$SCRIPT_DIR/VERSION" ]]; then
    FARMHAND_VERSION="$(cat "$SCRIPT_DIR/VERSION")"
else
    # Fallback for curl | bash installation
    FARMHAND_VERSION="2.2.1"
fi

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

# ASCII Art Banner - Classic Red Barn
echo ""
echo -e "${RED}"
cat << 'BARN'
                               ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
                           ▄▄██▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀██▄▄
                       ▄▄██▀▀      ┌──────────┐      ▀▀██▄▄
                   ▄▄██▀▀          │ ░░░░░░░░ │          ▀▀██▄▄
               ▄▄██▀▀              │ ░░░░░░░░ │              ▀▀██▄▄
           ▄▄██▀▀                  └──────────┘                  ▀▀██▄▄
       ▄▄██▀▀                                                        ▀▀██▄▄
   ████████████████████████████████████████████████████████████████████████████

      ███████╗ █████╗ ██████╗ ███╗   ███╗██╗  ██╗ █████╗ ███╗   ██╗██████╗
      ██╔════╝██╔══██╗██╔══██╗████╗ ████║██║  ██║██╔══██╗████╗  ██║██╔══██╗
      █████╗  ███████║██████╔╝██╔████╔██║███████║███████║██╔██╗ ██║██║  ██║
      ██╔══╝  ██╔══██║██╔══██╗██║╚██╔╝██║██╔══██║██╔══██║██║╚██╗██║██║  ██║
      ██║     ██║  ██║██║  ██║██║ ╚═╝ ██║██║  ██║██║  ██║██║ ╚████║██████╔╝
      ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝

   ╔═════════╗╔═════════╗          ▓▓▓▓▓▓▓▓▓▓▓▓          ╔═════════╗╔═════════╗
   ║ ╲     ╱ ║║ ╲     ╱ ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║ ╲     ╱ ║║ ╲     ╱ ║
   ║  ╲   ╱  ║║  ╲   ╱  ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║  ╲   ╱  ║║  ╲   ╱  ║
   ║   ╲ ╱   ║║   ╲ ╱   ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║   ╲ ╱   ║║   ╲ ╱   ║
   ║    ╳    ║║    ╳    ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║    ╳    ║║    ╳    ║
   ║   ╱ ╲   ║║   ╱ ╲   ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║   ╱ ╲   ║║   ╱ ╲   ║
   ║  ╱   ╲  ║║  ╱   ╲  ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║  ╱   ╲  ║║  ╱   ╲  ║
   ║ ╱     ╲ ║║ ╱     ╲ ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║ ╱     ╲ ║║ ╱     ╲ ║
   ╚═════════╝╚═════════╝                                ╚═════════╝╚═════════╝
   ████████████████████████████████████████████████████████████████████████████
BARN
echo -e "${NC}"
echo ""
echo -e "                            Multi-Agent AI Setup ${RED}·${NC} v${BLUE}$FARMHAND_VERSION${NC}"
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

# Set up comprehensive PATH before any installations
# This ensures all tools are findable throughout the install process
mkdir -p ~/.local/bin ~/.bun/bin ~/.cargo/bin
export BUN_INSTALL="$HOME/.bun"
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$HOME/.cargo/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH"

# Function to refresh PATH after each phase (picks up newly installed tools)
refresh_path() {
    export PATH="$HOME/.local/bin:$HOME/.bun/bin:$HOME/.cargo/bin:/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH"
    # Source Homebrew if available
    if [[ -f /home/linuxbrew/.linuxbrew/bin/brew ]]; then
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" 2>/dev/null || true
    fi
    # Source fnm if available (for Node.js)
    if command -v fnm &>/dev/null; then
        eval "$(fnm env --shell bash)" 2>/dev/null || true
    fi
}

# Initialize git submodules (knowledge_and_vibes requires this)
echo -e "${BLUE}[Pre-flight] Initializing git submodules...${NC}"
if [[ -d "$SCRIPT_DIR/.git" ]]; then
    git -C "$SCRIPT_DIR" submodule update --init --recursive 2>/dev/null || {
        echo -e "${YELLOW}    WARNING: Could not initialize submodules (may need manual init)${NC}"
    }
else
    echo "    Skipping submodule init (not a git repo)"
fi

# Run installation phases
# Disable set -e for sourced scripts to allow graceful failures
# Each phase can have errors without killing the entire install

run_phase() {
    local script="$1"
    local name="$2"
    echo -e "${BLUE}[Phase] $name${NC}"
    set +e
    source "$script"
    local rc=$?
    set -e
    # Refresh PATH to pick up newly installed tools
    refresh_path
    if [[ $rc -ne 0 ]]; then
        echo -e "${YELLOW}    WARNING: $name completed with errors (exit $rc)${NC}"
    fi
}

run_phase "$SCRIPT_DIR/scripts/install/01-system-deps.sh" "System dependencies"
run_phase "$SCRIPT_DIR/scripts/install/02-core-tools.sh" "Core tools"
run_phase "$SCRIPT_DIR/scripts/install/03-stack-tools.sh" "Stack tools"

# AI agents before cloud CLIs (Node.js needed for wrangler/vercel version checks)
run_phase "$SCRIPT_DIR/scripts/install/05-ai-agents.sh" "AI agents"

if [[ "$MINIMAL" != true ]]; then
    run_phase "$SCRIPT_DIR/scripts/install/04-cloud-clis.sh" "Cloud CLIs"
fi

if [[ "$SKIP_OLLAMA" != true ]]; then
    run_phase "$SCRIPT_DIR/scripts/install/06-ollama.sh" "Ollama"
fi

run_phase "$SCRIPT_DIR/scripts/install/07-mcp-agent-mail.sh" "MCP Agent Mail"
run_phase "$SCRIPT_DIR/scripts/install/08-shell-config.sh" "Shell config"
run_phase "$SCRIPT_DIR/scripts/install/09-hooks.sh" "Enforcement hooks"
run_phase "$SCRIPT_DIR/scripts/install/10-knowledge-vibes.sh" "Knowledge & Vibes"
run_phase "$SCRIPT_DIR/scripts/install/11-bd-claim.sh" "bd-claim atomic wrapper"

# Record installation
mkdir -p "$FARMHAND_HOME"
echo "$FARMHAND_VERSION" > "$FARMHAND_HOME/version"
date -Iseconds > "$FARMHAND_HOME/installed_at"

# Success Banner
echo ""
echo -e "${GREEN}"
cat << 'SUCCESS_BARN'
                               ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
                           ▄▄██▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀██▄▄
                       ▄▄██▀▀      ┌──────────┐      ▀▀██▄▄
                   ▄▄██▀▀          │ ░░░░░░░░ │          ▀▀██▄▄
               ▄▄██▀▀              │ ░░░░░░░░ │              ▀▀██▄▄
           ▄▄██▀▀                  └──────────┘                  ▀▀██▄▄
       ▄▄██▀▀                                                        ▀▀██▄▄
   ████████████████████████████████████████████████████████████████████████████

                  ██████╗ ███████╗ █████╗ ██████╗ ██╗   ██╗██╗
                  ██╔══██╗██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝██║
                  ██████╔╝█████╗  ███████║██║  ██║ ╚████╔╝ ██║
                  ██╔══██╗██╔══╝  ██╔══██║██║  ██║  ╚██╔╝  ╚═╝
                  ██║  ██║███████╗██║  ██║██████╔╝   ██║   ██╗
                  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝   ╚═╝

   ╔═════════╗╔═════════╗          ▓▓▓▓▓▓▓▓▓▓▓▓          ╔═════════╗╔═════════╗
   ║ ╲     ╱ ║║ ╲     ╱ ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║ ╲     ╱ ║║ ╲     ╱ ║
   ║  ╲   ╱  ║║  ╲   ╱  ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║  ╲   ╱  ║║  ╲   ╱  ║
   ║   ╲ ╱   ║║   ╲ ╱   ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║   ╲ ╱   ║║   ╲ ╱   ║
   ║    ╳    ║║    ╳    ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║    ╳    ║║    ╳    ║
   ║   ╱ ╲   ║║   ╱ ╲   ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║   ╱ ╲   ║║   ╱ ╲   ║
   ║  ╱   ╲  ║║  ╱   ╲  ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║  ╱   ╲  ║║  ╱   ╲  ║
   ║ ╱     ╲ ║║ ╱     ╲ ║          ▓▓▓▓▓▓▓▓▓▓▓▓          ║ ╱     ╲ ║║ ╱     ╲ ║
   ╚═════════╝╚═════════╝                                ╚═════════╝╚═════════╝
   ████████████████████████████████████████████████████████████████████████████
SUCCESS_BARN
echo -e "${NC}"
echo ""
echo -e "                         Farmhand ${GREEN}v$FARMHAND_VERSION${NC} installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Run 'exec zsh' to switch to the new shell (keyboard bindings included)"
echo "  2. Run 'claude' to authenticate Claude Code"
echo "  3. Run 'codex login --device-auth' to authenticate Codex"
echo "  4. Run 'gemini' to authenticate Gemini"
echo ""
echo "Quick commands:"
echo "  cla     - Claude Code (dangerous mode)"
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
