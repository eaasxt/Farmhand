# Farmhand Implementation Plan

Prioritized roadmap for addressing all findings from the system evaluation.

**Last Updated:** 2025-12-28
**Status:** Phases 1-3 COMPLETE. Phase 4 (long-term) remains.

---

## Phase 1: Critical Fixes ✅ COMPLETE
**Goal:** Fix blocking issues that undermine core claims of the system.
**Completed:** 2025-12-27

### 1.1 Hook git_safety_guard.py into settings.json ✅
**Status:** COMPLETE
**Evidence:** Configured in `~/.claude/settings.json`

### 1.2 Fix mcp-agent-mail.service ✅
**Status:** COMPLETE (Farmhand-6a9)
**Evidence:** Service uses `__HOME__` placeholder, replaced at install time

### 1.3 Replace hardcoded /home/ubuntu paths ✅
**Status:** COMPLETE (Farmhand-6a9)
**Evidence:** All systemd services use `__HOME__` placeholders

### 1.4 Add BEADS_DB to zshrc.template ✅
**Status:** COMPLETE
**Evidence:** `export BEADS_DB="$HOME/.beads/beads.db"` in template and `~/.zshrc`

### 1.5 Fix Knowledge & Vibes silent failure ✅
**Status:** COMPLETE (Farmhand-2ae)
**Evidence:** Script uses `exit 1` instead of `return 1`

---

## Phase 2: High Priority Improvements ✅ COMPLETE
**Goal:** Address robustness and observability gaps.
**Completed:** 2025-12-27

### 2.1 Add state file cleanup to session-init.py ✅
**Status:** COMPLETE
**Evidence:** `cleanup_old_state_files()` function in session-init.py removes files >7 days old

### 2.2 Add health monitoring for MCP Agent Mail ✅
**Status:** COMPLETE (Farmhand-6kg, Farmhand-fbu)
**Evidence:** `bin/mcp-health-check` and `scripts/health-alerts.sh` exist

### 2.3 Create pytest test suite for hooks ✅
**Status:** COMPLETE (Farmhand-dk1, Farmhand-rpq)
**Evidence:** 9 test files in `tests/` directory:
- test_git_safety_guard.py
- test_reservation_checker.py
- test_todowrite_interceptor.py
- test_session_init.py
- test_mcp_state_tracker.py
- test_integration.py
- test_idempotency.py
- test_obs_mask.py
- conftest.py

### 2.4 Add UBS enforcement via git pre-commit hook ✅
**Status:** COMPLETE (Farmhand-bhi, Farmhand-wjw)
**Evidence:** `.git/hooks/pre-commit` runs UBS on staged files

### 2.5 Add escape hatch for experienced users ✅
**Status:** COMPLETE
**Evidence:** All hooks check `FARMHAND_SKIP_ENFORCEMENT=1` env var

---

## Phase 3: Medium Priority ✅ COMPLETE
**Goal:** Polish and documentation improvements.
**Completed:** 2025-12-27

### 3.1 Update troubleshooting.md with hook failures ✅
**Status:** COMPLETE (Farmhand-bna)
**Evidence:** `docs/troubleshooting.md` + `docs/troubleshooting-flowchart.md`

### 3.2 Add "Known Issues" section to README ✅
**Status:** COMPLETE (Farmhand-2nm)
**Evidence:** `docs/known-limitations.md` documents SQLite limits, single-machine, etc.

### 3.3 Verify all CLAUDE.md examples work ✅
**Status:** COMPLETE
**Evidence:** Comprehensive CLAUDE.md with working examples, alias fixes (Farmhand-6rk)

### 3.4 Add stale reservation cron cleanup ✅
**Status:** COMPLETE
**Evidence:** `scripts/farmhand-cleanup.service` + `farmhand-cleanup.timer`

### 3.5 Add systemd watchdog to MCP service ✅
**Status:** COMPLETE
**Evidence:** `Restart=on-failure` in mcp-agent-mail.service

---

## Additional Items Completed (Beyond Original Plan)

| Item | Bead | Description |
|------|------|-------------|
| ADR Directory | Farmhand-0zk | 5 Architecture Decision Records in `docs/adr/` |
| Hook Timeouts | Farmhand-ktf | Signal-based timeout (9s) prevents hook hangs |
| Multi-agent AGENT_NAME Enforcement | Farmhand-3ry | Blocks edits when multiple agents lack AGENT_NAME |
| Automated Backups | Farmhand-gx1 | `farmhand-backup.sh` for database backups |
| Version Management | Farmhand-58c, Farmhand-c4c | VERSION file, dynamic version reading |

---

## Phase 4: Long-Term Vision ⏳ NOT STARTED
**Goal:** Scale and extend the system.
**Timeline:** This Quarter (as capacity allows)

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
1. Add `~/.farmhand/plugins/` directory
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

## Success Metrics

| Phase | Success Criteria | Status |
|-------|------------------|--------|
| Phase 1 | Fresh install works on non-ubuntu user | ✅ ACHIEVED |
| Phase 2 | Test suite passes, MCP auto-recovers from crashes | ✅ ACHIEVED |
| Phase 3 | All documentation examples work as written | ✅ ACHIEVED |
| Phase 4 | 50+ agents can run concurrently | ⏳ PENDING |

---

## Effort Summary

| Phase | Estimated | Status |
|-------|-----------|--------|
| Phase 1 (Critical) | 3 hours | ✅ Complete |
| Phase 2 (High) | 20 hours | ✅ Complete |
| Phase 3 (Medium) | 9 hours | ✅ Complete |
| Phase 4 (Low) | 120+ hours | ⏳ Not Started |

**Production-ready milestone:** ✅ ACHIEVED (Phases 1-3 complete)
