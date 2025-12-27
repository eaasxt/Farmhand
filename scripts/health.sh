#!/usr/bin/env bash
# Quick health check - run anytime to verify system status

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; }

echo "=== Health Check ==="

# Services
systemctl is-active --quiet mcp-agent-mail && ok "mcp-agent-mail running" || fail "mcp-agent-mail DOWN"
systemctl is-active --quiet ollama && ok "ollama running" || fail "ollama DOWN"

# APIs
curl -sf http://localhost:11434/api/version >/dev/null && ok "Ollama API responding" || fail "Ollama API DOWN"
curl -sf -X POST -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "health_check", "arguments": {}}, "id": 1}' http://127.0.0.1:8765/mcp/ | jq -e '.result | .isError == false' >/dev/null && ok "MCP API responding" || fail "MCP API DOWN"

# Hooks
test -f ~/.claude/hooks/todowrite-interceptor.py && ok "Enforcement hooks installed" || fail "Hooks missing (run 07-hooks.sh)"

# State
test -f ~/.claude/agent-state.json && ok "Agent state file exists" || echo "  (no agent state yet - normal for new session)"
test -f ~/.beads/beads.db && ok "Beads DB exists" || fail "Beads DB missing"

# Orphaned work check
if command -v bd &>/dev/null; then
    IN_PROGRESS=$(bd list --status=in_progress 2>/dev/null | grep -v "^$" | wc -l | tr -d ' ' || echo 0)
    if [ "$IN_PROGRESS" -gt 0 ] 2>/dev/null; then
        echo "  ⚠ $IN_PROGRESS issues in_progress (run 'bd list --status=in_progress')"
    fi
fi

echo ""
echo "Run './scripts/verify.sh' for full verification"
