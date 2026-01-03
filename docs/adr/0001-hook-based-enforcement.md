# ADR-0001: Hook-Based Enforcement Architecture

## Status

Accepted

## Context

AI coding agents (Claude Code, Codex, Gemini) can perform powerful operations but don't naturally coordinate when multiple agents work on the same codebase. Without enforcement:

- Agents edit the same files simultaneously, causing merge conflicts
- Agents skip security scans because "the code looks fine"
- Agents use TodoWrite instead of project-specific issue trackers
- Agents run destructive git commands (reset --hard, clean -fd)

**The core problem:** AI agents will take the path of least resistance. Documentation and instructions are not sufficient - agents regularly ignore them under time pressure or when context windows fill up.

## Decision

We implement **enforcement through Claude Code's hook system** rather than relying on agent cooperation:

### Hook Types Used

1. **PreToolUse hooks** - Intercept and block operations BEFORE they execute:
   - `reservation-checker.py`: Blocks Edit/Write unless agent is registered AND file is reserved
   - `git_safety_guard.py`: Blocks destructive git commands
   - `todowrite-interceptor.py`: Blocks TodoWrite and suggests `bd` instead

2. **PostToolUse hooks** - Track state AFTER operations complete:
   - `mcp-state-tracker.py`: Records registrations, reservations, and file access

3. **SessionStart hooks** - Initialize clean state:
   - `session-init.py`: Clears stale state, detects orphaned reservations

### Key Design Principles

1. **Enforcement, not suggestion**: Hooks return `{"decision": "block"}` to prevent operations
2. **Fail-closed by default**: If database unavailable, block edits (safety over usability)
3. **Clear error messages**: Tell agents exactly what command to run to fix the issue
4. **Escape hatch available**: `FARMHAND_SKIP_ENFORCEMENT=1` for experienced users

## Consequences

### Benefits

- Agents **cannot** skip the workflow, even if they want to
- File conflicts are prevented at the source, not detected after the fact
- Security scanning (via UBS) becomes mandatory before commits
- New agents are forced to learn the correct workflow through error messages

### Drawbacks

- Hooks add latency to every tool call (~5-50ms per hook)
- Agents sharing a session without AGENT_NAME env var conflict on state files
- Database unavailability blocks all work (fail-closed)
- Escape hatch can be abused

### Trade-offs Accepted

- We accept the latency cost for the coordination guarantee
- We accept potential blocking on database issues for the safety guarantee
- We document the escape hatch but warn about its risks

## Related

- [ADR-0002](0002-sqlite-coordination-database.md): Why SQLite for coordination
- [ADR-0004](0004-fail-closed-vs-fail-open.md): Fail-closed vs fail-open decisions
- [docs/hooks.md](../hooks.md): Hook implementation details
