# Known Limitations

This document describes known edge cases, limitations, and design constraints in Farmhand. For solutions to common problems, see [troubleshooting.md](troubleshooting.md).

---

## Multi-Agent Coordination

### Race Conditions on Bead Claims

**Limitation:** Two agents can create beads for the same task simultaneously before either announces their claim.

**Example:**
```
Agent A: bd create --title="Fix version" → Farmhand-86a
Agent B: bd create --title="Fix version" → Farmhand-58c
```

**Workaround:**
- Always check `bd ready` before creating new beads
- Send `[CLAIMED]` announcement immediately after claiming
- Use the file reservation system as the source of truth (SQLite database query)
- Check agent inbox for recent `[CLAIMED]` messages before starting

**Status:** By design. The decentralized nature of beads prioritizes availability over strict consistency.

---

### File Reservation Granularity

**Limitation:** File reservations use glob patterns, not individual lines. Two agents cannot work on different parts of the same file simultaneously.

**Impact:**
- Large files become bottlenecks
- Refactoring that touches many files requires broad reservations
- Fine-grained parallel work within a single file is not supported

**Workaround:**
- Structure code into smaller, focused files
- Coordinate via Agent Mail before claiming large file sets
- Use shorter TTLs (30 minutes) for files you're only reading

**Status:** By design. Line-level locking would add significant complexity and merge conflict risks.

---

### Reservation TTL vs Actual Work Duration

**Limitation:** Agents cannot accurately predict how long a task will take. Reservations may expire mid-work or remain long after completion.

**Symptoms:**
- Expired reservation while editing → subsequent edits blocked
- Agent crashes → orphaned reservations until TTL expires

**Workaround:**
- Use generous TTLs for complex tasks (2-4 hours)
- Renew reservations with `renew_file_reservations()` if work takes longer
- Run `bd-cleanup --cron` via systemd timer for automatic orphan cleanup
- Release reservations immediately upon task completion

**Status:** By design. TTL prevents permanent deadlocks from crashed agents.

---

## Hook Enforcement

### No Dynamic Hook Reload

**Limitation:** Hook configuration in `~/.claude/settings.json` is read at session start. Changes require restarting Claude.

**Workaround:**
- Edit `settings.json` before starting a session
- Exit and restart Claude to apply changes
- Test hooks manually: `echo '{"tool_name":"Edit"}' | python ~/.claude/hooks/reservation-checker.py`

**Status:** Claude Code limitation.

---

### Hook Timeout Not Configurable

**Limitation:** Hooks have no configurable timeout. A hanging hook blocks all tool calls.

**Symptoms:**
- SQLite database locked → hook query hangs
- Network issue → MCP call hangs
- Agent appears frozen

**Workaround:**
- Monitor hook execution time
- Kill and restart Claude session if hung > 30 seconds
- Check SQLite database for locks: `fuser ~/mcp_agent_mail/storage.sqlite3`
- Future enhancement: Add timeout configuration to hooks

**Status:** Known gap. See [ENHANCEMENT_ROADMAP.md](ENHANCEMENT_ROADMAP.md) for planned improvements.

---

### Hook Bypass with FARMHAND_SKIP_ENFORCEMENT

**Limitation:** The `FARMHAND_SKIP_ENFORCEMENT=1` environment variable bypasses all hook enforcement, potentially allowing conflicts.

**Risk:**
- Agents editing the same file without coordination
- Lost work from merge conflicts
- State desynchronization

**Guidance:**
- Use only for debugging or single-agent work
- Never use in multi-agent sessions
- Unset immediately after emergency use

**Status:** Intentional escape hatch for advanced users.

---

### State File Conflicts (Multi-Agent)

**Limitation:** Without `AGENT_NAME` environment variable, all agents share `~/.claude/agent-state.json`, causing state corruption.

**Symptoms:**
- Agent sees wrong reservations
- Registration state lost between operations
- Inconsistent enforcement behavior
- Hook blocks operations despite valid database reservations

**Solution:**
- Always use NTM (`ntm spawn`) which sets `AGENT_NAME` automatically
- Or set manually: `export AGENT_NAME="MyAgent"` before starting Claude
- State files become `state-{AGENT_NAME}.json` instead of shared

**Status:** Resolved by design in NTM. Manual sessions require `AGENT_NAME`.

---

## Tool-Specific Limitations

### bv (Beads Viewer) TUI Hangs Agents

**Limitation:** Running `bv` without `--robot-*` flags opens an interactive TUI that blocks non-interactive agents.

**Symptoms:**
- Agent appears hung
- No output
- Session becomes unresponsive

**Solution:**
- Always use `--robot-*` flags: `bv --robot-priority`, `bv --robot-plan`, etc.
- Never run bare `bv` in automated agent sessions
- See `bv --robot-help` for available machine-readable commands

**Status:** By design. TUI intended for human operators.

---

### CASS Requires GLIBC 2.39+

**Limitation:** The `cass` binary requires Ubuntu 24.04 or later due to GLIBC version requirements.

**Symptoms (Ubuntu 22.04):**
```
./cass: /lib/x86_64-linux-gnu/libc.so.6: version `GLIBC_2.39' not found
```

**Workaround:**
- Upgrade to Ubuntu 24.04
- Build CASS from source on older systems
- Skip CASS installation on Ubuntu 22.04

**Status:** Upstream dependency. GLIBC backports not recommended.

---

### qmd Requires Ollama Running

**Limitation:** The `qmd` tool requires Ollama service for embeddings. Queries fail silently if Ollama is down.

**Symptoms:**
- No results from `qmd search` or `qmd query`
- No error message

**Workaround:**
- Check service: `sudo systemctl status ollama`
- Start if needed: `sudo systemctl start ollama`
- Verify models: `ollama list`

**Status:** Service dependency. Future enhancement: better error messages.

---

## Installation Limitations

### Idempotency Edge Cases

**Limitation:** While the installer is designed to be idempotent, some edge cases can cause issues:

- Partially downloaded binaries (corrupted)
- Changed upstream binary URLs
- Permission changes between runs

**Workaround:**
- Use `--force` flag to redownload binaries
- Check `scripts/install/*.sh` for hardcoded URLs if downloads fail
- Run `./scripts/verify.sh` after installation

**Status:** Mitigated by verification script.

---

### Hardcoded ubuntu User

**Limitation:** Many paths assume `/home/ubuntu` user. Non-ubuntu usernames require manual adjustments.

**Affected:**
- Service files (systemd)
- Hook paths
- Database locations

**Workaround:**
- Review and update paths in `config/` templates before installation
- Or create `ubuntu` user and run as that user
- Future enhancement: Use `$HOME` expansion consistently

**Status:** Known gap. See ENHANCEMENT_ROADMAP.md path normalization task.

---

## Database Limitations

### SQLite Concurrency

**Limitation:** MCP Agent Mail uses SQLite with WAL mode, but high concurrency (5+ simultaneous agents) may cause lock contention.

**Symptoms:**
- "database is locked" errors
- Slow reservation queries
- Hook timeouts

**Workaround:**
- Limit to 3-4 concurrent agents per project
- Increase SQLite timeout in hook code if needed
- Consider PostgreSQL migration for high-scale deployments (not currently supported)

**Status:** Acceptable for typical multi-agent use (2-4 agents).

---

### No Cross-Project Coordination

**Limitation:** Each project has its own MCP Agent Mail instance. Agents cannot coordinate across different projects.

**Impact:**
- No shared context between projects
- No cross-project file reservations
- Agent names may collide across projects

**Workaround:**
- Use unique agent names globally
- Document cross-project dependencies in project AGENTS.md files
- Consider monorepo structure for related projects

**Status:** By design. Project isolation is intentional.

---

## Git Integration

### bd sync Conflicts

**Limitation:** `bd sync` can fail if remote has diverged significantly from local beads state.

**Symptoms:**
- Merge conflicts in `.beads/issues.jsonl`
- Duplicate bead IDs
- Lost bead metadata

**Workaround:**
- Run `bd sync` frequently (before and after work sessions)
- Resolve conflicts manually if needed
- In extreme cases: `bd init --force` (loses local-only beads)

**Status:** Inherent to git-backed distributed systems.

---

## Performance Notes

### Large Beads Databases

**Limitation:** With 1000+ beads, `bd` and `bv` operations may slow down.

**Workaround:**
- Archive closed beads periodically (manual process)
- Use `bv --robot-*` filters to limit scope
- Consider database vacuuming: `sqlite3 ~/.beads/beads.db "VACUUM;"`

**Status:** Acceptable for typical use (< 500 active beads).

---

## Related Documentation

- [troubleshooting.md](troubleshooting.md) - Solutions to common problems
- [disaster-recovery.md](disaster-recovery.md) - Recovery procedures
- [ENHANCEMENT_ROADMAP.md](ENHANCEMENT_ROADMAP.md) - Planned improvements
- [hooks.md](hooks.md) - Hook system deep dive
