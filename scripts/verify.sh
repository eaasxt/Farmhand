#!/usr/bin/env bash
set -euo pipefail

# Verify Farmhand v2.1.0 installation

echo "=========================================="
echo "  Farmhand v2.1.0 Installation Verify"
echo "=========================================="
echo ""

PASS=0
FAIL=0
WARN=0

check() {
    local name="$1"
    local cmd="$2"
    printf "%-35s" "$name"
    if eval "$cmd" &>/dev/null; then
        echo "[OK]"
        ((PASS++))
    else
        echo "[FAIL]"
        ((FAIL++))
    fi
}

check_optional() {
    local name="$1"
    local cmd="$2"
    printf "%-35s" "$name"
    if eval "$cmd" &>/dev/null; then
        echo "[OK]"
        ((PASS++))
    else
        echo "[SKIP]"
        ((WARN++))
    fi
}

check_service() {
    local name="$1"
    printf "%-35s" "$name service"
    if systemctl is-active --quiet "$name" 2>/dev/null; then
        echo "[RUNNING]"
        ((PASS++))
    else
        echo "[NOT RUNNING]"
        ((FAIL++))
    fi
}

echo "==> Core Tools..."
check "bd (beads)" "command -v bd"
check "bv (beads-viewer)" "command -v bv"
check "qmd" "command -v qmd"

echo ""
echo "==> Dicklesworthstone Stack..."
check "ast-grep (UBS JS/TS)" "command -v ast-grep || command -v sg"
check "ubs (bug scanner)" "command -v ubs"
check "ntm (tmux manager)" "command -v ntm"
check "cm (cass memory)" "command -v cm"
check "caam (account manager)" "command -v caam"
check_optional "slb (launch button)" "command -v slb"
check "cass (session search)" "command -v cass"

echo ""
echo "==> Cloud CLIs..."
check_optional "vault" "command -v vault"
check_optional "wrangler" "command -v wrangler"
check_optional "supabase" "command -v supabase"
check_optional "vercel" "command -v vercel"

echo ""
echo "==> AI Coding Agents..."
check "claude" "command -v claude"
check "codex" "command -v codex"
check_optional "gemini" "command -v gemini"

echo ""
echo "==> Runtime Dependencies..."
check "bun" "command -v bun"
check "uv" "command -v uv"
check "node" "command -v node"
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

echo ""
echo "==> Knowledge & Vibes Workflow..."
# Check skills directory has content
printf "%-35s" "Skills (18 expected)"
SKILLS_COUNT=$(ls ~/.claude/skills/ 2>/dev/null | wc -l)
if [[ "$SKILLS_COUNT" -ge 15 ]]; then
    echo "[OK] ($SKILLS_COUNT installed)"
    ((PASS++))
else
    echo "[INCOMPLETE] ($SKILLS_COUNT installed)"
    ((FAIL++))
fi

# Check commands
printf "%-35s" "Commands (7 expected)"
CMDS_COUNT=$(ls ~/.claude/commands/ 2>/dev/null | wc -l)
if [[ "$CMDS_COUNT" -ge 5 ]]; then
    echo "[OK] ($CMDS_COUNT installed)"
    ((PASS++))
else
    echo "[INCOMPLETE] ($CMDS_COUNT installed)"
    ((FAIL++))
fi

# Check rules
printf "%-35s" "Rules (3 expected)"
RULES_COUNT=$(ls ~/.claude/rules/ 2>/dev/null | wc -l)
if [[ "$RULES_COUNT" -ge 3 ]]; then
    echo "[OK] ($RULES_COUNT installed)"
    ((PASS++))
else
    echo "[INCOMPLETE] ($RULES_COUNT installed)"
    ((FAIL++))
fi

# Check templates
printf "%-35s" "Templates (8 expected)"
TEMPLATES_COUNT=$(ls ~/templates/ 2>/dev/null | wc -l)
if [[ "$TEMPLATES_COUNT" -ge 5 ]]; then
    echo "[OK] ($TEMPLATES_COUNT installed)"
    ((PASS++))
else
    echo "[INCOMPLETE] ($TEMPLATES_COUNT installed)"
    ((FAIL++))
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
    ((PASS++))
else
    echo "[MISSING]"
    ((FAIL++))
fi

printf "%-35s" "qwen3-reranker"
if ollama list 2>/dev/null | grep -q "qwen3-reranker"; then
    echo "[INSTALLED]"
    ((PASS++))
else
    echo "[MISSING]"
    ((FAIL++))
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
    ((PASS++))
else
    echo "[WARN] (use Homebrew path)"
    ((WARN++))
fi

# Check for stale agent state
printf "%-35s" "Agent state freshness"
if [[ -f ~/.claude/agent-state.json ]]; then
    STATE_AGE=$(( $(date +%s) - $(stat -c %Y ~/.claude/agent-state.json 2>/dev/null || echo 0) ))
    if [[ $STATE_AGE -gt 14400 ]]; then  # 4 hours
        echo "[STALE] (>4h old, run bd-cleanup)"
        ((WARN++))
    else
        echo "[OK]"
        ((PASS++))
    fi
else
    echo "[NONE] (will create on first run)"
    ((PASS++))
fi

echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed, $WARN skipped"
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
    echo ""
    echo "Quick start:"
    echo "  1. exec zsh              # Switch to new shell"
    echo "  2. bd ready              # See available work"
    echo "  3. ntm palette           # Command palette"
    echo ""
    echo "Slash commands (in Claude):"
    echo "  /prime      # Start session, register, claim work"
    echo "  /calibrate  # Check alignment between phases"
    echo "  /next-bead  # Close task, UBS scan, claim next"
    echo ""
fi
