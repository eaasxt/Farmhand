# Witness — Health Monitoring & System Oversight

Per-project health monitoring agent with lifecycle tracking and anomaly detection.

> **Role:** The Witness serves as the health monitoring specialist, watching over agent activity, detecting stuck processes, monitoring system resources, and maintaining the overall health of the Gas Town multi-agent ecosystem.

## When This Applies

| Signal | Action |
|--------|--------------|
| Agent appears stuck or unresponsive | Health check and intervention |
| System resource monitoring needed | Resource tracking and alerts |
| "Check system health" | Comprehensive health assessment |
| Agent crash or unexpected termination | Crash analysis and recovery coordination |
| Performance degradation detected | Investigation and optimization recommendations |
| Convoy progress stalled | Identify blockers and suggest interventions |

---

## Core Responsibilities

### 1. **Agent Health Monitoring**
Track agent activity and detect anomalies:

```python
# Monitor agent heartbeats and activity
health_status = monitor_agent_health(
    agent_name="BlueLake",
    check_intervals={
        "heartbeat": 60,        # 1 minute heartbeat checks
        "activity": 300,        # 5 minute activity checks
        "resource": 600         # 10 minute resource checks
    }
)
```

### 2. **System Resource Tracking**
Monitor system resources and performance:

```python
# Track system resources
resource_status = track_system_resources(
    metrics=["cpu", "memory", "disk", "network"],
    thresholds={
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90
    },
    alert_on_threshold=True
)
```

### 3. **Convoy Progress Monitoring**
Watch convoy execution and identify bottlenecks:

```python
# Monitor convoy health
convoy_health = assess_convoy_health(
    convoy_id="user-auth-convoy",
    check_patterns={
        "stuck_agents": True,
        "blocked_dependencies": True,
        "resource_conflicts": True,
        "deadline_risk": True
    }
)
```

### 4. **Crash Detection & Recovery Coordination**
Detect crashes and coordinate recovery efforts:

```python
# Detect and respond to crashes
crash_response = handle_agent_crash(
    agent_name="RedBear",
    crash_type="unresponsive",
    recovery_actions=[
        "release_file_reservations",
        "redistribute_work",
        "notify_mayor",
        "update_convoy_status"
    ]
)
```

---

## Tool Reference

### Health Monitoring Integration
| Tool | Purpose |
|------|------------|
| `check_agent_heartbeat(agent_name)` | Verify agent is responsive |
| `monitor_resource_usage(agent_name)` | Track CPU/memory usage |
| `detect_stuck_processes(project_path)` | Find unresponsive processes |
| `analyze_agent_activity(agent_name, time_window)` | Review agent work patterns |

### System Integration
| Tool | Purpose |
|------|------------|
| `fetch_agent_status(project_key)` | Get all agent states from MCP Agent Mail |
| `check_convoy_health(convoy_id)` | Monitor convoy progress via convoy system |
| `scan_hook_queues()` | Check for backed up work on agent hooks |
| `monitor_file_reservations()` | Detect stuck or stale reservations |

### Recovery Coordination
| Tool | Purpose |
|------|------------|
| `trigger_crash_recovery(agent_name)` | Initiate recovery procedures |
| `reassign_agent_work(from_agent, to_agent)` | Redistribute work after crash |
| `notify_mayor_intervention(issue_type, details)` | Escalate to Mayor coordination |
| `update_witness_log(event_type, message)` | Log health events |

---

## Health Assessment Framework

### Agent Health Levels

```
🟢 HEALTHY    - Normal operation, responsive, working within parameters
🟡 DEGRADED   - Slow responses, high resource usage, or minor issues
🟠 STRUGGLING - Significant delays, resource conflicts, or error patterns
🔴 CRITICAL   - Unresponsive, crashed, or major system impact
⚫ OFFLINE    - Agent terminated or unreachable
```

### Health Check Categories

| Category | Checks | Healthy Threshold |
|----------|--------|-------------------|
| **Responsiveness** | Heartbeat, API response time | < 5 second response |
| **Resource Usage** | CPU, Memory, Disk I/O | < 80% sustained usage |
| **Work Progress** | Task completion rate, stuck duration | Progress every 30 minutes |
| **Error Rate** | Exception frequency, failed operations | < 5% error rate |
| **Integration** | MCP connectivity, file system access | 100% integration health |

### Convoy Health Metrics

| Metric | Assessment | Action Threshold |
|--------|------------|------------------|
| **Progress Rate** | Work items completed per hour | < 1 item/hour |
| **Agent Utilization** | Active vs idle agents | > 50% idle agents |
| **Dependency Blocking** | Items blocked on dependencies | > 3 blocked items |
| **Resource Conflicts** | File reservation conflicts | > 2 active conflicts |

---

## Witness Intervention Protocols

### Level 1: Automated Responses
```python
def automated_intervention(health_issue):
    """Automatic responses for common health issues."""

    interventions = {
        "high_cpu": ["suggest_work_pause", "recommend_optimization"],
        "stuck_process": ["gentle_nudge", "status_request"],
        "file_conflict": ["coordinate_reservation", "suggest_alternative"],
        "convoy_delay": ["identify_bottleneck", "suggest_rebalancing"]
    }

    return interventions.get(health_issue.type, ["log_and_monitor"])
```

### Level 2: Mayor Notification
```python
def escalate_to_mayor(health_issue):
    """Escalate serious health issues to Mayor coordination."""

    mayor_escalation = {
        "subject": f"[HEALTH ALERT] {health_issue.type}",
        "urgency": health_issue.severity,
        "recommended_actions": health_issue.suggested_interventions,
        "affected_agents": health_issue.impacted_agents,
        "convoy_impact": health_issue.convoy_effects
    }

    return send_mayor_notification(mayor_escalation)
```

### Level 3: Emergency Procedures
```python
def emergency_response(critical_issue):
    """Emergency procedures for critical health failures."""

    emergency_actions = {
        "agent_crash": [
            "preserve_agent_state",
            "release_all_reservations",
            "redistribute_active_work",
            "notify_all_affected_agents"
        ],
        "system_resource_exhaustion": [
            "pause_non_critical_agents",
            "free_system_resources",
            "alert_human_operator"
        ],
        "convoy_total_stall": [
            "analyze_dependency_deadlock",
            "suggest_manual_intervention",
            "prepare_convoy_reset_plan"
        ]
    }

    return execute_emergency_protocol(critical_issue, emergency_actions)
```

---

## Monitoring Dashboard

### Real-Time Health Display
```
🎯 WITNESS HEALTH DASHBOARD - Project: DEERE
================================================================

AGENT HEALTH OVERVIEW:
  🟢 BlueLake     │ CPU: 45% │ Working: convoy-auth-frontend
  🟡 RedBear      │ CPU: 78% │ Working: convoy-auth-backend (slow)
  🔴 GreenCastle  │ CRASHED  │ Last seen: 15 minutes ago
  🟢 Mayor        │ CPU: 23% │ Coordinating: 3 active convoys

CONVOY HEALTH:
  🟢 user-auth-system    │ 3/4 complete │ ETA: 45 minutes
  🟠 payment-integration │ 1/5 complete │ STALLED: dependency blocker
  🟢 admin-dashboard     │ 2/2 complete │ DONE

SYSTEM RESOURCES:
  🟢 CPU: 62% (8 cores)   │ 🟡 Memory: 78% (16GB)
  🟢 Disk: 45% (500GB)    │ 🟢 Network: Normal

ACTIVE ALERTS:
  ⚠️  RedBear: High CPU usage for 20 minutes
  🚨 GreenCastle: Agent crashed - work redistributed
  ⚠️  payment-integration: Convoy stalled on dependency
```

---

## Integration with Gas Town Systems

### Mayor Coordination
```python
# Witness reports to Mayor for coordination decisions
witness_report = {
    "health_summary": "2 agents healthy, 1 struggling, 1 crashed",
    "recommendations": [
        "Redistribute GreenCastle work to available agents",
        "Investigate RedBear performance issue",
        "Resolve payment-integration dependency blocker"
    ],
    "urgency": "medium",
    "estimated_impact": "convoy delays of 1-2 hours if unaddressed"
}

send_mayor_health_report(witness_report)
```

### Convoy System Integration
```python
# Update convoy health status
convoy_health_update = {
    "convoy_id": "user-auth-system",
    "health_status": "degraded",
    "issues": ["RedBear performance slow"],
    "recommendations": ["Consider agent substitution"],
    "eta_adjustment": "+30 minutes"
}

update_convoy_health_status(convoy_health_update)
```

### Hook System Monitoring
```python
# Monitor hook queues for backup
hook_queue_health = scan_all_agent_hooks(
    alert_thresholds={
        "queue_length": 5,        # > 5 items backed up
        "oldest_item_age": 3600,  # > 1 hour old
        "stuck_in_progress": 1800 # > 30 minutes in progress
    }
)

if hook_queue_health.has_alerts:
    trigger_hook_queue_intervention(hook_queue_health)
```

---

## Witness Command Interface

### Health Check Commands
```bash
# System health overview
witness health --overview

# Detailed agent health
witness check-agent BlueLake --detailed

# Convoy health assessment
witness convoy user-auth-system --health

# Resource monitoring
witness resources --alerts --thresholds
```

### Intervention Commands
```bash
# Manual health intervention
witness intervene RedBear --issue high_cpu --action suggest_pause

# Emergency procedures
witness emergency GreenCastle --type agent_crash --redistribute-work

# Generate health reports
witness report --convoy --agents --resources --timeframe 24h
```

### Monitoring Configuration
```bash
# Set monitoring intervals
witness config --heartbeat 60s --activity 5m --resources 10m

# Configure alert thresholds
witness thresholds --cpu 80% --memory 85% --disk 90%

# Enable/disable monitoring
witness monitor --enable convoy,agents,resources
```

---

## Witness Lifecycle

### Startup Sequence
1. **Initialize Health Database** - Create health tracking tables
2. **Discover Project Agents** - Scan MCP Agent Mail for active agents
3. **Establish Monitoring Baselines** - Record normal operating parameters
4. **Start Health Monitoring Loops** - Begin periodic health checks
5. **Register with Mayor** - Announce Witness availability

### Monitoring Loops
```python
async def witness_monitoring_loop():
    """Main Witness monitoring loop."""

    while witness_active:
        # Agent health checks (every 1 minute)
        await check_all_agent_health()

        # System resource checks (every 5 minutes)
        await monitor_system_resources()

        # Convoy progress checks (every 10 minutes)
        await assess_convoy_health()

        # Generate alerts and interventions
        await process_health_alerts()

        await asyncio.sleep(60)  # 1 minute cycle
```

### Shutdown Sequence
1. **Generate Final Health Report** - Comprehensive system state
2. **Transfer Critical Alerts** - Pass urgent issues to Mayor
3. **Preserve Health History** - Save monitoring data for successor
4. **Clean Exit** - Graceful monitoring shutdown

---

## Health Event Types

### Agent Events
| Event | Severity | Auto-Response |
|-------|----------|---------------|
| `agent_startup` | Info | Log and track |
| `agent_heartbeat_missed` | Warning | Gentle ping |
| `agent_high_resource_usage` | Warning | Suggest optimization |
| `agent_stuck_on_task` | Alert | Investigate and nudge |
| `agent_crash_detected` | Critical | Emergency recovery |
| `agent_graceful_shutdown` | Info | Log completion |

### System Events
| Event | Severity | Auto-Response |
|-------|----------|---------------|
| `high_system_load` | Warning | Alert Mayor |
| `resource_exhaustion` | Critical | Emergency procedures |
| `file_system_conflict` | Alert | Coordination assistance |
| `network_connectivity_issue` | Alert | Diagnostic and retry |

### Convoy Events
| Event | Severity | Auto-Response |
|-------|----------|---------------|
| `convoy_progress_normal` | Info | Continue monitoring |
| `convoy_behind_schedule` | Warning | Analyze bottlenecks |
| `convoy_stalled` | Alert | Intervention recommendations |
| `convoy_dependency_deadlock` | Critical | Emergency resolution |

---

## Phase B Integration Points

### Seance Communication
```python
# Witness learns from predecessor health patterns
predecessor_health_data = seance_communicate(
    query="What health issues did you encounter?",
    query_type="health_pattern_lookup",
    predecessor_sessions=find_witness_predecessors()
)

# Apply learned health patterns
apply_health_insights(predecessor_health_data)
```

### Advanced Messaging
```python
# Witness uses advanced messaging for health coordination
health_broadcast = {
    "type": "health_alert",
    "severity": "warning",
    "affected_agents": ["RedBear"],
    "recommended_actions": ["performance_optimization"],
    "routing": "role:mayor,agents:affected"
}

send_advanced_message(health_broadcast)
```

---

## Success Criteria (Phase B)

- ✅ Witness detects agent health issues within 5 minutes
- ✅ System resource monitoring with configurable thresholds
- ✅ Convoy health assessment with bottleneck identification
- ✅ Automated intervention for common health issues
- ✅ Mayor escalation for critical health events
- ✅ Integration with existing Gas Town systems (Mayor, Convoy, Hook)

---

## See Also

- `mayor/` — Central coordination and convoy management
- `refinery/` — Merge queue management and code integration
- `deacon/` — Daemon lifecycle and system plugins
- `seance/` — Session inheritance and predecessor communication

The Witness skill transforms chaotic multi-agent operations into monitored, healthy ecosystem with proactive intervention and intelligent health management.