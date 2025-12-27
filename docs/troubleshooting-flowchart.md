# Troubleshooting Flowchart

Quick decision tree for diagnosing and resolving common Farmhand issues.

---

## Start Here: What's the Problem?

```
                    ┌─────────────────────────┐
                    │   What's happening?     │
                    └──────────┬──────────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Hook blocked │      │ Service down │      │ Command not  │
│ my edit      │      │ or failing   │      │ found        │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     ▼
   [Section A]           [Section B]           [Section C]
```

---

## Section A: Hook Blocked My Edit

### A1. "Agent not registered"

```
┌─────────────────────────────────────────────────────────────────┐
│ ERROR: "Agent not registered"                                   │
│ SYMPTOM: Edit/Write tool blocked                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Did you register     │
              │ with MCP Agent Mail? │
              └──────────┬───────────┘
                         │
         ┌───────────────┴───────────────┐
         │ NO                            │ YES
         ▼                               ▼
┌────────────────────┐       ┌────────────────────────┐
│ Run register_agent │       │ Check state file:      │
│ (copy-paste below) │       │ cat ~/.claude/         │
└────────┬───────────┘       │    agent-state.json    │
         │                   └───────────┬────────────┘
         ▼                               │
┌────────────────────┐       ┌───────────┴───────────┐
│ register_agent(    │       │ Is "registered":true? │
│   project_key=     │       └───────────┬───────────┘
│     "/home/ubuntu",│               │
│   program=         │       ┌───────┴───────┐
│     "claude-code", │       │ NO            │ YES
│   model="opus-4.5" │       ▼               ▼
│ )                  │  ┌─────────────┐  ┌─────────────────┐
└────────────────────┘  │ State lost. │  │ Project mismatch│
                        │ Re-register │  │ Check project_  │
                        │ or:         │  │ key matches     │
                        │ bd-cleanup  │  └─────────────────┘
                        │ --reset-    │
                        │ state       │
                        └─────────────┘
```

### A2. "File not reserved"

```
┌─────────────────────────────────────────────────────────────────┐
│ ERROR: "File not reserved"                                      │
│ SYMPTOM: Edit/Write tool blocked after registration             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Did you reserve the file │
              │ before editing?          │
              └────────────┬─────────────┘
                           │
           ┌───────────────┴───────────────┐
           │ NO                            │ YES
           ▼                               ▼
┌────────────────────────┐    ┌──────────────────────────────┐
│ Reserve it first:      │    │ Check pattern matching:      │
│                        │    │ • Did you use absolute path? │
│ file_reservation_paths(│    │ • Did glob pattern match?    │
│   project_key=         │    │ • Check expires_ts not past  │
│     "/home/ubuntu",    │    └──────────────┬───────────────┘
│   agent_name=          │                   │
│     "<your-name>",     │    ┌──────────────┴──────────────┐
│   paths=[              │    │ Check SQLite directly:      │
│     "/full/path/file"  │    │ sqlite3 ~/mcp_agent_mail/   │
│   ],                   │    │   storage.sqlite3           │
│   ttl_seconds=3600,    │    │ "SELECT * FROM file_        │
│   exclusive=True,      │    │  reservations WHERE         │
│   reason="issue-id"    │    │  released_ts IS NULL;"      │
│ )                      │    └─────────────────────────────┘
└────────────────────────┘
```

### A3. "File reserved by another agent"

```
┌─────────────────────────────────────────────────────────────────┐
│ ERROR: "File reserved by [OtherAgent]"                          │
│ SYMPTOM: Another agent has exclusive access                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Is the other agent       │
              │ actively working?        │
              └────────────┬─────────────┘
                           │
           ┌───────────────┼───────────────┐
           │ YES           │ UNKNOWN       │ NO (crashed)
           ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ Send message:    │ │ Check their  │ │ Check staleness: │
│                  │ │ last_active: │ │ bd-cleanup --list│
│ send_message(    │ │              │ │                  │
│   sender_name=   │ │ whois(agent) │ │ If stale (>4h):  │
│     "<you>",     │ │              │ │ bd-cleanup       │
│   to=["Agent"],  │ │ Check inbox  │ │   --force        │
│   subject=       │ │ for [CLOSED] │ │                  │
│     "File req",  │ │ messages     │ │ Or release all:  │
│   body_md=       │ └──────────────┘ │ bd-cleanup       │
│     "Need file"  │                  │   --release-all  │
│ )                │                  └──────────────────┘
│                  │
│ Wait for reply   │
│ or TTL expiry    │
└──────────────────┘
```

### A4. "TodoWrite blocked"

```
┌─────────────────────────────────────────────────────────────────┐
│ ERROR: "TodoWrite blocked"                                      │
│ SYMPTOM: Cannot use built-in todo tracking                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ This is intentional.     │
              │ Use bd (beads) instead:  │
              └────────────┬─────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ EQUIVALENT COMMANDS:                                            │
│                                                                 │
│ TodoWrite (blocked)          →   bd command                     │
│ ─────────────────────────────────────────────────               │
│ Create todo                  →   bd create --title="..."        │
│ Mark in_progress             →   bd update <id> --status=       │
│                                    in_progress                  │
│ Mark completed               →   bd close <id> --reason="..."   │
│ List todos                   →   bd ready                       │
│ Show all                     →   bd list                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section B: Service Down or Failing

### B1. MCP Agent Mail Issues

```
┌─────────────────────────────────────────────────────────────────┐
│ SYMPTOM: Agent Mail MCP calls failing                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ sudo systemctl status    │
              │ mcp-agent-mail           │
              └────────────┬─────────────┘
                           │
           ┌───────────────┼───────────────┐
           │ RUNNING       │ FAILED        │ NOT FOUND
           ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ Check logs:      │ │ Check error: │ │ Install service: │
│                  │ │              │ │                  │
│ journalctl -u    │ │ journalctl   │ │ cd ~/Farmhand    │
│ mcp-agent-mail   │ │ -u mcp-      │ │ ./install.sh     │
│ -f               │ │ agent-mail   │ │                  │
│                  │ │ -n 50        │ └──────────────────┘
│ Common issues:   │ │              │
│ • Port 8765 busy │ │ Then:        │
│ • Token mismatch │ │ sudo systemctl│
│ • DB locked      │ │ restart mcp- │
└──────────────────┘ │ agent-mail   │
                     └──────────────┘
```

### B2. Ollama Issues

```
┌─────────────────────────────────────────────────────────────────┐
│ SYMPTOM: qmd/embedding operations failing                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ sudo systemctl status    │
              │ ollama                   │
              └────────────┬─────────────┘
                           │
           ┌───────────────┼───────────────┐
           │ RUNNING       │ FAILED        │
           ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────────────────────────────┐
│ Check models:    │ │ Restart:                                 │
│                  │ │ sudo systemctl restart ollama            │
│ ollama list      │ │                                          │
│                  │ │ If still failing, check logs:            │
│ Missing models?  │ │ sudo journalctl -u ollama -n 50          │
│ Pull them:       │ │                                          │
│ ollama pull      │ │ Common issues:                           │
│   embeddinggemma │ │ • Out of disk space                      │
│   :latest        │ │ • GPU driver issues                      │
└──────────────────┘ │ • Memory exhaustion                      │
                     └──────────────────────────────────────────┘
```

### B3. Database Locked

```
┌─────────────────────────────────────────────────────────────────┐
│ SYMPTOM: "database is locked" errors                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Multiple agents or       │
              │ processes accessing DB?  │
              └────────────┬─────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Find processes with open handles:                            │
│    lsof ~/mcp_agent_mail/storage.sqlite3                        │
│                                                                 │
│ 2. Kill stuck processes (carefully):                            │
│    # Only if you're sure they're stuck                          │
│    kill <PID>                                                   │
│                                                                 │
│ 3. Restart MCP Agent Mail:                                      │
│    sudo systemctl restart mcp-agent-mail                        │
│                                                                 │
│ 4. Check WAL mode is enabled (improves concurrency):            │
│    sqlite3 ~/mcp_agent_mail/storage.sqlite3 "PRAGMA journal_mode;"│
│    # Should return "wal"                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Section C: Command Not Found

```
┌─────────────────────────────────────────────────────────────────┐
│ ERROR: "<command>: command not found"                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Which command?           │
              └────────────┬─────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌────────┐            ┌────────┐            ┌────────────┐
│ bd/bv  │            │ ubs    │            │ claude/    │
│        │            │        │            │ codex/gmi  │
└───┬────┘            └───┬────┘            └─────┬──────┘
    │                     │                       │
    ▼                     ▼                       ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│ Check PATH:     │ │ Install UBS:    │ │ Check installation: │
│ echo $PATH      │ │                 │ │                     │
│                 │ │ curl -sSL       │ │ which claude        │
│ Add if missing: │ │ https://raw.    │ │ which codex         │
│ export PATH=    │ │ githubusercontent│ │                     │
│ "/home/ubuntu/  │ │ .com/Dicks...   │ │ Re-authenticate:    │
│ .local/bin:     │ │ /ultimate_bug_  │ │ claude              │
│ $PATH"          │ │ scanner/main/   │ │ codex login         │
│                 │ │ install.sh      │ │   --device-auth     │
│ Re-install:     │ │ | bash          │ │ gemini              │
│ ./install.sh    │ └─────────────────┘ └─────────────────────┘
└─────────────────┘
```

---

## Section D: Multi-Agent Coordination

### D1. Agents Not Seeing Each Other's Messages

```
┌─────────────────────────────────────────────────────────────────┐
│ SYMPTOM: Messages not arriving in fetch_inbox()                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ Check contact approval:  │
              └────────────┬─────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Verify both agents are registered in SAME project:           │
│    sqlite3 ~/mcp_agent_mail/storage.sqlite3                     │
│    "SELECT name, project_id FROM agents;"                       │
│                                                                 │
│ 2. Check contact permissions:                                   │
│    list_contacts(project_key="...", agent_name="...")           │
│                                                                 │
│ 3. If not connected, request contact:                           │
│    macro_contact_handshake(                                     │
│      project_key="...",                                         │
│      requester="<you>",                                         │
│      target="<them>",                                           │
│      auto_accept=True                                           │
│    )                                                            │
└─────────────────────────────────────────────────────────────────┘
```

### D2. Reservation Conflicts

```
┌─────────────────────────────────────────────────────────────────┐
│ SYMPTOM: Two agents trying to reserve same files                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ This is working as       │
              │ intended! Options:       │
              └────────────┬─────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ WAIT            │ │ COORDINATE      │ │ WORK ELSEWHERE  │
│                 │ │                 │ │                 │
│ Check expiry:   │ │ Send message to │ │ Find different  │
│ TTL usually 1hr │ │ other agent:    │ │ files to work   │
│                 │ │ "I need X, can  │ │ on:             │
│ Monitor with:   │ │ you release?"   │ │ bd ready        │
│ bd-cleanup      │ │                 │ │ bv --robot-plan │
│ --list          │ └─────────────────┘ └─────────────────┘
└─────────────────┘
```

### D3. Shared State File Conflicts

```
┌─────────────────────────────────────────────────────────────────┐
│ SYMPTOM: "Your agent: X" but you registered as Y                │
│ CAUSE: Multiple agents overwriting ~/.claude/agent-state.json   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ SOLUTIONS:                                                      │
│                                                                 │
│ 1. Use AGENT_NAME environment variable (recommended):           │
│    export AGENT_NAME="MyUniqueAgent"                            │
│    claude                                                       │
│    # Uses ~/.claude/state-MyUniqueAgent.json instead            │
│                                                                 │
│ 2. Use NTM spawn (auto-sets AGENT_NAME per pane):               │
│    ntm spawn myproject --cc=2                                   │
│    # Each pane gets unique AGENT_NAME                           │
│                                                                 │
│ 3. Manual fix (temporary):                                      │
│    # Update state file to match your registration               │
│    cat > ~/.claude/agent-state.json << EOF                      │
│    {"registered": true, "agent_name": "<your-name>", ...}       │
│    EOF                                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: Recovery Commands

| Situation | Command |
|-----------|---------|
| Reset local state | `bd-cleanup --reset-state` |
| List orphaned items | `bd-cleanup --list` |
| Force release stale | `bd-cleanup --force` |
| Release ALL | `bd-cleanup --release-all` |
| Bypass hooks (emergency) | `export FARMHAND_SKIP_ENFORCEMENT=1` |
| Check service health | `./scripts/verify.sh` |
| Check beads health | `bd stats` |
| Check graph state | `bv --robot-priority` |
| Full reinstall | `./install.sh --force` |
| System diagnostic | `farmhand-doctor` |

---

## When All Else Fails

```
┌─────────────────────────────────────────────────────────────────┐
│ NUCLEAR OPTION: Complete Reset                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ # 1. Stop all services                                          │
│ sudo systemctl stop mcp-agent-mail ollama                       │
│                                                                 │
│ # 2. Clear all state (preserves beads database)                 │
│ bd-cleanup --reset-state                                        │
│ bd-cleanup --release-all                                        │
│                                                                 │
│ # 3. Restart services                                           │
│ sudo systemctl start mcp-agent-mail ollama                      │
│                                                                 │
│ # 4. Verify installation                                        │
│ ./scripts/verify.sh                                             │
│                                                                 │
│ # 5. Start fresh session                                        │
│ claude  # Will re-register automatically                        │
└─────────────────────────────────────────────────────────────────┘
```

---

See also: [troubleshooting.md](troubleshooting.md) for detailed command reference.
