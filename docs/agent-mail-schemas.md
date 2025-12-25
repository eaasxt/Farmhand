# Agent Mail Message Schemas

Structured JSON schemas for multi-agent coordination messages. Based on context-engineering research showing that unstructured natural language degrades as it passes between agents ("telephone game" problem).

## Why Structured Messages?

Research shows context quality degrades when:
- Information passes through multiple agents
- Natural language is paraphrased repeatedly
- Key details (file paths, IDs, status) get lost or corrupted

Structured JSON preserves:
- Exact identifiers (bead IDs, file paths)
- Numeric values (test counts, line numbers)
- Status enums (not fuzzy descriptions)

## Message Types

### CLAIMED

Sent when claiming a task. Preserves exact scope information.

```json
{
  "type": "CLAIMED",
  "bead_id": "lauderhill-123",
  "title": "Implement user authentication",
  "files": [
    "src/auth/**",
    "tests/auth/**"
  ],
  "approach": "Add JWT validation middleware with refresh token support",
  "dependencies": ["lauderhill-120", "lauderhill-121"],
  "estimated_scope": "medium",
  "timestamp": "2025-12-25T20:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | Always "CLAIMED" |
| bead_id | string | yes | Beads issue ID |
| title | string | yes | Task title |
| files | array | yes | File patterns being reserved |
| approach | string | no | Brief implementation approach |
| dependencies | array | no | Bead IDs this depends on |
| estimated_scope | enum | no | "small" / "medium" / "large" |
| timestamp | string | yes | ISO 8601 timestamp |

### CLOSED

Sent when completing a task. Preserves what was done.

```json
{
  "type": "CLOSED",
  "bead_id": "lauderhill-123",
  "title": "Implement user authentication",
  "summary": "Added JWT middleware with access/refresh tokens. 15-minute access, 7-day refresh.",
  "files_modified": [
    "src/auth/jwt.py",
    "src/auth/middleware.py",
    "src/auth/refresh.py"
  ],
  "files_created": [
    "tests/auth/test_jwt.py",
    "tests/auth/test_refresh.py"
  ],
  "tests": {
    "added": 12,
    "modified": 0,
    "passing": true
  },
  "commits": ["abc1234", "def5678"],
  "unblocks": ["lauderhill-124", "lauderhill-125"],
  "timestamp": "2025-12-25T22:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | Always "CLOSED" |
| bead_id | string | yes | Beads issue ID |
| title | string | yes | Task title |
| summary | string | yes | What was implemented |
| files_modified | array | yes | Files that were changed |
| files_created | array | no | New files created |
| tests | object | no | Test status (added, modified, passing) |
| commits | array | no | Commit hashes |
| unblocks | array | no | Bead IDs now unblocked |
| timestamp | string | yes | ISO 8601 timestamp |

### BLOCKED

Sent when stuck on a task after multiple attempts.

```json
{
  "type": "BLOCKED",
  "bead_id": "lauderhill-123",
  "title": "Implement user authentication",
  "blocker": {
    "type": "dependency",
    "description": "Waiting for database schema migration (lauderhill-120)",
    "bead_id": "lauderhill-120"
  },
  "attempts": 3,
  "last_error": "TypeError: 'NoneType' object is not subscriptable at auth/jwt.py:42",
  "files_touched": ["src/auth/jwt.py"],
  "needs": "Database connection or mock setup",
  "timestamp": "2025-12-25T21:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | Always "BLOCKED" |
| bead_id | string | yes | Beads issue ID |
| title | string | yes | Task title |
| blocker | object | yes | What's blocking (type, description) |
| attempts | number | yes | How many times tried |
| last_error | string | no | Last error message |
| files_touched | array | no | Files attempted to modify |
| needs | string | no | What would unblock |
| timestamp | string | yes | ISO 8601 timestamp |

Blocker types:
- `dependency` - Waiting on another bead
- `technical` - Code/architecture issue
- `external` - External service/API issue
- `unclear` - Requirements unclear

### HANDOFF

Sent when passing work to another agent or session.

```json
{
  "type": "HANDOFF",
  "bead_id": "lauderhill-123",
  "title": "Implement user authentication",
  "from_agent": "BlueLake",
  "to_agent": "GreenCastle",
  "status": "partial",
  "completed": [
    "JWT generation working",
    "Access token validation done"
  ],
  "remaining": [
    "Refresh token logic",
    "Token revocation"
  ],
  "context": {
    "key_files": ["src/auth/jwt.py", "src/auth/tokens.py"],
    "test_command": "pytest tests/auth/ -v",
    "notes": "Using PyJWT library, tokens stored in Redis"
  },
  "files_reserved": ["src/auth/**"],
  "timestamp": "2025-12-25T21:30:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | Always "HANDOFF" |
| bead_id | string | yes | Beads issue ID |
| title | string | yes | Task title |
| from_agent | string | yes | Handing off agent |
| to_agent | string | no | Receiving agent (or broadcast) |
| status | enum | yes | "partial" / "blocked" / "review" |
| completed | array | yes | What's done |
| remaining | array | yes | What's left |
| context | object | no | Key context for continuation |
| files_reserved | array | no | Files to transfer reservation |
| timestamp | string | yes | ISO 8601 timestamp |

### TRACK_COMPLETE

Sent when all beads in a track are done.

```json
{
  "type": "TRACK_COMPLETE",
  "track_name": "Authentication",
  "phase": 1,
  "beads_closed": [
    "lauderhill-120",
    "lauderhill-121",
    "lauderhill-123"
  ],
  "summary": "User auth fully implemented with JWT tokens and refresh logic",
  "unblocks_tracks": ["Frontend Auth UI"],
  "timestamp": "2025-12-25T23:00:00Z"
}
```

### PHASE_COMPLETE

Sent when all tracks in a phase are done.

```json
{
  "type": "PHASE_COMPLETE",
  "phase": 1,
  "phase_name": "Core Infrastructure",
  "tracks_completed": ["Authentication", "Database", "API Framework"],
  "beads_closed": 15,
  "next_phase": 2,
  "calibration_required": true,
  "timestamp": "2025-12-26T00:00:00Z"
}
```

## Usage in Skills

### Sending Structured Messages

```python
# In send_message(), use body_md with JSON code block
send_message(
    project_key="/home/ubuntu",
    sender_name="BlueLake",
    to=["GreenCastle"],
    subject="[CLAIMED] lauderhill-123 - User auth",
    body_md="""```json
{
  "type": "CLAIMED",
  "bead_id": "lauderhill-123",
  "title": "Implement user authentication",
  "files": ["src/auth/**"],
  "approach": "JWT with refresh tokens",
  "timestamp": "2025-12-25T20:00:00Z"
}
```""",
    thread_id="lauderhill-123"
)
```

### Parsing Structured Messages

When receiving messages, look for JSON code blocks:

```python
import json
import re

def parse_structured_message(body_md):
    """Extract structured JSON from message body."""
    # Find JSON code block
    match = re.search(r'```json\s*([\s\S]*?)\s*```', body_md)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None

# Use in inbox processing
for message in inbox:
    structured = parse_structured_message(message.body_md)
    if structured and structured.get("type") == "CLAIMED":
        # Handle claim announcement
        claimed_files = structured.get("files", [])
        # ...
```

## Subject Line Conventions

Subject lines should still follow the pattern for quick scanning:

| Type | Subject Pattern |
|------|-----------------|
| CLAIMED | `[CLAIMED] {bead_id} - {title}` |
| CLOSED | `[CLOSED] {bead_id} - {title}` |
| BLOCKED | `[BLOCKED] {agent} - {bead_id}` |
| HANDOFF | `[HANDOFF] {bead_id} - {title}` |
| TRACK_COMPLETE | `[TRACK COMPLETE] {track_name}` |
| PHASE_COMPLETE | `[PHASE COMPLETE] Phase {n}` |

The structured JSON in the body provides the detail; the subject provides quick triage.

## Backwards Compatibility

These schemas are conventions, not enforced. Agents should:

1. Always include structured JSON when sending coordination messages
2. Gracefully handle messages without JSON (fall back to parsing text)
3. Not break if unknown fields are present (forward compatibility)

## Benefits

1. **No degradation**: Exact values preserved through any number of forwards
2. **Machine-readable**: Agents can parse and act on messages programmatically
3. **Audit trail**: Structured data enables better session replay and debugging
4. **Consistency**: Same format across all agents and sessions

## See Also

- `multi-agent.md` - Multi-agent coordination rules
- `bead-workflow/` - Bead claiming and closing workflow
- `prime/` - Session startup with structured messages
