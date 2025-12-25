# AGENTS.md

Project coordination file for multi-agent AI development.

> **This file lives in your project root.** Update it as agents join, leave, or change focus.

---

## Current Agents

| Agent Name | Program | Focus | Status |
|------------|---------|-------|--------|
| *None registered* | - | - | - |

<!-- Example:
| BlueLake | claude-code | Backend API | Active |
| GreenMountain | codex | Frontend UI | Active |
| RedStone | claude-code | Tests | Idle |
-->

---

## Active Work

### In Progress

<!-- Updated by agents when claiming beads -->

| Bead ID | Title | Agent | Started |
|---------|-------|-------|---------|
| *None* | - | - | - |

### Blocked

| Bead ID | Blocked By | Reason |
|---------|------------|--------|
| *None* | - | - |

---

## File Reservations

Current exclusive file reservations (auto-managed by Agent Mail):

```bash
# Check reservations:
bd-cleanup --list
```

---

## Project Conventions

### Branching

```
main              # Production-ready code
├── feature/*     # New features
├── fix/*         # Bug fixes
└── agent/*       # Agent work branches (optional)
```

### Commit Messages

```
[bead-id] Short description

- What was done
- Why it was done

Co-Authored-By: AgentName <noreply@anthropic.com>
```

### Code Style

<!-- Project-specific style notes -->
- Follow existing patterns in the codebase
- Run `ubs <files>` before committing

---

## Communication Protocol

### Message Subjects

| Subject Pattern | When |
|-----------------|------|
| `[CLAIMED] bd-XXX - Title` | After claiming a bead |
| `[CLOSED] bd-XXX - Title` | After closing a bead |
| `[BLOCKED] Agent - bd-XXX` | When stuck |
| `Agent Online` | When starting a session |

### Coordination Rules

1. **Check inbox** before starting work
2. **Announce claims** before editing files
3. **Reserve files** before editing
4. **Release reservations** when done
5. **Close beads** promptly after completing

---

## Tool Quick Reference

### Finding Work

```bash
bd ready                    # Available beads
bd ready --json             # Machine-readable
bv --robot-priority         # AI-recommended priorities
bv --robot-plan             # Execution order with parallel tracks
```

### Claiming Work

```bash
bd update <id> --status=in_progress --assignee=YourName
```

```python
file_reservation_paths(
    project_key="/path/to/project",
    agent_name="YourName",
    paths=["src/**"],
    ttl_seconds=3600,
    exclusive=True,
    reason="<bead-id>"
)
```

### Completing Work

```bash
ubs $(git diff --name-only)  # Security scan (MANDATORY)
git add -A && git commit     # Commit changes
bd close <id> --reason="..." # Close bead
```

```python
release_file_reservations(project_key="/path/to/project", agent_name="YourName")
```

### Communication

```python
# Send announcement
send_message(
    project_key="/path/to/project",
    sender_name="YourName",
    to=[],  # Empty = broadcast
    subject="[CLAIMED] bd-123 - Feature title",
    body_md="Starting work on...",
    thread_id="bd-123"
)

# Check inbox
fetch_inbox(project_key="/path/to/project", agent_name="YourName")
```

---

## Session Checklist

### Starting

- [ ] Read this file (AGENTS.md)
- [ ] Register with Agent Mail
- [ ] Check inbox for messages
- [ ] Run `bd ready` to find work
- [ ] Claim bead and reserve files
- [ ] Announce `[CLAIMED]`

### Ending

- [ ] Run `ubs` on changed files
- [ ] Commit and push changes
- [ ] Close completed beads
- [ ] Release file reservations
- [ ] Announce `[CLOSED]`
- [ ] Update this file if needed

---

## Project-Specific Notes

<!-- Add project-specific information here -->

### Architecture

<!-- Describe key architectural decisions -->

### Dependencies

<!-- Note any critical external dependencies -->

### Known Issues

<!-- Document known issues agents should be aware of -->

---

## History

| Date | Agent | Action |
|------|-------|--------|
| *Project created* | - | Initial setup |

<!-- Agents should log significant events here -->
