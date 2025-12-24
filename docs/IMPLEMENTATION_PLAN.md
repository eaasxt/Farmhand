# JohnDeere Implementation Plan

Prioritized roadmap for addressing all findings from the system evaluation.

---

## Phase 1: Critical Fixes (This Week)
**Goal:** Fix blocking issues that undermine core claims of the system.

### 1.1 Hook git_safety_guard.py into settings.json
**Priority:** 🔴 CRITICAL
**Effort:** 5 minutes
**Files:**
- `config/claude-settings.json`
- `~/.claude/settings.json` (live)

**Problem:** The hook exists and works, but isn't configured. Destructive git commands are allowed despite documentation claiming otherwise.

**Fix:**
```json
// Add to PreToolUse array in settings.json:
{
  "matcher": "Bash",
  "hooks": [{"type": "command", "command": "/home/ubuntu/.claude/hooks/git_safety_guard.py"}]
}
```

**Verification:** Run `echo '{"tool_name":"Bash","tool_input":{"command":"git reset --hard"}}' | ~/.claude/hooks/git_safety_guard.py` - should output deny JSON.

---

### 1.2 Fix mcp-agent-mail.service
**Priority:** 🔴 CRITICAL
**Effort:** 10 minutes
**Files:**
- `config/systemd/mcp-agent-mail.service`

**Problem:** Line 11 sources `/home/ubuntu/.local/bin/env` which doesn't exist. Service fails to start on fresh install.

**Current (broken):**
```ini
ExecStart=/bin/bash -c 'source /home/ubuntu/.local/bin/env && cd /home/ubuntu/mcp_agent_mail && ...'
```

**Fixed:**
```ini
Environment="PATH=/home/ubuntu/.local/bin:/home/ubuntu/.bun/bin:/usr/local/bin:/usr/bin:/bin"
WorkingDirectory=/home/ubuntu/mcp_agent_mail
ExecStart=/home/ubuntu/mcp_agent_mail/scripts/run_server.sh
```

**Verification:** `sudo systemctl daemon-reload && sudo systemctl restart mcp-agent-mail && sudo systemctl status mcp-agent-mail`

---

### 1.3 Replace hardcoded /home/ubuntu paths
**Priority:** 🔴 CRITICAL
**Effort:** 2 hours
**Files:**
- `scripts/install/02-core-tools.sh` (line 99 - qmd wrapper)
- `scripts/install/07-mcp-agent-mail.sh`
- `scripts/install/09-hooks.sh`
- `config/systemd/mcp-agent-mail.service`
- `config/systemd/ollama.service`
- `hooks/reservation-checker.py` (examples in comments)

**Approach:**
1. Define `INSTALL_USER` and `INSTALL_HOME` at top of install.sh
2. Pass to child scripts via environment
3. Use variable expansion in all paths

**Pattern:**
```bash
# At top of install.sh
export INSTALL_USER="${SUDO_USER:-$(whoami)}"
export INSTALL_HOME=$(eval echo "~$INSTALL_USER")

# In child scripts, replace:
#   /home/ubuntu → $INSTALL_HOME
#   ubuntu (user) → $INSTALL_USER
```

**Verification:** Run install on a test user account (not ubuntu).

---

### 1.4 Add BEADS_DB to zshrc.template
**Priority:** 🔴 CRITICAL
**Effort:** 5 minutes
**Files:**
- `config/zshrc.template`

**Problem:** `bd` command may use wrong database path if BEADS_DB not set.

**Fix:** Add after PATH exports:
```bash
# Beads configuration
export BEADS_DB="$HOME/.beads/beads.db"
export BEADS_DIR="$HOME/.beads"
```

**Verification:** `source ~/.zshrc && echo $BEADS_DB`

---

### 1.5 Fix Knowledge & Vibes silent failure
**Priority:** 🔴 CRITICAL
**Effort:** 10 minutes
**Files:**
- `scripts/install/10-knowledge-vibes.sh`

**Problem:** Uses `return 1` which doesn't propagate in sourced context.

**Fix:**
```bash
# Replace: return 1
# With:
echo "ERROR: Knowledge & Vibes installation failed" >&2
exit 1

# Or wrap the source call in install.sh:
source scripts/install/10-knowledge-vibes.sh || {
    echo "FATAL: Knowledge & Vibes installation failed"
    exit 1
}
```

**Verification:** Intentionally break the script, verify parent stops.

---

## Phase 2: High Priority Improvements (Next 2 Weeks)
**Goal:** Address robustness and observability gaps.

### 2.1 Add state file cleanup to session-init.py
**Priority:** 🟠 HIGH
**Effort:** 2 hours
**Files:**
- `hooks/session-init.py`

**Problem:** State files accumulate forever. After 100 sessions = 100 files.

**Fix:**
```python
def cleanup_old_state_files():
    """Remove state files older than 7 days."""
    state_dir = Path.home() / ".claude"
    cutoff = time.time() - (7 * 24 * 3600)

    for state_file in state_dir.glob("state-*.json"):
        if state_file.stat().st_mtime < cutoff:
            state_file.unlink()
            print(f"Cleaned up old state file: {state_file.name}")
```

Call this at session start (after clearing current agent's state).

---

### 2.2 Add health monitoring for MCP Agent Mail
**Priority:** 🟠 HIGH
**Effort:** 4 hours
**Files:**
- Create `bin/mcp-health-check`
- Create `config/systemd/mcp-health-check.timer`

**Approach:**
1. Script that pings `http://127.0.0.1:8765/mcp/` with a test request
2. If fails 3x in a row, restart MCP service
3. Log to syslog
4. Systemd timer runs every 5 minutes

```bash
#!/bin/bash
# bin/mcp-health-check
ENDPOINT="http://127.0.0.1:8765/mcp/"
MAX_RETRIES=3

for i in $(seq 1 $MAX_RETRIES); do
    if curl -s -f -o /dev/null "$ENDPOINT"; then
        exit 0
    fi
    sleep 2
done

logger "MCP Agent Mail unresponsive, restarting..."
sudo systemctl restart mcp-agent-mail
```

---

### 2.3 Create pytest test suite for hooks
**Priority:** 🟠 HIGH
**Effort:** 8 hours
**Files:**
- Create `tests/` directory
- Create `tests/test_hooks.py`
- Create `tests/conftest.py`

**Test cases:**
```python
# tests/test_hooks.py

def test_todowrite_interceptor_blocks():
    """TodoWrite should always be denied."""

def test_reservation_checker_allows_registered_reserved():
    """Edit allowed when registered AND file reserved."""

def test_reservation_checker_blocks_unregistered():
    """Edit blocked when not registered."""

def test_reservation_checker_blocks_unreserved():
    """Edit blocked when file not reserved."""

def test_reservation_checker_blocks_other_agent():
    """Edit blocked when another agent has reservation."""

def test_git_safety_guard_blocks_hard_reset():
    """git reset --hard should be blocked."""

def test_git_safety_guard_allows_checkout_branch():
    """git checkout -b should be allowed."""

def test_session_init_clears_state():
    """Session start should clear this agent's state file."""
```

---

### 2.4 Add UBS enforcement via git pre-commit hook
**Priority:** 🟠 HIGH
**Effort:** 2 hours
**Files:**
- Create `config/git-hooks/pre-commit`
- Update `scripts/install/09-hooks.sh`

**Approach:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Get staged files
STAGED=$(git diff --cached --name-only --diff-filter=ACMR)

if [ -z "$STAGED" ]; then
    exit 0
fi

# Run UBS on staged files
echo "Running UBS security scan..."
if ! ubs $STAGED; then
    echo "ERROR: UBS found issues. Fix before committing."
    exit 1
fi
```

Install via: `cp config/git-hooks/pre-commit .git/hooks/ && chmod +x .git/hooks/pre-commit`

---

### 2.5 Add escape hatch for experienced users
**Priority:** 🟠 HIGH
**Effort:** 4 hours
**Files:**
- `hooks/reservation-checker.py`
- `hooks/todowrite-interceptor.py`

**Approach:** Check for `JOHNDEERE_SKIP_ENFORCEMENT=1` env var:

```python
# At top of each hook:
if os.environ.get("JOHNDEERE_SKIP_ENFORCEMENT") == "1":
    sys.exit(0)  # Allow everything
```

**Usage:**
```bash
# Quick fix mode - bypasses all enforcement
JOHNDEERE_SKIP_ENFORCEMENT=1 claude

# Normal mode - full enforcement
claude
```

**Documentation:** Add warning that this disables safety features.

---

## Phase 3: Medium Priority (This Month)
**Goal:** Polish and documentation improvements.

### 3.1 Update troubleshooting.md with hook failures
**Priority:** 🟡 MEDIUM
**Effort:** 2 hours
**Files:**
- `docs/troubleshooting.md`

**Add sections for:**
- "Hook execution failed" errors
- "Reservation database locked" (concurrent agent issue)
- "Agent not registered" - step-by-step fix
- "File reserved by another agent" - coordination steps
- "Ollama out of memory" - GPU selection

---

### 3.2 Add "Known Issues" section to README
**Priority:** 🟡 MEDIUM
**Effort:** 1 hour
**Files:**
- `README.md`

**Content:**
- SQLite concurrency limit (~10-15 agents)
- Single-machine assumption (no distributed support)
- State file cleanup not automatic
- Manual recovery required after crashes

---

### 3.3 Verify all CLAUDE.md examples work
**Priority:** 🟡 MEDIUM
**Effort:** 3 hours
**Files:**
- `config/CLAUDE.md`
- `~/CLAUDE.md`

**Approach:**
1. Read through every code example
2. Run each command/snippet
3. Fix any that fail
4. Update paths to use `$HOME` instead of `/home/ubuntu`

---

### 3.4 Add stale reservation cron cleanup
**Priority:** 🟡 MEDIUM
**Effort:** 2 hours
**Files:**
- Create `bin/cleanup-stale-reservations`
- Create `config/cron/johndeere-cleanup`

**Cron entry:**
```cron
# /etc/cron.d/johndeere-cleanup
0 * * * * ubuntu /home/ubuntu/.local/bin/cleanup-stale-reservations --force --stale-hours=2
```

This auto-releases reservations older than 2 hours every hour.

---

### 3.5 Add systemd watchdog to MCP service
**Priority:** 🟡 MEDIUM
**Effort:** 1 hour
**Files:**
- `config/systemd/mcp-agent-mail.service`

**Add:**
```ini
[Service]
WatchdogSec=30
Restart=on-failure
RestartSec=5
```

Requires MCP server to call `sd_notify("WATCHDOG=1")` periodically, or use `Type=notify`.

---

## Phase 4: Long-Term Vision (This Quarter)
**Goal:** Scale and extend the system.

### 4.1 PostgreSQL backend option for MCP
**Priority:** 🟢 LOW (long-term)
**Effort:** 2 weeks

**Enables:** Distributed agents across multiple machines.

**Approach:**
1. Abstract database layer in MCP Agent Mail
2. Add PostgreSQL connection option
3. Update reservation queries for PostgreSQL syntax
4. Add connection pooling (pgbouncer recommended)
5. Document setup for remote agents

---

### 4.2 Lossless spec verification tool
**Priority:** 🟢 LOW (long-term)
**Effort:** 1 week

**Concept:** LLM-based check that asks "Are there any ambiguities in this spec?"

**Approach:**
1. Create `/verify-spec` skill
2. Pass spec to LLM with prompt: "List any ambiguities, undefined terms, or questions that would need answers to implement this."
3. If any found, block until resolved

---

### 4.3 Plugin ecosystem for custom hooks/skills
**Priority:** 🟢 LOW (long-term)
**Effort:** 2 weeks

**Concept:** Allow users to add custom hooks without modifying core files.

**Approach:**
1. Add `~/.johndeere/plugins/` directory
2. Auto-load hooks from `plugins/hooks/`
3. Auto-load skills from `plugins/skills/`
4. Document plugin API

---

### 4.4 Connection pooling + read replicas for scaling
**Priority:** 🟢 LOW (long-term)
**Effort:** 3 weeks

**Enables:** 50+ concurrent agents.

**Approach:**
1. Switch to PostgreSQL (see 4.1)
2. Add read replicas for reservation queries
3. Use write primary for mutations
4. Implement proper connection pooling

---

## Implementation Order

```
Week 1:
  ├── 1.1 Hook git_safety_guard (5 min)
  ├── 1.2 Fix mcp-agent-mail.service (10 min)
  ├── 1.4 Add BEADS_DB to zshrc (5 min)
  ├── 1.5 Fix K&V silent failure (10 min)
  └── 1.3 Replace hardcoded paths (2 hours)

Week 2:
  ├── 2.1 State file cleanup (2 hours)
  ├── 2.4 UBS pre-commit hook (2 hours)
  └── 2.5 Escape hatch (4 hours)

Week 3:
  ├── 2.3 Pytest test suite (8 hours)
  └── 2.2 Health monitoring (4 hours)

Week 4:
  ├── 3.1 Update troubleshooting.md (2 hours)
  ├── 3.2 Known Issues in README (1 hour)
  └── 3.3 Verify CLAUDE.md examples (3 hours)

Ongoing:
  ├── 3.4 Stale reservation cron (2 hours)
  ├── 3.5 Systemd watchdog (1 hour)
  └── Phase 4 items as capacity allows
```

---

## Success Metrics

| Phase | Success Criteria |
|-------|------------------|
| Phase 1 | Fresh install works on non-ubuntu user |
| Phase 2 | Test suite passes, MCP auto-recovers from crashes |
| Phase 3 | All documentation examples work as written |
| Phase 4 | 50+ agents can run concurrently |

---

## Total Effort Estimate

| Phase | Hours | Calendar Time |
|-------|-------|---------------|
| Phase 1 (Critical) | 3 | 1 day |
| Phase 2 (High) | 20 | 1 week |
| Phase 3 (Medium) | 9 | 3 days |
| Phase 4 (Low) | 120+ | 1-2 months |

**To production-ready:** ~32 hours over 2 weeks
