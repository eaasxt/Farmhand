#!/usr/bin/env bash
set -euo pipefail

# Verify JohnDeere v2.0.0 installation

echo "=========================================="
echo "  JohnDeere v2.0.0 Installation Verify"
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
printf "%-35s" "JohnDeere version"
if [[ -f ~/.johndeere/version ]]; then
    echo "v$(cat ~/.johndeere/version)"
else
    echo "[NOT TRACKED]"
fi

printf "%-35s" "Claude Code version"
if command -v claude &>/dev/null; then
    claude --version 2>&1 | head -1 || echo "[UNKNOWN]"
else
    echo "[NOT INSTALLED]"
fi

echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed, $WARN skipped"
echo "=========================================="

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo "Some checks failed. Review the output above."
    echo "Run individual install scripts to fix:"
    echo "  ./scripts/install/03-stack-tools.sh   # Stack tools"
    echo "  ./scripts/install/04-cloud-clis.sh    # Cloud CLIs"
    echo "  ./scripts/install/05-ai-agents.sh     # AI agents"
    echo "  ./scripts/install/08-shell-config.sh  # Shell config"
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
fi
