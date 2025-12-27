# ADR-0004: Fail-Closed vs Fail-Open Patterns

## Status

Accepted

## Context

Hooks can fail for various reasons:
- Database unavailable or locked
- JSON parsing errors in input
- Lock acquisition timeouts
- Network issues with MCP server

We must decide: when a hook fails, should it **block** the operation (fail-closed) or **allow** it (fail-open)?

## Decision

We use a **hybrid approach** based on the type of failure and its safety implications.

### Fail-Closed (Block on Failure)

Used when safety is paramount:

| Hook | Failure Scenario | Behavior |
|------|------------------|----------|
| `reservation-checker.py` | Database unavailable | Block edit |
| `reservation-checker.py` | Cannot determine agent identity | Block edit |
| `git_safety_guard.py` | Database error during check | Block (default safe) |

**Rationale:** If we can't verify the agent has the right to edit a file, blocking prevents potential merge conflicts.

### Fail-Open (Allow on Failure)

Used when usability outweighs risk:

| Hook | Failure Scenario | Behavior |
|------|------------------|----------|
| `git_safety_guard.py` | Malformed JSON input | Allow command |
| `mcp-state-tracker.py` | Lock timeout | Proceed without lock |
| `todowrite-interceptor.py` | Any internal error | Block (but log error) |
| All hooks | Hook script crashes | Claude Code allows by default |

**Rationale:** A JSON parsing error in git_safety_guard shouldn't prevent legitimate git commands.

### Decision Matrix

```
                    High Safety Impact    Low Safety Impact
                    ------------------------------------------
Temporary Failure   | Fail-closed         | Fail-open
Permanent Failure   | Fail-closed         | Fail-open + alert
```

## Implementation Details

### Reservation Checker (Fail-Closed)

```python
try:
    db = get_db_connection()
    reservations = check_reservations(db, file_path, agent_name)
except Exception as e:
    # Cannot verify - block for safety
    return {"decision": "block", "reason": f"Database error: {e}"}
```

### Git Safety Guard (Fail-Open for Parsing)

```python
try:
    tool_input = json.loads(sys.stdin.read())
    command = tool_input.get("tool_input", {}).get("command", "")
except json.JSONDecodeError:
    # Can't parse - allow (don't block legitimate commands)
    sys.exit(0)
```

### State Tracker (Fail-Open for Locks)

```python
try:
    with file_lock(state_path, timeout=5):
        update_state(state_path, new_data)
except LockTimeout:
    # Can't lock - proceed without (usability > perfect state)
    update_state_unsafe(state_path, new_data)
```

## Consequences

### Benefits

- **Safety-critical paths are protected**: File edits require verified reservations
- **Usability preserved**: Minor failures don't block work
- **Explicit decisions**: Each failure mode is consciously chosen
- **Recovery-friendly**: Fail-closed prevents cascading damage

### Drawbacks

- **Complexity**: Different hooks behave differently
- **User confusion**: "Why did X work but Y failed?"
- **Potential gaps**: New failure modes need conscious classification

### Monitoring Recommendations

1. Log all fail-open events for audit
2. Alert on repeated database failures
3. Track hook execution times to detect degradation

## Related

- [ADR-0001](0001-hook-based-enforcement.md): Hook architecture overview
- [ADR-0002](0002-sqlite-coordination-database.md): Database failure scenarios
- [docs/troubleshooting.md](../troubleshooting.md): Debugging hook failures
