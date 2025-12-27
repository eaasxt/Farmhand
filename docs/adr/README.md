# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) documenting key design decisions made during Farmhand's development.

## What is an ADR?

An ADR is a document that captures an important architectural decision along with its context and consequences. ADRs help:

- New team members understand why things are built a certain way
- Future maintainers avoid repeating past debates
- Track the evolution of the system's design

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-0001](0001-hook-based-enforcement.md) | Hook-Based Enforcement Architecture | Accepted | 2025-12 |
| [ADR-0002](0002-sqlite-coordination-database.md) | SQLite as Coordination Database | Accepted | 2025-12 |
| [ADR-0003](0003-multi-agent-state-isolation.md) | Multi-Agent State Isolation | Accepted | 2025-12 |
| [ADR-0004](0004-fail-closed-vs-fail-open.md) | Fail-Closed vs Fail-Open Patterns | Accepted | 2025-12 |

## ADR Template

When adding a new ADR, use this template:

```markdown
# ADR-NNNN: Title

## Status

Proposed | Accepted | Deprecated | Superseded by [ADR-XXXX](./xxxx-title.md)

## Context

What is the issue that we're seeing that motivates this decision?

## Decision

What is the change we're proposing and/or doing?

## Consequences

What becomes easier or more difficult because of this change?
```

## Related Documents

- [docs/architecture.md](../architecture.md) - System architecture overview
- [docs/hooks.md](../hooks.md) - Hook system deep-dive
- [README.md](../../README.md) - Project overview
