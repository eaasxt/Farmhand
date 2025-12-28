# Dispatcher Planning Document

**Status:** PLANNING
**Created:** 2025-12-27
**Thread:** `dispatcher-planning`

---

## Vision

An **Automated Work Dispatcher** that reduces agent idle time through push-based task assignment. Instead of agents polling `bd ready`, the dispatcher monitors the beads graph and proactively assigns work to available agents.

---

## Problem Statement

### Current State
1. Agents poll `bd ready` to find work
2. Multiple agents may race for the same bead
3. Idle agents don't know when new work becomes unblocked
4. No central coordination of parallel execution tracks

### Desired State
1. Dispatcher monitors beads graph for unblocked work
2. Dispatcher knows which agents are idle/active
3. Dispatcher assigns work to available agents (push model)
4. Parallel tracks are identified and assigned to maximize throughput

---

## Core Concepts

### Agent States
```
IDLE        - Registered, no active bead, ready for work
WORKING     - Has claimed bead, actively executing
BLOCKED     - Waiting on dependency or resource
OFFLINE     - No heartbeat in last N minutes
```

### Dispatcher Responsibilities
1. **Graph Monitoring** - Watch beads for state changes (blocked -> ready)
2. **Agent Tracking** - Maintain registry of agent states via heartbeats
3. **Work Assignment** - Match ready beads to idle agents
4. **Parallel Planning** - Identify independent tracks for parallel execution
5. **Load Balancing** - Distribute work evenly across agents

---

## Architecture Options

### Option A: Centralized Dispatcher Service

```
+-------------+     +---------------------+     +-------------+
|   Agent 1   |---->|    Dispatcher       |<----|   Agent 2   |
|  (claude)   |<----|    (new service)    |---->|  (claude)   |
+-------------+     +---------------------+     +-------------+
                             |
                    +--------+--------+
                    |                 |
              +-----v-----+    +------v------+
              |  Beads DB |    |  Agent Mail |
              +-----------+    +-------------+
```

**Pros:**
- Single source of truth for assignments
- Can optimize globally across all agents
- Clear coordination point

**Cons:**
- New service to maintain
- Single point of failure
- Adds complexity

### Option B: Agent Mail + Polling Enhancement

```
+-------------+     +---------------------+     +-------------+
|   Agent 1   |---->|    Agent Mail       |<----|   Agent 2   |
|  (claude)   |<----|    (existing)       |---->|  (claude)   |
+-------------+     +---------------------+     +-------------+
                             |
                    +--------+--------+
                    |                 |
              +-----v-----+    +------v------+
              |  Beads DB |    | Dispatcher  |
              |           |    |   (cron)    |
              +-----------+    +-------------+
```

**Pros:**
- Uses existing Agent Mail infrastructure
- Dispatcher is stateless cron job
- Simpler implementation

**Cons:**
- Polling-based, not true push
- Latency between unblock and assignment

### Option C: Hook-Based Reactive Assignment

```
+-------------+                              +-------------+
|   Agent 1   |--[closes bead]-------------->|   Agent 2   |
|  (claude)   |<-[assigned next]-------------|  (claude)   |
+-------------+                              +-------------+
        |                                           |
        +-------[PostToolUse hook]------------------+
                           |
                    +------v------+
                    | Assignment  |
                    |   Logic     |
                    +-------------+
```

**Pros:**
- Zero latency - assignment happens on bead close
- No new service
- Fully reactive

**Cons:**
- Complex hook logic
- Assignment logic runs in hook context (timeout risk)

---

## Recommended Approach: Hybrid (B + C)

1. **PostToolUse hook** on `bd close` triggers immediate assignment attempt
2. **Cron job** (every 1 min) catches any missed assignments
3. **Agent Mail** for notifications ("You have been assigned Farmhand-xyz")

### Implementation Phases

#### Phase 1: Idle Agent Registry
- Agents send heartbeat to Agent Mail on startup
- Agents mark themselves idle when finishing work
- Query: "Which agents are idle?"

#### Phase 2: Assignment Notifications
- When bead becomes ready, find idle agent
- Send high-priority Agent Mail: "[ASSIGNED] Farmhand-xyz"
- Agent checks inbox, claims bead

#### Phase 3: Automatic Claiming
- If agent has auto-accept enabled, dispatcher claims on their behalf
- Reduces race conditions
- Agent just starts working when it sees assignment

#### Phase 4: Parallel Track Optimization
- Use `bv --robot-plan` to identify parallel tracks
- Assign entire tracks to agents (not individual beads)
- Reduces context switching

---

## Technical Design Specification

### 1. Data Model Updates

We leverage `mcp_agent_mail/storage.sqlite3` as the source of truth for agent state.

**Table: `agents` (existing)**
- `id`, `name`, `program`, `model`
- `last_active_ts`: Updated on any tool call. Used for heartbeat.

**New Table: `agent_status` (proposed)**
- `agent_id`: FK to agents
- `status`: ENUM('IDLE', 'WORKING', 'BLOCKED', 'OFFLINE')
- `current_bead_id`: FK to beads (if known) or string
- `updated_at`: Timestamp

### 2. The Dispatcher Script (`bin/farmhand-dispatcher`)

A Python script runnable as a oneshot (cron) or daemon.

**Algorithm:**

1.  **Reconcile States:**
    - Query `beads` for all `in_progress` tasks.
    - Update `agent_status` to 'WORKING' for agents assigned to those tasks.
    - Set agents with `last_active_ts` > 10m ago to 'OFFLINE'.
    - Set remaining agents to 'IDLE'.

2.  **Fetch Demand:**
    - Run `bd ready --json` (or query DB) to get list of open, unblocked beads.
    - Sort by Priority (P0 > P1) then Age.

3.  **Fetch Supply:**
    - Query `agent_status` for 'IDLE' agents.

4.  **Match:**
    - **Simple Matching:** Assign top priority bead to first available idle agent.
    - **Affinity Matching (Future):** Check `cass` or `mcp` history. Did this agent touch the relevant files recently?

5.  **Dispatch:**
    - Send Agent Mail message:
      - **Subject:** `[DISPATCH] Assigned: Farmhand-123`
      - **Body:**
        ```json
        {
          "type": "DISPATCH_ORDER",
          "bead_id": "Farmhand-123",
          "title": "Fix login bug",
          "priority": "P1"
        }
        ```
    - (Optional) If Auto-Claim enabled: Run `bd update ...` on behalf of agent.

### 3. Agent Integration

Agents need to know when to check for work.

**Hook Integration (`mcp-state-tracker.py`):**
- When `bd close` is detected:
  - Mark agent status as 'IDLE'.
  - Trigger `farmhand-dispatcher --quick` (Hook-Based Reactivity).

**Polling:**
- Agents should poll `fetch_inbox` periodically.
- When a `DISPATCH_ORDER` message is received, the agent loop should prioritize it.

---

## Answered Questions

1. **How do agents signal "idle"?**
   - **Answer:** Implicitly via `bd close`. When an agent closes a bead and has no other `in_progress` beads, it is effectively IDLE. We can also add a specific `set_agent_status` tool for explicit signaling.

2. **What if assigned agent doesn't respond?**
   - **Answer:** The Dispatcher tracks "Pending Assignments". If the bead remains `open` (not `in_progress`) for > 5 minutes after dispatch, the Dispatcher re-queues it and marks that agent as 'UNRESPONSIVE' (temp offline).

3. **How to handle agent preferences?**
   - **Answer:** Use the `task_description` field in `register_agent`. "I am working on SQL optimization". Dispatcher matches keywords in bead title to task description.

4. **How does this interact with existing `bd update --status=in_progress`?**
   - **Answer:** The Dispatcher sends the *order*. The Agent performs the *action* (`bd update`). This maintains the audit trail that the Agent is the one doing the work.

5. **Multi-project coordination?**
   - **Answer:** Scoped to single project for v1. Each project runs its own Dispatcher instance (systemd timer).

---

## Related Work

- **Agent Mail** - Already has message routing infrastructure
- **Beads (bd)** - Already has graph analysis (`bv --robot-plan`)
- **NTM** - Already spawns multiple agents with AGENT_NAME
- **/execute skill** - K&V has execution orchestration concept

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time from bead-ready to claim | Manual (minutes) | < 30 seconds |
| Agent idle time | Unknown | < 10% of session |
| Duplicate claims (races) | Occasional | Zero |
| Parallel track utilization | Manual | Automatic |

---

## Next Steps

1. [ ] Create `agent_status` table in MCP database (or equivalent JSON state file)
2. [ ] Implement `bin/farmhand-dispatcher` prototype (Python)
3. [ ] Add systemd timer `farmhand-dispatcher.timer` (1 min interval)
4. [ ] Update `mcp-state-tracker` hook to trigger dispatcher on bead close

---

## Discussion Thread

Use Agent Mail thread `dispatcher-planning` for coordination.
---

## Agent Reviews

### FuchsiaCastle Review (2025-12-28)

**Overall Assessment:** The plan is well-structured and the hybrid approach (B+C) is pragmatic. However, several integration concerns need resolution before implementation.

#### Functionality Analysis

**Strengths:**
1. ✅ Solves the core problem: reduces agent idle time through push-based assignment
2. ✅ Leverages existing infrastructure (Agent Mail, beads graph)
3. ✅ Phased approach allows incremental rollout and easy rollback
4. ✅ Clear success metrics with measurable targets

**Gaps Identified:**

| Gap | Risk | Mitigation |
|-----|------|------------|
| No agent capability matching | Medium | Add optional `specializations` field to agent profile |
| No assignment priority when multiple idle | Low | Use agent inception_ts (oldest first) or round-robin |
| No rollback for bad assignments | Medium | Add `[UNASSIGN]` message type for dispatcher to retract |
| Track optimization (Phase 4) scope creep | High | Defer entirely to v2; keep v1 simple |

#### Interoperability Analysis

**Critical Issue: State File Race Conditions**

The plan assumes agents can reliably report their state. However, in production multi-agent scenarios, I observed (Farmhand-d2t session):

```
Agent A registers as "FuchsiaCastle" → writes state file
Agent B registers as "RedDog" → overwrites state file  
Agent A tries to edit → hook thinks it's "RedDog" → BLOCKED
```

**Prerequisite:** The AGENT_NAME enforcement (Farmhand-3ry, now merged) must be widely adopted before dispatcher can trust agent identity. Without per-agent state files (`state-{AGENT_NAME}.json`), idle detection will be unreliable.

**Integration Points:**

| Component | Current State | Required Change | Risk |
|-----------|---------------|-----------------|------|
| `agents` table | Has `last_active_ts` | Can use as-is for OFFLINE detection | None |
| `agent_status` table | **Proposed new** | Schema migration needed | Medium |
| `mcp-state-tracker.py` | Watches MCP tools only | Must also detect `bd close` (Bash) | High |
| Agent Mail schemas | Has CLAIMED/CLOSED/etc | Add DISPATCH type | Low |
| `bv --robot-plan` | External binary | Not always installed | Medium |

**Recommendation:** Avoid new `agent_status` table. Instead derive state:
- IDLE = registered agent with no `in_progress` beads in `bd list --json`
- WORKING = has `in_progress` bead (join against beads.db)
- OFFLINE = `last_active_ts` > 30 minutes ago

This keeps the dispatcher stateless and avoids schema migration.

**Message Schema Addition:**

Following existing patterns in `agent-mail-schemas.md`:

```json
{
  "type": "DISPATCH",
  "bead_id": "Farmhand-123",
  "title": "Fix authentication bug",
  "priority": "P1",
  "reason": "Highest priority unblocked task",
  "auto_claim": false,
  "expires_ts": "2025-12-28T03:00:00Z",
  "timestamp": "2025-12-28T02:30:00Z"
}
```

#### Implementation Path Analysis

**Phase 1 Concerns:**
- "Agents send heartbeat to Agent Mail on startup" - **Undefined mechanism**. Suggest using `register_agent()` call itself as implicit heartbeat (already updates `last_active_ts`).

**Phase 2 → 3 Transition Risk:**
Going from "agent claims after receiving notification" to "dispatcher claims on agent's behalf" is a significant shift. Recommend intermediate step:

- Phase 2a: Dispatcher notifies, agent claims manually
- Phase 2b: Agent can set `auto_claim: true` preference  
- Phase 3: Dispatcher respects preference and claims for opted-in agents

**Hook Trigger Concern:**
The plan says: "PostToolUse hook on `bd close` triggers immediate assignment attempt."

Issues:
1. `bd close` is a Bash command, not an MCP tool. `mcp-state-tracker.py` doesn't see it.
2. Running `farmhand-dispatcher --quick` from a hook adds latency (hooks already have timeout issues per Farmhand-ktf)
3. Hook failures should not break `bd close`

**Alternative:** Use inotify/watchdog on beads.db for reactive triggers, or accept 1-min cron latency as acceptable for v1.

#### Feature Set Evaluation

| Feature | V1 Necessity | Recommendation |
|---------|--------------|----------------|
| Idle agent detection | Essential | ✅ Include |
| Push notifications via Agent Mail | Essential | ✅ Include |
| Priority-based assignment | Essential | ✅ Include |
| Affinity matching (file history) | Nice-to-have | ❌ Defer to v2 |
| Parallel track optimization | Complex | ❌ Defer to v2 |
| Auto-claim on behalf | Complex | ⚠️ Phase 3, opt-in only |

**Minimum Viable Dispatcher (Proposed V1):**

```python
#!/usr/bin/env python3
# bin/farmhand-dispatcher (simplified concept)
import json
import subprocess

def main():
    # 1. Get unblocked beads
    ready = subprocess.run(['bd', 'ready', '--json'], capture_output=True)
    beads = json.loads(ready.stdout)
    
    # 2. Get idle agents (registered, no in_progress beads)
    # Query MCP Agent Mail for agents with last_active_ts < 30min
    # Cross-reference with bd list --status=in_progress
    idle_agents = get_idle_agents()
    
    # 3. Match (simple: first idle gets highest priority)
    for bead in sorted(beads, key=lambda b: b['priority']):
        if idle_agents:
            agent = idle_agents.pop(0)
            send_dispatch_message(agent, bead)
```

#### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Dispatcher crashes mid-assignment | Low | Medium | Cron re-runs; agent ignores stale dispatches |
| Agent ignores dispatch message | Medium | Low | Dispatcher tracks pending, re-queues after 5min |
| Race between dispatcher and manual `bd update` | Medium | Medium | Use `bd update --if-status=open` atomic claim |
| State file race (multi-agent) | High | High | **Enforce AGENT_NAME requirement** |

#### Concrete Next Steps (Priority Order)

1. **[PREREQUISITE]** Document AGENT_NAME requirement in CLAUDE.md session start checklist
2. **[PHASE 1]** Implement `bin/farmhand-dispatcher` as stateless Python script
3. **[PHASE 1]** Add `farmhand-dispatcher.timer` (1 min) without hook integration
4. **[PHASE 1]** Add DISPATCH schema to `agent-mail-schemas.md`
5. **[PHASE 2]** Agent skill to check inbox for DISPATCH messages on loop
6. **[DEFER]** Hook integration, auto-claim, parallel tracks → v2

#### Questions for Other Agents

1. Should dispatcher run per-project or globally? (Plan says per-project - I agree)
2. How should agent "specializations" be represented? (Free text vs. enum)
3. What's the maximum acceptable latency from bead-ready to dispatch? (Plan says <30s - achievable with cron?)
4. Should expired DISPATCH messages be auto-cleaned from inbox?

---

**End FuchsiaCastle Review**
