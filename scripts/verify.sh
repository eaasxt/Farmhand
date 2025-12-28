#!/usr/bin/env bash
# Note: Not using set -e because arithmetic operations can return non-zero
set -uo pipefail

# Get version from VERSION file or default
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/../VERSION"
if [[ -f "$VERSION_FILE" ]]; then
    FARMHAND_VERSION=$(cat "$VERSION_FILE")
else
    FARMHAND_VERSION="unknown"
fi

echo "=========================================="
echo "  Farmhand v${FARMHAND_VERSION} Installation Verify"
echo "=========================================="
echo ""

PASS=0
FAIL=0
WARN=0
REFRESH=0

# Known installation paths for tools that may not be in PATH during fresh install
declare -A KNOWN_PATHS=(
    # Core tools
    ["bd"]="$HOME/.local/bin/bd"
    ["bv"]="$HOME/.local/bin/bv"
    ["qmd"]="$HOME/.local/bin/qmd"
    ["claude"]="$HOME/.local/bin/claude /home/linuxbrew/.linuxbrew/bin/claude"
    # Stack tools
    ["ubs"]="$HOME/.local/bin/ubs"
    ["cm"]="$HOME/.local/bin/cm"
    ["cass"]="$HOME/.local/bin/cass"
    ["ntm"]="$HOME/.local/share/fnm/node-versions/*/installation/bin/ntm"
    ["caam"]="$HOME/.local/share/fnm/node-versions/*/installation/bin/caam"
    # Runtime
    ["bun"]="$HOME/.bun/bin/bun"
    ["uv"]="$HOME/.local/bin/uv"
    ["node"]="$HOME/.local/bin/node"
    ["npm"]="$HOME/.local/bin/npm"
    # Cloud CLIs
    ["codex"]="$HOME/.bun/bin/codex"
    ["wrangler"]="$HOME/.bun/bin/wrangler"
    ["vercel"]="$HOME/.bun/bin/vercel"
    ["gemini"]="$HOME/.bun/bin/gemini"
    ["supabase"]="/home/linuxbrew/.linuxbrew/bin/supabase"
)

# Check if binary exists at known path (supports globs)
find_at_known_path() {
    local tool="$1"
    local pattern="${KNOWN_PATHS[$tool]:-}"
    [[ -z "$pattern" ]] && return 1
    # Use compgen to expand globs safely
    for f in $pattern; do
        [[ -x "$f" ]] && return 0
    done
    return 1
}

check() {
    local name="$1"
    local cmd="$2"
    local tool="${3:-}"  # Optional: tool name for path lookup
    printf "%-35s" "$name"
    if eval "$cmd" &>/dev/null; then
        echo "[OK]"
        PASS=$((PASS + 1))
    elif [[ -n "$tool" ]] && find_at_known_path "$tool"; then
        echo "[OK] (shell refresh needed)"
        PASS=$((PASS + 1))
        REFRESH=$((REFRESH + 1))
    else
        echo "[FAIL]"
        FAIL=$((FAIL + 1))
    fi
}

check_optional() {
    local name="$1"
    local cmd="$2"
    local tool="${3:-}"  # Optional: tool name for path lookup
    printf "%-35s" "$name"
    if eval "$cmd" &>/dev/null; then
        echo "[OK]"
        PASS=$((PASS + 1))
    elif [[ -n "$tool" ]] && find_at_known_path "$tool"; then
        echo "[OK] (shell refresh needed)"
        PASS=$((PASS + 1))
        REFRESH=$((REFRESH + 1))
    else
        echo "[SKIP]"
        WARN=$((WARN + 1))
    fi
}

check_service() {
    local name="$1"
    printf "%-35s" "$name service"
    if systemctl is-active --quiet "$name" 2>/dev/null; then
        echo "[RUNNING]"
        PASS=$((PASS + 1))
    else
        echo "[NOT RUNNING]"
        FAIL=$((FAIL + 1))
    fi
}

echo "==> Core Tools..."
check "bd (beads)" "command -v bd" "bd"
check "bv (beads-viewer)" "command -v bv" "bv"
check "qmd" "command -v qmd" "qmd"

echo ""
echo "==> Dicklesworthstone Stack..."
check "ast-grep (UBS JS/TS)" "command -v ast-grep || command -v sg"
check "ubs (bug scanner)" "command -v ubs" "ubs"
check "ntm (tmux manager)" "command -v ntm" "ntm"
check "cm (cass memory)" "command -v cm" "cm"
check "caam (account manager)" "command -v caam" "caam"
check_optional "slb (launch button)" "command -v slb"
check "cass (session search)" "command -v cass" "cass"

echo ""
echo "==> Cloud CLIs..."
check_optional "vault" "command -v vault"
check_optional "wrangler" "command -v wrangler" "wrangler"
check_optional "supabase" "command -v supabase" "supabase"
check_optional "vercel" "command -v vercel" "vercel"

echo ""
echo "==> AI Coding Agents..."
check "claude" "command -v claude" "claude"
check "codex" "command -v codex" "codex"
check_optional "gemini" "command -v gemini" "gemini"

echo ""
echo "==> Runtime Dependencies..."
check "bun" "command -v bun" "bun"
check "uv" "command -v uv" "uv"
check "node" "command -v node" "node"
check "ollama" "command -v ollama"
check "zsh" "command -v zsh"

echo ""
echo "==> Services..."
check_service "mcp-agent-mail"
check_service "ollama"

echo ""
echo "==> Configuration Files..."
check "CLAUDE.md" "test -f ~/CLAUDE.md"
check "Beads DB" "test -f ~/.beads/beads.db"
check "Claude settings" "test -f ~/.claude/settings.json"
check "MCP Agent Mail" "test -d ~/mcp_agent_mail"
check "NTM command palette" "test -f ~/.config/ntm/command_palette.md"
check_optional "zshrc" "test -f ~/.zshrc"
check_optional "p10k config" "test -f ~/.p10k.zsh"

echo ""
echo "==> Enforcement Hooks..."
check "todowrite-interceptor" "test -x ~/.claude/hooks/todowrite-interceptor.py"
check "reservation-checker" "test -x ~/.claude/hooks/reservation-checker.py"
check "mcp-state-tracker" "test -x ~/.claude/hooks/mcp-state-tracker.py"
check "session-init" "test -x ~/.claude/hooks/session-init.py"
check "bd-cleanup" "test -x ~/.local/bin/bd-cleanup"
check "bd-claim" "test -x ~/.local/bin/bd-claim"
check_optional "identity-check" "test -x ~/.local/bin/identity-check"

echo ""
echo "==> Knowledge & Vibes Workflow..."
# Check skills directory has content
printf "%-35s" "Skills (18 expected)"
SKILLS_COUNT=$(ls ~/.claude/skills/ 2>/dev/null | wc -l)
if [[ "$SKILLS_COUNT" -ge 15 ]]; then
    echo "[OK] ($SKILLS_COUNT installed)"
    PASS=$((PASS + 1))
else
    echo "[INCOMPLETE] ($SKILLS_COUNT installed)"
    FAIL=$((FAIL + 1))
fi

# Check commands
printf "%-35s" "Commands (7 expected)"
CMDS_COUNT=$(ls ~/.claude/commands/ 2>/dev/null | wc -l)
if [[ "$CMDS_COUNT" -ge 5 ]]; then
    echo "[OK] ($CMDS_COUNT installed)"
    PASS=$((PASS + 1))
else
    echo "[INCOMPLETE] ($CMDS_COUNT installed)"
    FAIL=$((FAIL + 1))
fi

# Check rules
printf "%-35s" "Rules (3 expected)"
RULES_COUNT=$(ls ~/.claude/rules/ 2>/dev/null | wc -l)
if [[ "$RULES_COUNT" -ge 3 ]]; then
    echo "[OK] ($RULES_COUNT installed)"
    PASS=$((PASS + 1))
else
    echo "[INCOMPLETE] ($RULES_COUNT installed)"
    FAIL=$((FAIL + 1))
fi

# Check templates
printf "%-35s" "Templates (8 expected)"
TEMPLATES_COUNT=$(ls ~/templates/ 2>/dev/null | wc -l)
if [[ "$TEMPLATES_COUNT" -ge 5 ]]; then
    echo "[OK] ($TEMPLATES_COUNT installed)"
    PASS=$((PASS + 1))
else
    echo "[INCOMPLETE] ($TEMPLATES_COUNT installed)"
    FAIL=$((FAIL + 1))
fi

# Check key commands exist
check "/prime command" "test -f ~/.claude/commands/prime.md"
check "/calibrate command" "test -f ~/.claude/commands/calibrate.md"
check "/next-bead command" "test -f ~/.claude/commands/next-bead.md"

echo ""
echo "==> API Connectivity..."
check "Ollama API" "curl -s http://localhost:11434/api/version"

echo ""
echo "==> Ollama Models..."
printf "%-35s" "embeddinggemma"
if ollama list 2>/dev/null | grep -q "embeddinggemma"; then
    echo "[INSTALLED]"
    PASS=$((PASS + 1))
else
    echo "[MISSING]"
    FAIL=$((FAIL + 1))
fi

printf "%-35s" "qwen3-reranker"
if ollama list 2>/dev/null | grep -q "qwen3-reranker"; then
    echo "[INSTALLED]"
    PASS=$((PASS + 1))
else
    echo "[MISSING]"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "==> Version Info..."
printf "%-35s" "Farmhand version"
if [[ -f ~/.farmhand/version ]]; then
    echo "v$(cat ~/.farmhand/version)"
else
    echo "[NOT TRACKED]"
fi

printf "%-35s" "Claude Code version"
if command -v claude &>/dev/null; then
    claude --version 2>&1 | head -1 || echo "[UNKNOWN]"
else
    echo "[NOT INSTALLED]"
fi

printf "%-35s" "bd (beads) version"
if command -v bd &>/dev/null; then
    bd --version 2>&1 | head -1 || echo "[UNKNOWN]"
else
    echo "[NOT INSTALLED]"
fi

printf "%-35s" "ubs version"
if command -v ubs &>/dev/null; then
    ubs --version 2>&1 | head -1 || echo "[UNKNOWN]"
else
    echo "[NOT INSTALLED]"
fi

echo ""
echo "==> Path Verification (ACFS checks)..."
# Claude should be accessible from ~/.local/bin
printf "%-35s" "Claude in ~/.local/bin"
if [[ -x ~/.local/bin/claude ]] || [[ -L ~/.local/bin/claude ]]; then
    echo "[OK]"
    PASS=$((PASS + 1))
else
    echo "[WARN] (use Homebrew path)"
    WARN=$((WARN + 1))
fi

# Check for stale agent state
printf "%-35s" "Agent state freshness"
if [[ -f ~/.claude/agent-state.json ]]; then
    STATE_AGE=$(( $(date +%s) - $(stat -c %Y ~/.claude/agent-state.json 2>/dev/null || echo 0) ))
    if [[ $STATE_AGE -gt 14400 ]]; then  # 4 hours
        echo "[STALE] (>4h old, run bd-cleanup)"
        WARN=$((WARN + 1))
    else
        echo "[OK]"
        PASS=$((PASS + 1))
    fi
else
    echo "[NONE] (will create on first run)"
    PASS=$((PASS + 1))
fi

echo ""
echo "==> System Compatibility..."
# Check GLIBC version for CASS compatibility (requires 2.39+, Ubuntu 24.04+)
printf "%-35s" "GLIBC version (CASS needs 2.39+)"
GLIBC_VERSION=$(ldd --version 2>/dev/null | head -1 | grep -oP '\d+\.\d+$' || echo "0.0")
GLIBC_MAJOR=$(echo "$GLIBC_VERSION" | cut -d. -f1)
GLIBC_MINOR=$(echo "$GLIBC_VERSION" | cut -d. -f2)
# Compare: 2.39+ means major=2 and minor>=39, or major>2
if [[ "$GLIBC_MAJOR" -gt 2 ]] || { [[ "$GLIBC_MAJOR" -eq 2 ]] && [[ "$GLIBC_MINOR" -ge 39 ]]; }; then
    echo "[OK] ($GLIBC_VERSION)"
    PASS=$((PASS + 1))
else
    echo "[WARN] ($GLIBC_VERSION < 2.39)"
    echo "       CASS requires Ubuntu 24.04+ (GLIBC 2.39+)"
    echo "       Session search will not work on this system"
    WARN=$((WARN + 1))
fi

echo ""
echo "==> File Permissions Security Audit..."

# Function to check file permissions
check_perms() {
    local file="$1"
    local expected="$2"
    local name="$3"
    printf "%-35s" "$name"
    if [[ -e "$file" ]]; then
        actual=$(stat -c "%a" "$file" 2>/dev/null)
        if [[ "$actual" == "$expected" ]]; then
            echo "[OK] ($actual)"
            PASS=$((PASS + 1))
        else
            echo "[WARN] ($actual, expected $expected)"
            WARN=$((WARN + 1))
        fi
    else
        echo "[SKIP] (not present)"
        WARN=$((WARN + 1))
    fi
}

# Hooks directory should be 700 (owner execute only)
check_perms ~/.claude/hooks "700" "Hooks dir (700)"

# Credentials files should be 600 (owner read/write only)
check_perms ~/.claude/.credentials.json "600" "Credentials file (600)"
check_perms ~/mcp_agent_mail/.env "600" "MCP Agent Mail .env (600)"
check_perms ~/.beads/beads.db "600" "Beads database (600)"

# State files should be 600
for state_file in ~/.claude/agent-state.json ~/.claude/state-*.json; do
    if [[ -f "$state_file" ]]; then
        check_perms "$state_file" "600" "$(basename "$state_file") (600)"
    fi
done

echo ""
echo "=========================================="
if [[ $REFRESH -gt 0 ]]; then
    echo "  Results: $PASS passed, $FAIL failed, $WARN skipped"
    echo "           ($REFRESH tools need shell refresh)"
else
    echo "  Results: $PASS passed, $FAIL failed, $WARN skipped"
fi
echo "=========================================="

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo "Some checks failed. Review the output above."
    echo "Run individual install scripts to fix:"
    echo "  ./scripts/install/03-stack-tools.sh      # Stack tools"
    echo "  ./scripts/install/04-cloud-clis.sh       # Cloud CLIs"
    echo "  ./scripts/install/05-ai-agents.sh        # AI agents"
    echo "  ./scripts/install/08-shell-config.sh     # Shell config"
    echo "  ./scripts/install/10-knowledge-vibes.sh  # K&V workflow"
    exit 1
else
    echo ""
    echo "All required checks passed!"
    if [[ $REFRESH -gt 0 ]]; then
        echo ""
        echo "NOTE: $REFRESH tools are installed but not in current PATH."
        echo "      Run 'exec zsh' to refresh your shell environment."
    fi
    echo ""
    echo "Next steps:"
    echo "  1. exec zsh              # Switch to new shell (REQUIRED)"
    echo "  2. claude                # Authenticate Claude Code"
    echo "  3. codex login           # Authenticate Codex (optional)"
    echo ""
    echo "Quick start:"
    echo "  bd ready                 # See available work"
    echo "  ntm palette              # Command palette"
    echo ""
    echo "Slash commands (in Claude):"
    echo "  /prime      # Start session, register, claim work"
    echo "  /calibrate  # Check alignment between phases"
    echo "  /next-bead  # Close task, UBS scan, claim next"
    echo ""
fi
