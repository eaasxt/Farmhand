# ADR-0002: SQLite as Coordination Database

## Status

Accepted

## Context

Multi-agent coordination requires a shared database to track:
- Which agents are active
- Which files are reserved by which agents
- Messages between agents
- Reservation expiry and TTLs

Options considered:
1. **PostgreSQL/MySQL**: Full RDBMS with network access
2. **Redis**: In-memory key-value store
3. **SQLite**: Embedded database with file-based storage
4. **Plain files**: JSON/YAML files with file locking

## Decision

We use **SQLite** as the coordination database for MCP Agent Mail.

### Implementation Details

- **Location**: `~/mcp_agent_mail/storage.sqlite3`
- **WAL mode**: Enabled for concurrent read access
- **Busy timeout**: 30 seconds to handle lock contention
- **Retry logic**: Exponential backoff (3 retries) on database locked errors

### Key Tables

```sql
-- Core coordination tables
projects(id, human_key, slug, created_ts)
agents(id, project_id, name, program, model, last_active_ts)
file_reservations(id, project_id, agent_id, path_pattern, exclusive, expires_ts, released_ts)
messages(id, project_id, sender_id, thread_id, subject, body_md, created_ts)
```

## Consequences

### Benefits

- **Zero configuration**: No separate database server to install/maintain
- **Single file backup**: `cp storage.sqlite3 backup.sqlite3`
- **ACID guarantees**: Full transaction support
- **Portable**: Works on any Ubuntu install
- **Fast for small scale**: Sub-millisecond queries for <1000 records

### Drawbacks

- **Single-machine only**: Cannot share SQLite across network (without workarounds)
- **Write contention**: Only one writer at a time (WAL helps but doesn't eliminate)
- **Scaling limit**: Performance degrades beyond ~10-15 concurrent agents
- **No real-time notifications**: Must poll for changes

### Scaling Path (Future)

If scaling beyond single-machine becomes necessary:
1. Abstract database layer in MCP Agent Mail
2. Add PostgreSQL connection option
3. Use connection pooling (pgbouncer)
4. This is documented in `docs/IMPLEMENTATION_PLAN.md` Phase 4

### Why Not Alternatives?

| Option | Rejected Because |
|--------|------------------|
| PostgreSQL | Requires server installation, overkill for 2-4 agents |
| Redis | No persistence by default, complex data modeling |
| Plain files | No ACID, race conditions on concurrent access |

## Related

- [ADR-0001](0001-hook-based-enforcement.md): How hooks query this database
- [ADR-0004](0004-fail-closed-vs-fail-open.md): Database unavailability handling
