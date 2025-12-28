# Farmhand Roadmap

**Status:** Phases 1-3 COMPLETE. Phase 4+ in planning.
**Last Updated:** 2025-12-28

---

## Philosophy

> Enhancements must be "bolt-on" additions that improve functionality without destabilizing the core "Enforcement Layer" (hooks/reservations).

| Principle | Meaning |
|-----------|---------|
| **ADDITIVE ONLY** | No rewrites. New files, new scripts, new optional features. |
| **OPT-IN** | All enhancements disabled by default. User explicitly enables. |
| **BACKWARDS COMPATIBLE** | Existing workflows must continue unchanged. |
| **INCREMENTAL** | Small PRs. Frequent integration. Easy rollback. |
| **FALLBACK SAFE** | If new feature fails, old behavior continues. |

---

## Completed Work

### Phase 1: Critical Fixes (COMPLETE)

| Item | Bead | Description |
|------|------|-------------|
| Hook git_safety_guard.py | - | Configured in settings.json |
| Fix mcp-agent-mail.service | Farmhand-6a9 | Uses `__HOME__` placeholder |
| Replace hardcoded paths | Farmhand-6a9 | All systemd services use placeholders |
| Add BEADS_DB to zshrc | - | Export in template and ~/.zshrc |
| Fix Knowledge & Vibes | Farmhand-2ae | Script uses `exit 1` not `return 1` |

### Phase 2: High Priority Improvements (COMPLETE)

| Item | Bead | Description |
|------|------|-------------|
| State file cleanup | - | `cleanup_old_state_files()` removes files >7 days |
| Health monitoring | Farmhand-6kg, Farmhand-fbu | `bin/mcp-health-check` and `scripts/health-alerts.sh` |
| Hook test suite | Farmhand-dk1, Farmhand-rpq | 9 test files in `tests/` directory |
| UBS pre-commit | Farmhand-bhi, Farmhand-wjw | `.git/hooks/pre-commit` runs UBS |
| Escape hatch | - | All hooks check `FARMHAND_SKIP_ENFORCEMENT=1` |

### Phase 3: Polish & Documentation (COMPLETE)

| Item | Bead | Description |
|------|------|-------------|
| Troubleshooting docs | Farmhand-bna | `docs/troubleshooting.md` with flowcharts |
| Known limitations | Farmhand-2nm | `docs/known-limitations.md` |
| CLAUDE.md examples | Farmhand-6rk | Working examples, alias fixes |
| Stale reservation cron | - | `farmhand-cleanup.service` + timer |
| Systemd watchdog | - | `Restart=on-failure` in mcp-agent-mail.service |

### Additional Completed Items

| Item | Bead | Description |
|------|------|-------------|
| ADR Directory | Farmhand-0zk | 5 Architecture Decision Records in `docs/adr/` |
| Hook Timeouts | Farmhand-ktf | Signal-based timeout (4.5s) prevents hook hangs |
| Multi-agent AGENT_NAME | Farmhand-3ry | Per-agent state files via AGENT_NAME env var |
| Automated Backups | Farmhand-gx1 | `farmhand-backup.sh` for database backups |
| Version Management | Farmhand-58c, Farmhand-c4c | VERSION file, dynamic version reading |
| Timestamp bug fixes | - | Fixed reservation-checker.py and mcp-state-tracker.py |

---

## Phase 4: Long-Term Vision (NOT STARTED)

### 4.1 Automated Work Dispatcher

**Goal:** Push-based task assignment to reduce agent idle time.

**Problem:** Agents poll `bd ready` to find work. Multiple agents may race for the same bead. Idle agents don't know when new work becomes unblocked.

**Solution:** A dispatcher that monitors the beads graph and proactively assigns work to available agents via Agent Mail.

**Architecture (Recommended: Hybrid):**
1. PostToolUse hook on `bd close` triggers immediate assignment attempt
2. Cron job (every 1 min) catches any missed assignments
3. Agent Mail for notifications ("You have been assigned Farmhand-xyz")

**Implementation Phases:**

| Phase | Feature | Complexity |
|-------|---------|------------|
| 4.1a | Idle agent detection via `last_active_ts` | Low |
| 4.1b | Assignment notifications via Agent Mail | Medium |
| 4.1c | Opt-in auto-claiming on behalf of agents | Medium |
| 4.1d | Parallel track optimization | High (defer to v2) |

**Agent States:**
```
IDLE        - Registered, no active bead, ready for work
WORKING     - Has claimed bead, actively executing
BLOCKED     - Waiting on dependency or resource
OFFLINE     - No heartbeat in last N minutes
```

**Success Metrics:**
| Metric | Current | Target |
|--------|---------|--------|
| Time from bead-ready to claim | Manual (minutes) | < 30 seconds |
| Agent idle time | Unknown | < 10% of session |
| Duplicate claims (races) | Occasional | Zero |

**Open Questions:**
1. Should dispatcher run per-project or globally? (Recommend: per-project)
2. How should agent "specializations" be represented?
3. What's the maximum acceptable latency from bead-ready to dispatch?

---

### 4.2 PostgreSQL Backend Option

**Priority:** Low (long-term)
**Effort:** 2 weeks

**Enables:** Distributed agents across multiple machines.

**Approach:**
1. Abstract database layer in MCP Agent Mail
2. Add PostgreSQL connection option
3. Update reservation queries for PostgreSQL syntax
4. Add connection pooling (pgbouncer recommended)
5. Document setup for remote agents

---

### 4.3 Lossless Spec Verification Tool

**Priority:** Low (long-term)
**Effort:** 1 week

**Concept:** LLM-based check that asks "Are there any ambiguities in this spec?"

**Approach:**
1. Create `/verify-spec` skill
2. Pass spec to LLM with prompt: "List any ambiguities, undefined terms, or questions that would need answers to implement this."
3. If any found, block until resolved

---

### 4.4 Plugin Ecosystem

**Priority:** Low (long-term)
**Effort:** 2 weeks

**Concept:** Allow users to add custom hooks/skills without modifying core files.

**Approach:**
1. Add `~/.farmhand/plugins/` directory
2. Auto-load hooks from `plugins/hooks/`
3. Auto-load skills from `plugins/skills/`
4. Document plugin API

---

### 4.5 Connection Pooling + Read Replicas

**Priority:** Low (long-term)
**Effort:** 3 weeks

**Enables:** 50+ concurrent agents.

**Approach:**
1. Switch to PostgreSQL (see 4.2)
2. Add read replicas for reservation queries
3. Use write primary for mutations
4. Implement proper connection pooling

---

## Backlog: Nice-to-Have Features

### Infrastructure Improvements

| Task | Description | Risk |
|------|-------------|------|
| JIT Dynamic Reservations | Granular, short-lived file reservations based on analysis | Medium |
| Shared Knowledge Base | Centralized cache for codebase understanding | Medium |
| Path normalization | Add `$HOME` support with hardcoded fallback | Low |
| Service health checks | Check MCP/Ollama before operations | Low |

### Documentation

| Task | Description | Status |
|------|-------------|--------|
| Known limitations | Document edge cases | Done |
| Troubleshooting flowchart | Decision tree for common issues | Done |
| ADR directory | Architecture Decision Records | Done |

---

## Rejected Approaches

These were considered but rejected to preserve stability:

| Approach | Why Rejected |
|----------|--------------|
| Rewrite hooks in different language | Too fundamental |
| Replace SQLite with Postgres (for core) | Not additive |
| Change MCP Agent Mail protocol | Breaking change |
| Restructure directory layout | Existing paths baked in |
| Auto-migration of existing installs | Too risky |

---

## Success Metrics

| Phase | Success Criteria | Status |
|-------|------------------|--------|
| Phase 1 | Fresh install works on non-ubuntu user | ACHIEVED |
| Phase 2 | Test suite passes, MCP auto-recovers from crashes | ACHIEVED |
| Phase 3 | All documentation examples work as written | ACHIEVED |
| Phase 4 | 50+ agents can run concurrently | PENDING |

---

## Related Documentation

- `troubleshooting.md` - Diagnostic decision trees
- `known-limitations.md` - Current system constraints
- `agent-mail-schemas.md` - Structured message formats for multi-agent coordination
- `adr/` - Architecture Decision Records
