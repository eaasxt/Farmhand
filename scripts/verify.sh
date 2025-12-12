#!/usr/bin/env bash
set -euo pipefail

# Verify JohnDeere installation

echo "=========================================="
echo "  JohnDeere Installation Verification"
echo "=========================================="
echo ""

PASS=0
FAIL=0

check() {
    local name="$1"
    local cmd="$2"
    printf "%-30s" "$name"
    if eval "$cmd" &>/dev/null; then
        echo "[OK]"
        ((PASS++))
    else
        echo "[FAIL]"
        ((FAIL++))
    fi
}

check_service() {
    local name="$1"
    printf "%-30s" "$name service"
    if systemctl is-active --quiet "$name"; then
        echo "[RUNNING]"
        ((PASS++))
    else
        echo "[NOT RUNNING]"
        ((FAIL++))
    fi
}

echo "==> Checking tools..."
check "bd (beads)" "command -v bd"
check "bv (beads-viewer)" "command -v bv"
check "qmd" "command -v qmd"
check "ollama" "command -v ollama"
check "claude" "command -v claude"
check "bun" "command -v bun"
check "uv" "command -v uv"

echo ""
echo "==> Checking services..."
check_service "mcp-agent-mail"
check_service "ollama"

echo ""
echo "==> Checking configuration..."
check "CLAUDE.md exists" "test -f ~/CLAUDE.md"
check "Beads DB exists" "test -f ~/.beads/beads.db"
check "Claude MCP settings" "test -f ~/.config/claude-code/settings.json"
check "Claude hooks settings" "test -f ~/.claude/settings.json"
check "MCP Agent Mail dir" "test -d ~/mcp_agent_mail"

echo ""
echo "==> Checking enforcement hooks..."
check "todowrite-interceptor" "test -x ~/.claude/hooks/todowrite-interceptor.py"
check "reservation-checker" "test -x ~/.claude/hooks/reservation-checker.py"
check "mcp-state-tracker" "test -x ~/.claude/hooks/mcp-state-tracker.py"
check "session-init" "test -x ~/.claude/hooks/session-init.py"
check "bd-cleanup" "test -x ~/.local/bin/bd-cleanup"

echo ""
echo "==> Checking connectivity..."
check "Ollama API" "curl -s http://localhost:11434/api/version"
check "MCP Agent Mail API" "curl -s http://localhost:8765/health"

echo ""
echo "==> Checking Ollama models..."
printf "%-30s" "embeddinggemma"
if ollama list 2>/dev/null | grep -q "embeddinggemma"; then
    echo "[INSTALLED]"
    ((PASS++))
else
    echo "[MISSING]"
    ((FAIL++))
fi

printf "%-30s" "qwen3-reranker"
if ollama list 2>/dev/null | grep -q "qwen3-reranker"; then
    echo "[INSTALLED]"
    ((PASS++))
else
    echo "[MISSING]"
    ((FAIL++))
fi

echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=========================================="

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo "Some checks failed. Review the output above."
    exit 1
else
    echo ""
    echo "All checks passed! Your environment is ready."
    echo ""
    echo "Quick start:"
    echo "  1. Run: claude"
    echo "  2. Check: bd ready"
    echo ""
fi
