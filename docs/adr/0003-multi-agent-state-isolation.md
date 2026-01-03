# ADR-0003: Multi-Agent State Isolation

## Status

Accepted

## Context

When multiple AI agents run concurrently, each needs to track:
- Their own registration status
- Their own file reservations
- Their current issue/task ID
- Files they've created, modified, or read

Without isolation, agents overwrite each other's state, causing:
- Identity confusion (Agent A thinks it's Agent B)
- Reservation mismatches (hooks check wrong agent's reservations)
- Lost artifact trails (one agent's work attributed to another)

## Decision

We implement **per-agent state files** using the `AGENT_NAME` environment variable.

### Implementation

1. **With AGENT_NAME set** (multi-agent mode):
   - State file: `~/.claude/state-{AGENT_NAME}.json`
   - Example: `~/.claude/state-myproject__cc_1.json`
   - Each agent has isolated state

2. **Without AGENT_NAME** (single-agent mode):
   - State file: `~/.claude/agent-state.json`
   - Legacy behavior, shared by all agents in session

### NTM Integration

When using `ntm spawn`, each pane automatically gets `AGENT_NAME` set:
```bash
ntm spawn myproject --cc=2
# Creates panes with:
#   AGENT_NAME=myproject__cc_1
#   AGENT_NAME=myproject__cc_2
```

### State File Structure

```json
{
  "registered": true,
  "agent_name": "BlueLake",
  "reservations": [
    {
      "paths": ["src/**/*.py"],
      "reason": "farmhand-42",
      "created_at": 1735320000,
      "expires_at": 1735323600
    }
  ],
  "issue_id": "farmhand-42",
  "session_start": 1735319000,
  "files_created": ["src/new_file.py"],
  "files_modified": ["src/existing.py"],
  "files_read": ["README.md", "docs/arch.md"]
}
```

### Locking

State file operations use `fcntl` exclusive locks:
- Prevent race conditions during read-modify-write
- 5-second timeout (fail-open if exceeded)
- Stale lock detection (1-hour cleanup)

## Consequences

### Benefits

- Agents can work in parallel without state corruption
- Each agent maintains accurate reservation records
- Artifact trails (files touched) are per-agent
- Crash recovery is per-agent (only affected agent's state is stale)

### Drawbacks

- Requires AGENT_NAME to be set for proper isolation
- State files accumulate (mitigated by session-init cleanup of files >7 days old)
- Manual setup required outside of NTM

### Known Limitation

When multiple agents share a session **without** AGENT_NAME:
- They share `~/.claude/agent-state.json`
- Last agent to make MCP call "owns" the state
- This causes hook enforcement failures

**Recommendation:** Always use `ntm spawn` for multi-agent work, or manually set `AGENT_NAME`.

## Related

- [ADR-0001](0001-hook-based-enforcement.md): How hooks use state for enforcement
- [docs/troubleshooting.md](../troubleshooting.md): Debugging state conflicts
