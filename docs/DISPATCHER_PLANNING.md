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