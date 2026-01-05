# Deacon — Daemon Lifecycle & System Orchestration

System-wide plugin management, daemon coordination, and infrastructure oversight.

> **Role:** The Deacon serves as the system orchestrator, managing long-running processes, daemon lifecycles, system-wide plugins, and infrastructure coordination. Think of the Deacon as the "system administrator" of the Gas Town multi-agent ecosystem.

## When This Applies

| Signal | Action |
|--------|--------------|
| System startup or infrastructure changes | Daemon orchestration |
| "Start system services" or "initialize daemons" | Service lifecycle management |
| Long-running background tasks needed | Daemon process creation |
| System plugin installation or updates | Plugin lifecycle management |
| Infrastructure health monitoring | System oversight |
| Cross-project coordination required | Multi-project daemon management |

---

## Core Responsibilities

### 1. **Daemon Lifecycle Management**
Orchestrate system daemons and long-running processes:

```python
# Manage daemon lifecycles
daemon_config = {
    "mcp_agent_mail": {
        "service": "mcp-agent-mail",
        "port": 8765,
        "health_check": "http://localhost:8765/health",
        "restart_policy": "always",
        "dependencies": ["postgresql"]
    },
    "convoy_monitor": {
        "command": ["python", "/home/ubuntu/.claude/convoy_monitor.py"],
        "working_dir": "/home/ubuntu/.claude",
        "restart_policy": "on_failure",
        "dependencies": ["mcp_agent_mail"]
    }
}

daemon_status = manage_daemon_lifecycle(daemon_config)
```

### 2. **System Plugin Coordination**
Manage system-wide plugins and extensions:

```python
# Plugin lifecycle management
plugin_registry = {
    "gas_town_hooks": {
        "type": "claude_hooks",
        "location": "/home/ubuntu/.claude/hooks",
        "enabled": True,
        "auto_update": True
    },
    "convoy_dashboard": {
        "type": "web_interface",
        "port": 8080,
        "enabled": True,
        "dependencies": ["convoy_system"]
    }
}

plugin_status = orchestrate_plugins(plugin_registry)
```

### 3. **Cross-Project Coordination**
Coordinate daemons across multiple projects:

```python
# Multi-project daemon coordination
project_daemons = {
    "/home/ubuntu/projects/deere": ["convoy_monitor", "hook_processor"],
    "/home/ubuntu/projects/marketplace": ["template_indexer", "usage_analyzer"],
    "/home/ubuntu/projects/tools": ["cass_indexer", "health_monitor"]
}

coordination_status = coordinate_cross_project_daemons(project_daemons)
```

### 4. **Infrastructure Health Oversight**
Monitor and maintain system infrastructure:

```python
# Infrastructure health management
infrastructure_config = {
    "databases": {
        "convoy_db": "/home/ubuntu/.beads/convoy.db",
        "hooks_db": "/home/ubuntu/.beads/hooks.db",
        "seance_db": "/home/ubuntu/.beads/seance.db"
    },
    "services": ["mcp-agent-mail", "ollama"],
    "filesystem": {
        "session_storage": "/home/ubuntu/.claude/sessions",
        "log_directory": "/home/ubuntu/.claude/logs"
    }
}

health_status = monitor_infrastructure_health(infrastructure_config)
```

---

## Tool Reference

### Daemon Management
| Tool | Purpose |
|------|------------|
| `start_daemon(name, config)` | Launch system daemon process |
| `stop_daemon(name, graceful=True)` | Terminate daemon with optional grace period |
| `restart_daemon(name, reason)` | Restart daemon with logging |
| `check_daemon_health(name)` | Verify daemon is healthy and responsive |

### Plugin Orchestration
| Tool | Purpose |
|------|------------|
| `install_plugin(plugin_spec)` | Install and configure system plugin |
| `enable_plugin(plugin_name)` | Activate plugin in system |
| `update_plugin(plugin_name, version)` | Update plugin to specific version |
| `list_active_plugins()` | Get status of all system plugins |

### Infrastructure Monitoring
| Tool | Purpose |
|------|------------|
| `check_service_status(service_name)` | Monitor systemd service health |
| `validate_database_health(db_path)` | Check database integrity and performance |
| `monitor_filesystem_space(paths)` | Track disk usage and capacity |
| `assess_system_resources()` | Comprehensive resource utilization |

---

## Daemon Architecture Framework

### Service Dependency Graph
```
                     🔧 DEACON DAEMON ORCHESTRATION
                    ════════════════════════════════

Level 1 (Foundation):
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │     Ollama      │  │   File System   │
│   (optional)    │  │  (LLM Runtime)  │  │   Watchers      │
└─────────────────┘  └─────────────────┘  └─────────────────┘

Level 2 (Core Services):
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ MCP Agent Mail  │  │   Convoy Sys    │  │   Hook Sys      │
│   (Port 8765)   │  │   (SQLite)      │  │   (SQLite)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └──────────┬─────────────────┬────────────┘
                    │                 │
Level 3 (Monitoring):
         ┌─────────────────┐  ┌─────────────────┐
         │ Convoy Monitor  │  │  Health Monitor │
         │   (Daemon)      │  │   (Witness)     │
         └─────────────────┘  └─────────────────┘

Level 4 (User Interfaces):
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│Convoy Dashboard │  │  Health Web UI  │  │  Plugin Manager │
│  (Port 8080)    │  │  (Port 8081)    │  │     (CLI)       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Daemon Configuration Schema
```yaml
# /home/ubuntu/.claude/deacon/daemon_config.yaml
daemons:
  mcp_agent_mail:
    type: systemd_service
    service_name: mcp-agent-mail
    health_check:
      url: "http://localhost:8765/health"
      timeout: 5
      interval: 60
    restart_policy: always
    dependencies: []

  convoy_monitor:
    type: python_process
    command: ["python3", "/home/ubuntu/.claude/convoy_monitor.py"]
    working_directory: "/home/ubuntu/.claude"
    environment:
      PYTHONPATH: "/home/ubuntu/.claude"
    health_check:
      type: heartbeat_file
      file_path: "/tmp/convoy_monitor.heartbeat"
      max_age: 120
    restart_policy: on_failure
    dependencies: ["mcp_agent_mail"]

  hook_processor:
    type: python_process
    command: ["python3", "/home/ubuntu/.claude/hook_processor.py"]
    working_directory: "/home/ubuntu/.claude"
    health_check:
      type: process_check
      timeout: 30
    restart_policy: always
    dependencies: ["mcp_agent_mail"]
```

---

## Plugin Management System

### Plugin Registry
```python
PLUGIN_REGISTRY = {
    "gas_town_core": {
        "type": "system_integration",
        "components": ["mayor", "convoy", "hooks", "seance"],
        "auto_start": True,
        "health_check": "integrated_health_check"
    },

    "witness_monitoring": {
        "type": "monitoring_daemon",
        "executable": "/home/ubuntu/.claude/witness_daemon.py",
        "config_file": "/home/ubuntu/.claude/witness/config.json",
        "web_interface": {"port": 8081, "enabled": True}
    },

    "refinery_queue": {
        "type": "integration_service",
        "git_hooks": ["pre-merge", "post-merge"],
        "quality_gates": ["ubs", "tests", "review"],
        "webhook_endpoint": "/refinery/webhook"
    },

    "enhanced_templates": {
        "type": "processing_engine",
        "template_locations": [
            "/home/ubuntu/projects/deere/molecule-marketplace/templates"
        ],
        "processing_queue": "template_jobs"
    }
}
```

### Plugin Lifecycle Management
```python
async def manage_plugin_lifecycle(plugin_name, action):
    """Manage plugin installation, updates, and removal."""

    plugin_config = PLUGIN_REGISTRY.get(plugin_name)
    if not plugin_config:
        raise ValueError(f"Unknown plugin: {plugin_name}")

    lifecycle_actions = {
        "install": install_plugin_components,
        "start": start_plugin_services,
        "stop": stop_plugin_services,
        "update": update_plugin_version,
        "uninstall": remove_plugin_components,
        "health_check": check_plugin_health
    }

    action_handler = lifecycle_actions.get(action)
    if not action_handler:
        raise ValueError(f"Unknown action: {action}")

    return await action_handler(plugin_config)
```

---

## System Orchestration Patterns

### Startup Sequence Orchestration
```python
async def orchestrate_system_startup():
    """Coordinate Gas Town system startup sequence."""

    startup_phases = [
        {
            "name": "foundation",
            "parallel": True,
            "services": ["filesystem_setup", "database_init", "ollama_check"]
        },
        {
            "name": "core_services",
            "parallel": False,  # Sequential for dependency order
            "services": ["mcp_agent_mail", "convoy_system", "hook_system"]
        },
        {
            "name": "monitoring",
            "parallel": True,
            "services": ["witness_daemon", "convoy_monitor", "health_monitor"]
        },
        {
            "name": "interfaces",
            "parallel": True,
            "services": ["convoy_dashboard", "health_web_ui", "plugin_manager"]
        }
    ]

    for phase in startup_phases:
        if phase["parallel"]:
            await start_services_parallel(phase["services"])
        else:
            await start_services_sequential(phase["services"])

        # Validate phase completion
        await validate_phase_health(phase["name"])

    return await system_startup_verification()
```

### Graceful Shutdown Coordination
```python
async def orchestrate_graceful_shutdown():
    """Coordinate clean system shutdown."""

    shutdown_phases = [
        {
            "name": "user_interfaces",
            "services": ["convoy_dashboard", "health_web_ui"],
            "timeout": 30
        },
        {
            "name": "monitoring",
            "services": ["witness_daemon", "convoy_monitor"],
            "timeout": 60
        },
        {
            "name": "core_services",
            "services": ["hook_system", "convoy_system"],
            "timeout": 120
        },
        {
            "name": "foundation",
            "services": ["mcp_agent_mail"],
            "timeout": 180
        }
    ]

    for phase in reversed(shutdown_phases):  # Reverse order
        await shutdown_services_gracefully(
            phase["services"],
            timeout=phase["timeout"]
        )
```

---

## Infrastructure Health Monitoring

### System Health Dashboard
```
🔧 DEACON INFRASTRUCTURE DASHBOARD - Gas Town System Health
═══════════════════════════════════════════════════════════════════

DAEMON STATUS:
  🟢 mcp-agent-mail      │ PID: 12345 │ CPU: 2.1% │ Mem: 45MB  │ Up: 2d 4h
  🟢 convoy-monitor      │ PID: 12346 │ CPU: 0.8% │ Mem: 28MB  │ Up: 2d 4h
  🟢 hook-processor      │ PID: 12347 │ CPU: 1.2% │ Mem: 35MB  │ Up: 2d 4h
  🟡 witness-daemon      │ PID: 12348 │ CPU: 15%  │ Mem: 120MB │ Up: 4h (restarted)

PLUGIN STATUS:
  ✅ gas_town_core       │ Active    │ Version: 2.1.0 │ Health: Good
  ✅ witness_monitoring  │ Active    │ Version: 1.5.2 │ Health: Good
  ✅ refinery_queue      │ Active    │ Version: 1.3.1 │ Health: Good
  🔄 enhanced_templates  │ Updating  │ Version: 1.2.0→1.2.1 │ Health: Updating

DATABASE HEALTH:
  🟢 convoy.db          │ Size: 15MB   │ Connections: 3  │ Last backup: 2h ago
  🟢 hooks.db           │ Size: 8MB    │ Connections: 2  │ Last backup: 2h ago
  🟢 seance.db          │ Size: 45MB   │ Connections: 1  │ Last backup: 2h ago

SYSTEM RESOURCES:
  🟢 CPU Usage: 18% (8 cores)     │ 🟢 Memory: 62% (16GB)
  🟢 Disk Usage: 45% (500GB)      │ 🟢 Network: 15MB/s
  🟢 Load Average: 0.8, 0.7, 0.9  │ 🟢 Uptime: 15d 8h 32m

SERVICE ENDPOINTS:
  🌐 MCP Agent Mail: http://localhost:8765 (✅ Healthy)
  🌐 Convoy Dashboard: http://localhost:8080 (✅ Healthy)
  🌐 Health Monitor: http://localhost:8081 (✅ Healthy)

RECENT EVENTS:
  15:23 │ witness-daemon restarted (high memory usage resolved)
  14:45 │ enhanced_templates plugin update initiated
  12:30 │ convoy-monitor: Queue processing optimized
  10:15 │ Daily database backup completed successfully

ALERTS:
  ⚠️  witness-daemon memory usage trending upward - monitoring
  💡 System performance excellent - no issues detected
```

---

## Cross-Project Coordination

### Multi-Project Daemon Management
```python
class CrossProjectCoordinator:
    """Coordinate daemons across multiple Gas Town projects."""

    def __init__(self):
        self.projects = {
            "deere": "/home/ubuntu/projects/deere",
            "marketplace": "/home/ubuntu/projects/deere/molecule-marketplace",
            "tools": "/home/ubuntu/projects/tools"
        }

    async def coordinate_project_daemons(self):
        """Start project-specific daemons with coordination."""

        project_configs = {
            "deere": {
                "convoy_monitor": {"priority": "high", "port": 8082},
                "template_processor": {"priority": "medium", "port": 8083}
            },
            "marketplace": {
                "usage_analyzer": {"priority": "low", "port": 8084},
                "template_indexer": {"priority": "medium", "port": 8085}
            },
            "tools": {
                "cass_indexer": {"priority": "low", "port": 8086}
            }
        }

        # Start high priority daemons first
        for priority in ["high", "medium", "low"]:
            parallel_starts = []
            for project, daemons in project_configs.items():
                for daemon, config in daemons.items():
                    if config["priority"] == priority:
                        parallel_starts.append(
                            self.start_project_daemon(project, daemon, config)
                        )

            if parallel_starts:
                await asyncio.gather(*parallel_starts)
```

---

## Integration with Gas Town Systems

### Mayor Coordination
```python
# Deacon reports infrastructure status to Mayor
infrastructure_report = {
    "system_health": "good",
    "daemon_status": {
        "total_daemons": 8,
        "healthy": 7,
        "degraded": 1,
        "failed": 0
    },
    "resource_utilization": {
        "cpu_percent": 18,
        "memory_percent": 62,
        "disk_percent": 45
    },
    "recommendations": [
        "witness-daemon memory optimization needed",
        "system capacity available for additional agents"
    ]
}

send_mayor_infrastructure_report(infrastructure_report)
```

### Witness Health Integration
```python
# Coordinate with Witness for comprehensive health monitoring
witness_integration = {
    "infrastructure_health": get_infrastructure_health(),
    "daemon_performance": get_daemon_performance_metrics(),
    "system_capacity": assess_system_capacity(),
    "scaling_recommendations": generate_scaling_recommendations()
}

coordinate_with_witness(witness_integration)
```

### Plugin Event System
```python
# Plugin event coordination
plugin_events = {
    "plugin_installed": notify_system_of_new_capabilities,
    "plugin_updated": refresh_dependent_services,
    "plugin_failed": isolate_and_recover_plugin,
    "plugin_removed": cleanup_plugin_dependencies
}

async def handle_plugin_event(event_type, plugin_name, event_data):
    """Coordinate plugin lifecycle events across system."""

    handler = plugin_events.get(event_type)
    if handler:
        await handler(plugin_name, event_data)

    # Notify Mayor of plugin changes
    await notify_mayor_plugin_event(event_type, plugin_name, event_data)
```

---

## Deacon Command Interface

### Daemon Management Commands
```bash
# Daemon lifecycle
deacon start convoy-monitor --config /path/to/config
deacon stop witness-daemon --graceful
deacon restart mcp-agent-mail --reason "configuration update"
deacon status --all --detailed

# Health monitoring
deacon health --daemons --infrastructure --databases
deacon logs convoy-monitor --tail 100 --follow
deacon performance --metrics cpu,memory,disk --interval 5s
```

### Plugin Management Commands
```bash
# Plugin operations
deacon plugin install gas_town_enhanced --version latest
deacon plugin enable witness_monitoring
deacon plugin update enhanced_templates --auto-restart
deacon plugin list --status --health

# System orchestration
deacon system startup --verify-health
deacon system shutdown --graceful --timeout 300
deacon system health --comprehensive --export /tmp/health_report.json
```

### Cross-Project Commands
```bash
# Multi-project coordination
deacon projects status --all
deacon projects sync-daemons --project deere,marketplace
deacon projects resource-summary --include-recommendations
```

---

## Advanced Orchestration Features

### Automatic Scaling
```python
async def auto_scale_system(load_metrics):
    """Automatically scale system based on load."""

    scaling_rules = {
        "high_convoy_load": {
            "trigger": "convoy_queue_length > 10",
            "action": "start_additional_convoy_monitor"
        },
        "high_agent_count": {
            "trigger": "active_agents > 15",
            "action": "increase_mcp_agent_mail_workers"
        },
        "low_system_load": {
            "trigger": "cpu_usage < 20% for 30m",
            "action": "consolidate_daemon_processes"
        }
    }

    for rule_name, rule in scaling_rules.items():
        if evaluate_trigger(rule["trigger"], load_metrics):
            await execute_scaling_action(rule["action"])
```

### Disaster Recovery
```python
async def disaster_recovery_protocol():
    """Coordinate disaster recovery procedures."""

    recovery_steps = [
        {"action": "assess_system_damage", "timeout": 30},
        {"action": "preserve_critical_data", "timeout": 120},
        {"action": "restart_foundation_services", "timeout": 180},
        {"action": "verify_data_integrity", "timeout": 300},
        {"action": "restore_monitoring_systems", "timeout": 120},
        {"action": "notify_agents_of_recovery", "timeout": 60}
    ]

    recovery_log = []
    for step in recovery_steps:
        try:
            result = await execute_recovery_step(
                step["action"],
                timeout=step["timeout"]
            )
            recovery_log.append({"step": step["action"], "result": "success"})
        except Exception as e:
            recovery_log.append({"step": step["action"], "result": f"failed: {e}"})
            # Continue with recovery - some failures may be acceptable

    return recovery_log
```

---

## Success Criteria (Phase B)

- ✅ System daemon orchestration with dependency management
- ✅ Plugin lifecycle management with health monitoring
- ✅ Cross-project coordination and resource sharing
- ✅ Infrastructure health oversight with automated scaling
- ✅ Integration with Mayor for system-wide coordination
- ✅ Disaster recovery and system resilience protocols

---

## See Also

- `mayor/` — Central coordination and convoy management
- `witness/` — Health monitoring and system oversight
- `refinery/` — Merge queue management and code integration
- `seance/` — Session inheritance and predecessor communication

The Deacon skill transforms chaotic system administration into orchestrated infrastructure management, enabling Gas Town's vision of robust, scalable, multi-agent coordination with enterprise-grade reliability.