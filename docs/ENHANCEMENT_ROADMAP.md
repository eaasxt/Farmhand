# Farmhand Enhancement Roadmap

**Status:** UNIFIED DRAFT - Awaiting Full Agent Consensus
**Thread:** `farmhand-enhancements-2025`
**Contributors:** BrownHill, GreenCat, FuchsiaHill, WhitePond
**Last Updated:** 2025-12-27

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

## Agent Status

| Agent | Current Task | Status | Last Active |
|-------|--------------|--------|-------------|
| BrownHill | farmhand-doctor CLI | In Progress | 16:37 |
| GreenCat | _Unknown_ | - | - |
| FuchsiaHill | _Unknown_ | - | - |
| WhitePond | Coordination | Active | NOW |
| WhiteDog | _Awaiting response_ | - | 04:56 |
| GreenPond | Timestamp bugs | - | 15:05 |
| OrangePond | Timestamp bugs | - | 15:33 |
| PinkDog | update.sh hooks | - | 15:13 |
| BrownSnow | Code review bn9 | - | 15:02 |
| FuchsiaDog | Timestamp bugs | - | 15:33 |

---

## Phase 1: Quick Wins (Immediate Priority)

Focus on operational stability, monitoring, and developer experience.

*   **[ASSIGNED: BrownHill] `farmhand-doctor` CLI Tool**
    *   **Goal:** A single command to diagnose system health.
    *   **Checks:** Agent registration, MCP server status, hook installation, disk space, git status.
    *   **Status:** In Progress

*   **[OPEN] Automated Backup System**
    *   **Goal:** Prevent data loss of the `beads` and `mcp-agent-mail` databases.
    *   **Implementation:** Script + systemd timer for nightly backups.

*   **[OPEN] Stale Reservation Cleanup**
    *   **Goal:** Auto-release files held by crashed/inactive agents.
    *   **Implementation:** Enhance `bd-cleanup` to run automatically via cron/systemd.

*   **[OPEN] Health Alerts**
    *   **Goal:** Proactive notification of system issues.
    *   **Implementation:** Integration with `notify-send` or desktop notifications.

## Phase 2: Workflow Automation (Next)

Focus on increasing agent efficiency and parallelism.

*   **Automated Work Dispatcher**
    *   **Goal:** Push-based task assignment to reduce agent idle time.
    *   **Concept:** MCP service monitoring `bd` for unblocked tasks and notifying idle agents.

*   **JIT Dynamic Reservations**
    *   **Goal:** Reduce lock contention.
    *   **Concept:** Granular, short-lived file reservations based on analysis.

## Phase 3: Shared Intelligence (Future)

Focus on collective learning.

*   **Shared Knowledge Base**
    *   **Goal:** Centralized cache for codebase understanding.
    *   **Concept:** Shared vector store or summary cache for file analysis.

---

## Additional Enhancements Identified (WhitePond Analysis)

### Infrastructure Fixes (Low Risk)

| Task | Description | Type | Owner |
|------|-------------|------|-------|
| Path normalization | Add `$HOME` support with hardcoded fallback | Bolt-on | _Open_ |
| CASS timeline bug | Report upstream (timestamps ms vs s) | External | _Open_ |
| Gemini hideWindowTitle | Already in install/update scripts | Done | WhitePond |

### Robustness (Medium Risk)

| Task | Description | Type | Owner |
|------|-------------|------|-------|
| Hook timeouts | Add configurable timeout to prevent hangs | Config | _Open_ |
| Service health checks | Check MCP/Ollama before operations | New script | _Open_ |
| Better error messages | Actionable guidance in hook errors | Enhancement | _Open_ |

### Documentation (No Risk)

| Task | Description | Type | Owner |
|------|-------------|------|-------|
| Known limitations | Document edge cases | New file | _Open_ |
| Troubleshooting flowchart | Decision tree for common issues | New file | _Open_ |
| ADR directory | Architecture Decision Records | New dir | _Open_ |

---

## Consensus Checklist

Before any implementation begins:

- [ ] All active agents have responded to thread `farmhand-enhancements-2025`
- [ ] Task assignments confirmed (no overlaps)
- [ ] User has approved Phase 1 scope
- [ ] Beads created for each claimed task

### Agent Response Status

| Agent | Responded? | Claimed Tasks |
|-------|------------|---------------|
| BrownHill | Yes (via doc) | farmhand-doctor |
| GreenCat | Yes (via doc) | _Unknown_ |
| FuchsiaHill | Yes (via doc) | _Unknown_ |
| WhitePond | Yes | Coordination |
| WhiteDog | **NO** | - |
| GreenPond | **NO** | - |
| OrangePond | **NO** | - |
| PinkDog | **NO** | - |
| BrownSnow | **NO** | - |
| FuchsiaDog | **NO** | - |

**Consensus Status:** 4/10 agents responded. **WAITING FOR INPUT.**

---

## Rejected Approaches

These were considered but rejected to preserve stability:

| Approach | Why Rejected |
|----------|--------------|
| Rewrite hooks in different language | Too fundamental |
| Replace SQLite with Postgres | Not additive |
| Change MCP Agent Mail protocol | Breaking change |
| Restructure directory layout | Existing paths baked in |
| Auto-migration of existing installs | Too risky |

---

**Maintenance & Governance**

*   This roadmap is a living document.
*   Agents must "Claim" tasks via `bd` and `AGENTS.md` before starting.
*   All changes must pass `ubs` scanning.
*   Thread `farmhand-enhancements-2025` is the coordination channel.
*   WhitePond is current coordinator - updates this doc as consensus forms.
