# Gas Town Blog Post - Component Breakdown

## Executive Summary
Steve Yegge's Gas Town blog post describes a comprehensive multi-agent orchestration system built on 4 core layers. This document breaks down every component for validation against our implementation.

---

## 1. CORE INFRASTRUCTURE COMPONENTS

### 1.1 Worker Roles (7 + Overseer)
| Role | Description | Scope | Core Function |
|------|-------------|-------|---------------|
| **👤 Overseer** | Human operator with system identity | Town-level | Strategic direction, high-level coordination |
| **🎩 Mayor** | Chief-of-staff, concierge agent | Town-level | Primary human interface, convoy orchestration |
| **😺 Polecats** | Ephemeral swarm workers | Per-rig | Code implementation, feature delivery via MRs |
| **🏭 Refinery** | Merge queue manager | Per-rig | Intelligent conflict resolution, sequential merging |
| **🦉 Witness** | Patrol supervisor | Per-rig | Monitors polecats, prevents stuck states |
| **🐺 Deacon** | Daemon coordinator | Town-level | Heartbeat system, DYFJ propagation |
| **🐶 Dogs** | Deacon's crew | Town-level | Maintenance, handyman work, plugin execution |
| **👷 Crew** | Named persistent workers | Per-rig | Design work, long-term identity, direct human collaboration |

### 1.2 Organizational Structure
- **🏙️ Town**: Central HQ (e.g., ~/gt), manages all rigs
- **🏗️ Rigs**: Individual projects/repos under Gas Town management
- **Two-tier architecture**: Town-level + Rig-level operations

---

## 2. MEOW STACK (Molecular Expression of Work)

### 2.1 Core Work Units (Bottom to Top)
| Component | Description | Persistence | Usage |
|-----------|-------------|-------------|--------|
| **Beads** | Atomic work units (issues) | Git JSONL | Basic work tracking, identities |
| **Epics** | Beads with children | Git JSONL | Top-down planning, hierarchical structure |
| **Molecules** | Workflow chains | Git JSONL | Sequential execution, TODO lists |
| **Protomolecules** | Workflow templates | Git JSONL | Reusable workflow patterns |
| **Formulas** | TOML workflow source | Git JSONL | High-level workflow definition |
| **Wisps** | Ephemeral orchestration beads | Memory only | High-velocity operations, auto-burned |

### 2.2 Workflow Composition
- **Formulas** → "cooked" into → **Protomolecules** → instantiated into → **Molecules/Wisps**
- **Variable substitution** during instantiation
- **Macro expansion** for loops and gates
- **Mol Mall**: Planned marketplace for formulas

---

## 3. CORE MECHANISMS

### 3.1 GUPP (Gas Town Universal Propulsion Principle)
- **Principle**: "If there is work on your hook, YOU MUST RUN IT"
- **Persistent Identities**: Agents as beads, not sessions
- **Hooks**: Per-agent pinned beads for work assignment
- **Physics over Politeness**: Agents told to work without waiting for input

### 3.2 The GUPP Nudge System
- **Problem**: Claude Code too polite, waits for human input
- **Solution**: `gt nudge` command sends tmux notifications
- **Timing**: 30-60 seconds after startup, max 5 minutes
- **Debounce**: Handles tmux send-keys issues

### 3.3 Work Assignment (Sling Mechanism)
- **`gt sling`**: Core primitive for work distribution
- **Hook Assignment**: Work placed on agent's personal hook
- **Immediate/Deferred**: Can start immediately or queue
- **Cross-agent**: Any agent can sling work to any other

### 3.4 Nondeterministic Idempotence (NDI)
- **Principle**: Nondeterministic path, deterministic outcome
- **Durability**: All work persists in Git-backed beads
- **Recovery**: Agents resume work after crashes/restarts
- **Comparison**: Similar to Temporal but different implementation

---

## 4. MESSAGING & COORDINATION SYSTEMS

### 4.1 Mail System
- **Agent Inboxes**: All beads-based messaging
- **Cross-rig Routing**: Beads handles rig-appropriate routing
- **Event System**: All orchestration events via beads
- **Persistence**: All mail persisted in Git

### 4.2 Seance System (`gt seance`)
- **Purpose**: Current agent talks to predecessor
- **Mechanism**: Uses Claude Code `/resume` feature
- **Session Titles**: Include role, PID, session_id
- **Use Case**: Handoff continuity, "where's my stuff?"

### 4.3 Handoff Protocol (`gt handoff` / `/handoff`)
- **Core Workflow**: Most fundamental Gas Town operation
- **Session Management**: Graceful cleanup and restart
- **Work Continuity**: Ensures work survives session changes
- **GUPP Integration**: Auto-restart via hook mechanism

---

## 5. OPERATIONAL SYSTEMS

### 5.1 Convoys (Work Order System)
- **Definition**: Special bead wrapping tracked work units
- **Purpose**: Ticketing system for feature delivery
- **Structure**: Not epic-based, tracks external work
- **Dashboard**: Charmbracelet TUI with expanding trees
- **Swarms**: Multiple ephemeral attacks on same convoy

### 5.2 Patrol System
| Agent | Patrol Function | Frequency | Purpose |
|-------|----------------|-----------|---------|
| **Refinery** | Process merge queue | Loop with backoff | Sequential conflict-free merging |
| **Witness** | Check polecat health | Loop with backoff | Prevent stuck states, assist workers |
| **Deacon** | Town coordination | Loop with backoff | DYFJ propagation, plugin execution |

### 5.3 Merge Queue (MQ) Architecture
- **Problem**: Monkey knife fight over rebasing/merging
- **Solution**: Refinery processes one MR at a time
- **Intelligence**: Reimagines changes against new head
- **Escalation**: No work lost, but can escalate conflicts

### 5.4 Plugin System
- **Definition**: "Coordinated or scheduled attention from an agent"
- **Town-level**: Run by Deacon via Dogs
- **Rig-level**: Run by Witness patrol
- **Infrastructure**: Lifecycle hooks, timers, callbacks
- **Future**: Planned Mol Mall integration

---

## 6. USER INTERFACE & INTERACTION

### 6.1 tmux Integration
- **Primary UI**: tmux as core interface
- **Key Bindings**: `C-b s`, `C-b n/p`, `C-b [`, `C-b a`
- **Session Management**: List, switch, cycle workers
- **Activity Feed**: Real-time convoy tracking
- **Remote Workers**: Enables cloud worker expansion

### 6.2 Command Line Interface
```bash
gt rig add <repo>           # Add project to Gas Town
gt sling <work> <agent>     # Assign work to agent
gt nudge <agent>            # Send startup notification
gt seance <role>            # Talk to predecessor
gt handoff                  # Restart session gracefully
```

### 6.3 Dashboard & Monitoring
- **Convoy Dashboard**: Real-time work tracking
- **Activity Feed**: Live update stream
- **Worker Status**: Agent health and workload
- **Charmbracelet TUI**: Expandable tree interface

---

## 7. ADVANCED FEATURES

### 7.1 Federation (Planned)
- **Remote Workers**: GCP/cloud expansion
- **Town Linking**: Share work between human towns
- **Capacity Scaling**: Expand beyond local tmux limits

### 7.2 Quality Gates
- **Integration**: UBS scanning, safety hooks
- **Review Workflows**: Multi-pass review templates
- **Rule of Five**: Jeffrey Emanuel's 5-review formula

### 7.3 Planning & Work Generation
- **Epic Creation**: Top-down planning via beads
- **Formula Workflows**: Template-driven work generation
- **Swarm Generation**: Large convoy creation
- **Design Integration**: Spec Kit, BMAD compatibility

---

## 8. INFRASTRUCTURE REQUIREMENTS

### 8.1 Dependencies
- **Beads**: Universal Git-backed data plane
- **Claude Code**: Worker agent foundation
- **tmux**: Primary UI and session management
- **Go**: Gas Town core implementation (75k LOC)
- **Git**: All persistence and coordination

### 8.2 Architecture Principles
- **Graceful Degradation**: Works with partial systems
- **No-tmux Mode**: Limps along with naked Claude Code
- **Cattle vs Pets**: Sessions = cattle, agents = pets
- **Git-centric**: All state in version control

---

## 9. COMPARISON FRAMEWORKS

### 9.1 vs Kubernetes
- **Similarities**: Control plane, execution nodes, local agents, source of truth
- **Differences**: K8s asks "Is it running?", Gas Town asks "Is it done?"
- **Focus**: Uptime vs completion, continuous vs terminal goals

### 9.2 vs Temporal
- **Similarities**: Workflow durability, orchestration patterns
- **Differences**: Deterministic replay vs nondeterministic idempotence
- **Implementation**: Different machinery, similar guarantees

---

## 10. OPERATIONAL CHARACTERISTICS

### 10.1 Scale & Performance
- **Agent Count**: 20-30 active workers sustained
- **Cost Model**: "Expensive as hell", multiple Claude accounts needed
- **Throughput**: "Speed of thought" creation and correction
- **Efficiency**: ~100% not required, focus on velocity

### 10.2 Working Style
- **Vibe Coding**: Fluid, uncountable work units
- **Product Management**: Human as PM, Gas Town as idea compiler
- **Chaos Management**: Some work lost, bugs fixed multiple times
- **Relentless Forward**: Churning through huge work piles

### 10.3 Safety & Reliability
- **Graceful Degradation**: Partial failures handled
- **Work Preservation**: No work can be permanently lost
- **Session Recovery**: Automatic restart via GUPP
- **Conflict Resolution**: Intelligent merge queue handling

---

## NEXT: VALIDATION MAPPING
This component breakdown provides the foundation for systematic validation against our Gas Town Phase A/B/C implementation. Each component needs verification for:
1. **Presence**: Does it exist in our system?
2. **Functionality**: Does it work as described?
3. **Integration**: Does it integrate properly with other components?
4. **Performance**: Does it meet the described operational characteristics?