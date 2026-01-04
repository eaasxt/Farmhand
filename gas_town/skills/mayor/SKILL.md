# Mayor — Central Coordinator & Work Orchestrator

Multi-agent coordination hub with natural language interface for Gas Town-style orchestration.

> **Role:** The Mayor serves as the central intelligence coordinating 20-30 agents via convoy creation, work dispatch, and system oversight. Think of the Mayor as the "town manager" who understands the full context and can make intelligent decisions about work distribution.

## When This Applies

| Signal | Action |
|--------|-----------|
| Starting multi-agent work session | Initialize as Mayor |
| "Create convoy for feature X" | Convoy creation and management |
| "What agents are working on what?" | Status overview and reporting |
| "Dispatch this work to available agents" | Work sling and assignment |
| Cross-project coordination needed | Mayor orchestration |
| Agent conflicts or blockers | Mayor intervention and resolution |
| Work priority decisions | Mayor intelligence and routing |

---

## Core Responsibilities

### 1. **Convoy Creation & Management**
Bundle related work into trackable units with dependency management:

```python
# Create convoy with related beads
convoy = create_convoy(
    name="user-authentication-system",
    description="Complete user auth implementation with backend, frontend, and tests",
    beads=["lauderhill-a1b2", "lauderhill-c3d4", "lauderhill-e5f6"],
    dependencies={"lauderhill-c3d4": ["lauderhill-a1b2"]},  # Frontend depends on backend
    priority="high",
    deadline="2024-01-15"
)
```

### 2. **Work Dispatch (Sling Mechanism)**
Intelligently assign work to appropriate agents based on capabilities and availability:

```python
# Sling work to best available agent
sling_result = dispatch_work(
    work_item="lauderhill-a1b2",
    preferred_agents=["RedBear", "BlueLake"],
    required_skills=["python", "fastapi", "database"],
    exclusive_reservation=True,
    timeout_hours=4
)
```

### 3. **Agent Status & Health Monitoring**
Track all agents in the system and their current state:

```python
# Get system overview
status = get_town_status()
# Returns: agent count, active convoys, blocked items, resource utilization
```

### 4. **Natural Language Coordination**
Process natural language requests and translate to system actions:

```python
# Example: "Create convoy for the billing feature with backend and frontend work"
# Mayor analyzes, identifies related beads, creates convoy, assigns agents
```

---

## Tool Reference

### Agent Mail Integration
| Tool | Purpose |
|------|---------|
| `ensure_project(human_key)` | Initialize project coordination |
| `register_agent(project_key, program, model)` | Register Mayor as coordinator |
| `fetch_active_agents(project_key)` | Discover available agents |
| `send_coordination_message(agents, subject, body, priority)` | Broadcast coordination |
| `create_convoy_announcement(convoy_name, members, work_items)` | Announce convoy formation |

### Beads Integration
| Tool | Purpose |
|------|---------|
| `bd ready --json` | Find available work for assignment |
| `bd show <id> --json` | Get detailed work item information |
| `bd update <id> --assignee <agent> --status in_progress` | Assign work to agent |
| `bd convoy create <name> <beads...>` | Bundle work into convoy |
| `bd convoy status <name>` | Track convoy progress |
| `bv --robot-plan` | Get orchestration recommendations |

### Hook System Integration
| Tool | Purpose |
|------|---------|
| `assign_to_hook(agent_name, work_item)` | Place work on agent's hook |
| `check_hook_status(agent_name)` | Verify hook state |
| `sling_work(work_item, target_agent, priority)` | Gas Town sling mechanism |

---

## Convoy System Architecture

```
Convoy "user-auth"
├── Planning Phase
│   ├── Backend Models (lauderhill-a1b2) → Agent: RedBear
│   └── API Design (lauderhill-c3d4) → Agent: BlueLake
├── Implementation Phase
│   ├── Database Schema → Depends on: Backend Models
│   ├── API Endpoints → Depends on: Backend Models, API Design
│   └── Frontend Components → Depends on: API Design
└── Integration Phase
    ├── End-to-End Tests → Depends on: All Implementation
    └── Documentation → Depends on: All Implementation
```

**Convoy Benefits:**
- **Visual Progress Tracking**: Real-time convoy status dashboard
- **Dependency Management**: Automatic work ordering and blocking
- **Resource Optimization**: Parallel execution where possible
- **Swarm Coordination**: Multiple agents attacking the same convoy

---

## Work Dispatch Intelligence

### Agent Capability Matching
```python
def select_optimal_agent(work_item, available_agents):
    """
    Intelligent agent selection based on:
    - Current workload and availability
    - Historical performance on similar tasks
    - Required skills and agent capabilities
    - Agent preferences and specializations
    - Resource requirements (file access, tools needed)
    """

    # Analyze work requirements
    requirements = analyze_work_requirements(work_item)

    # Score available agents
    scored_agents = []
    for agent in available_agents:
        score = calculate_agent_score(agent, requirements)
        scored_agents.append((agent, score))

    # Return best match
    return max(scored_agents, key=lambda x: x[1])
```

### Sling Mechanism
```python
def sling_work_to_hook(work_item, target_agent):
    """
    Gas Town sling: Place work directly on agent's hook

    1. Verify agent availability and hook capacity
    2. Reserve required files for the agent
    3. Create hook entry (special bead type)
    4. Send notification to agent
    5. Agent autonomously picks up work from hook on next activation
    """

    # Implement GUPP Protocol: "If hook has work, YOU MUST RUN IT"
    hook_entry = create_hook_assignment(
        agent_name=target_agent,
        work_item=work_item,
        priority=work_item.priority,
        deadline=work_item.deadline
    )

    # Agent will autonomously detect and execute
    return hook_entry
```

---

## Mayor Command Interface

### Convoy Management Commands
```bash
# Create new convoy
mayor convoy create "user-auth" --beads lauderhill-a1b2,lauderhill-c3d4 --description "User authentication system"

# Add work to existing convoy
mayor convoy add "user-auth" lauderhill-e5f6

# Get convoy status
mayor convoy status "user-auth"

# List all active convoys
mayor convoy list --status active
```

### Work Dispatch Commands
```bash
# Sling specific work to agent
mayor sling lauderhill-a1b2 --to RedBear --priority high

# Auto-assign based on agent capabilities
mayor assign lauderhill-a1b2 --auto

# Dispatch convoy to swarm
mayor dispatch-convoy "user-auth" --swarm-size 3
```

### Status & Monitoring Commands
```bash
# System overview
mayor status --detailed

# Agent activity
mayor agents --status --workload

# Convoy progress
mayor progress --convoy "user-auth" --visual

# Blocked items requiring intervention
mayor blocked --show-resolution-options
```

---

## Natural Language Processing

The Mayor processes natural language coordination requests:

**Example Interactions:**

*User:* "I need the user authentication feature implemented with backend API, frontend components, and tests"

*Mayor:* "I'll create a convoy for user authentication with 3 tracks: backend (API + database), frontend (components + auth flow), and testing (unit + integration). I found 4 related beads already in the system. Should I assign RedBear to backend work since they have recent FastAPI experience?"

*User:* "Yes, and assign BlueLake to frontend"

*Mayor:* "Done. Convoy 'user-auth' created with:
- Backend track: RedBear (2 beads, 4-6 hour estimate)
- Frontend track: BlueLake (2 beads, 3-4 hour estimate)
- Testing track: Will auto-assign when dependencies complete
- All agents notified and work slung to their hooks"

---

## Integration Patterns

### With Existing Farmhand Systems

**File Reservations:**
```python
# Mayor automatically handles file reservations for slung work
def sling_with_reservations(work_item, agent):
    file_patterns = analyze_required_files(work_item)

    reservation = file_reservation_paths(
        project_key=PROJECT_PATH,
        agent_name=agent,
        paths=file_patterns,
        reason=f"convoy-{convoy_name}-{work_item.id}",
        ttl_seconds=work_item.estimated_duration * 3600
    )

    sling_work_to_hook(work_item, agent)
    return reservation
```

**Safety Integration:**
- All work dispatch respects existing file reservation system
- GUPP automation only triggers after Mayor approval
- UBS scanning enforced before convoy completion
- Git safety hooks preserved for all agent operations

### With Enhanced MCP Agent Mail

**Convoy Messaging:**
```python
# Broadcast convoy formation to all participants
def announce_convoy_formation(convoy):
    send_message(
        project_key=PROJECT_PATH,
        sender_name="Mayor",
        to=convoy.assigned_agents,
        subject=f"[CONVOY FORMED] {convoy.name}",
        body_md=generate_convoy_announcement(convoy),
        thread_id=f"convoy-{convoy.id}",
        importance="high"
    )
```

---

## Phase A Implementation Focus

### Core Features (Phase A)
1. ✅ **Basic Mayor Role**: Central coordinator with project context
2. ✅ **Convoy Creation**: Bundle related work items
3. ✅ **Simple Dispatch**: Assign work to specific agents
4. ✅ **Status Monitoring**: Track agent activity and convoy progress
5. ✅ **Natural Language Interface**: Process coordination requests

### Integration Points
- **Beads**: Convoy creation and work assignment
- **MCP Agent Mail**: Agent discovery and coordination messaging
- **Hook System**: Work placement on agent hooks (when implemented in Phase A)
- **File Reservations**: Automatic reservation management for assigned work

### Success Criteria (Phase A)
- ✅ Mayor can create convoys with 3+ related beads
- ✅ Work can be slung to specific agents via hooks
- ✅ Convoy status provides real-time progress visibility
- ✅ Natural language requests correctly identify and bundle work
- ✅ Integration with existing Farmhand safety systems maintained

---

## Advanced Features (Future Phases)

### Phase B Enhancements
- **Seance Integration**: Access to predecessor Mayor sessions
- **Advanced Role Coordination**: Integration with Witness, Deacon, Refinery
- **Cross-Project Coordination**: Multi-repository convoy management

### Phase C Enhancements
- **AI-Powered Dispatch**: ML-driven agent selection and optimization
- **Predictive Resource Management**: Forecast convoy completion times
- **Swarm Orchestration**: Coordinate 20-30 agents simultaneously
- **Crash Recovery**: Resume Mayor state after system failures

---

## Error Handling & Resilience

### Common Scenarios
| Error | Mayor Response |
|-------|----------------|
| Agent unavailable for sling | Auto-reassign to next best agent |
| File reservation conflict | Coordinate with conflicting agent or delay |
| Convoy deadline at risk | Escalate priority, add resources, notify stakeholders |
| Agent stuck/crashed | Witness notification, work redistribution |

### Graceful Degradation
- Mayor unavailable → Individual agents continue with assigned work
- Hook system down → Fallback to direct MCP Agent Mail messaging
- Convoy system failure → Work items remain in beads system
- Natural language processing error → Fallback to manual command interface

---

## Quick Reference

### Essential Commands
```bash
mayor convoy create "feature-name" --beads id1,id2,id3
mayor sling <bead-id> --to <agent-name>
mayor status --convoys --agents
mayor assign <bead-id> --auto-select
```

### Integration
```python
# Python API for Mayor functions
from mayor import create_convoy, sling_work, get_town_status

convoy = create_convoy("user-auth", beads=["id1", "id2"])
sling_work("id1", target_agent="RedBear")
status = get_town_status()
```

---

## See Also

- `convoy/` — Convoy bundling and tracking system
- `hooks/` — Hook-based work distribution
- `witness/` — Agent health monitoring (Phase B)
- `refinery/` — Merge queue management (Phase B)
- `deacon/` — Daemon lifecycle coordination (Phase B)

The Mayor skill transforms chaotic multi-agent coordination into intelligent orchestration, enabling Gas Town's vision of 20-30 agents working in harmony toward shared goals.