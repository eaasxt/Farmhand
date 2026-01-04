# Refinery — Intelligent Merge Queue & Code Integration

Sequential code integration with conflict resolution and quality gates.

> **Role:** The Refinery serves as the intelligent merge queue manager, ensuring clean sequential integration of multi-agent code contributions while maintaining code quality and preventing integration conflicts in Gas Town's high-velocity development environment.

## When This Applies

| Signal | Action |
|--------|--------------|
| Multiple agents completing work simultaneously | Sequence merge order |
| Pull request ready for integration | Quality gate assessment |
| Merge conflict detected | Conflict resolution coordination |
| "Ready to merge" or "integrate changes" | Queue management and execution |
| Code quality gate failure | Issue investigation and remediation |
| Convoy work ready for integration | Coordinated multi-agent merge |

---

## Core Responsibilities

### 1. **Intelligent Merge Sequencing**
Optimize merge order to minimize conflicts and maximize throughput:

```python
# Analyze and sequence merge requests
merge_sequence = optimize_merge_order(
    pending_merges=[
        {"agent": "BlueLake", "branch": "feature/auth-ui", "files": ["src/ui/**"], "risk": "low"},
        {"agent": "RedBear", "branch": "feature/auth-api", "files": ["src/api/**"], "risk": "medium"},
        {"agent": "GreenCastle", "branch": "feature/auth-db", "files": ["migrations/**"], "risk": "high"}
    ],
    optimization_strategy="minimal_conflicts"
)
```

### 2. **Conflict Detection & Resolution**
Proactively detect and coordinate conflict resolution:

```python
# Analyze potential merge conflicts
conflict_analysis = analyze_merge_conflicts(
    base_branch="main",
    merge_branches=["feature/auth-ui", "feature/auth-api"],
    analysis_depth="semantic",  # syntax, semantic, or integration
    auto_resolution=True
)
```

### 3. **Quality Gate Management**
Enforce quality standards before integration:

```python
# Define and execute quality gates
quality_gates = [
    {"type": "tests", "requirement": "all_pass", "timeout": 600},
    {"type": "security_scan", "requirement": "no_high_severity", "tool": "ubs"},
    {"type": "code_review", "requirement": "approved", "reviewers": 1},
    {"type": "integration_test", "requirement": "pass", "environments": ["staging"]}
]

gate_results = execute_quality_gates("feature/auth-ui", quality_gates)
```

### 4. **Convoy Integration Coordination**
Coordinate complex multi-agent convoy merges:

```python
# Coordinate convoy completion integration
convoy_integration = coordinate_convoy_merge(
    convoy_id="user-auth-system",
    completed_work=["auth-api", "auth-ui", "auth-db", "auth-tests"],
    integration_strategy="dependency_ordered",
    rollback_plan="auto_revert"
)
```

---

## Tool Reference

### Git Integration
| Tool | Purpose |
|------|------------|
| `analyze_merge_impact(branch, target)` | Assess merge complexity and conflicts |
| `create_integration_branch(convoy_name)` | Temporary integration testing branch |
| `execute_safe_merge(branch, strategy)` | Conflict-aware merge execution |
| `rollback_integration(merge_id, reason)` | Revert failed integrations |

### Quality Assessment
| Tool | Purpose |
|------|------------|
| `run_quality_gates(branch, gates)` | Execute quality checks |
| `analyze_code_impact(changes)` | Assess change impact and risk |
| `detect_breaking_changes(diff)` | Identify API/behavior changes |
| `validate_convoy_consistency(convoy_id)` | Check convoy work coherence |

### Coordination
| Tool | Purpose |
|------|------------|
| `notify_merge_queue_status(agents)` | Update agents on queue position |
| `request_conflict_resolution(agents, files)` | Coordinate conflict fixing |
| `trigger_integration_testing(branch)` | Run comprehensive integration tests |
| `update_convoy_integration_status(convoy_id)` | Report convoy merge progress |

---

## Merge Queue Architecture

### Priority-Based Sequencing

```
🏭 REFINERY MERGE QUEUE
════════════════════════════════════════════════════════════

PRIORITY 1 (Critical/Hotfix):
  🔥 hotfix/security-patch     │ RedBear    │ Ready    │ ETA: 5 min
  🚨 hotfix/prod-crash        │ BlueLake   │ Testing  │ ETA: 10 min

PRIORITY 2 (Convoy Completions):
  📦 convoy/user-auth-system  │ 4 agents   │ Ready    │ ETA: 15 min
  📦 convoy/payment-flow      │ 2 agents   │ Staging  │ ETA: 25 min

PRIORITY 3 (Feature Work):
  ⭐ feature/dashboard-ui     │ GreenCast  │ Queue    │ ETA: 35 min
  ⭐ feature/reporting-api    │ YellowLak  │ Queue    │ ETA: 45 min

PRIORITY 4 (Improvements):
  🔧 refactor/auth-cleanup    │ RedBear    │ Queue    │ ETA: 55 min
  📝 docs/api-updates         │ BlueLake   │ Queue    │ ETA: 65 min

CURRENT STATUS: Processing hotfix/security-patch
QUEUE HEALTH: 🟢 Normal (8 items, avg wait: 12 minutes)
```

### Conflict Detection Matrix

| File Pattern | Auth-UI | Auth-API | Auth-DB | Risk Level |
|--------------|---------|----------|---------|------------|
| `src/auth/models.py` | ✅ | ⚠️ | ⚠️ | Medium |
| `src/auth/routes.py` | ❌ | ✅ | ❌ | Low |
| `migrations/*.sql` | ❌ | ❌ | ✅ | High |
| `tests/auth/**` | ✅ | ✅ | ✅ | High |
| `docs/auth.md` | ✅ | ✅ | ✅ | Medium |

**Legend**: ✅ Modifies, ❌ No Changes, ⚠️ Potential Conflict

---

## Quality Gate Framework

### Standard Quality Gates

```python
QUALITY_GATES = {
    "fast_track": [
        {"type": "syntax_check", "timeout": 30},
        {"type": "unit_tests", "timeout": 120},
        {"type": "security_scan_basic", "timeout": 60}
    ],

    "standard": [
        {"type": "syntax_check", "timeout": 30},
        {"type": "unit_tests", "timeout": 300},
        {"type": "integration_tests", "timeout": 600},
        {"type": "security_scan_full", "timeout": 180},
        {"type": "code_review", "requirement": "approved"}
    ],

    "convoy_integration": [
        {"type": "unit_tests", "timeout": 300},
        {"type": "integration_tests", "timeout": 900},
        {"type": "cross_component_tests", "timeout": 1200},
        {"type": "security_scan_comprehensive", "timeout": 300},
        {"type": "performance_regression", "timeout": 600},
        {"type": "multi_agent_review", "requirement": "consensus"}
    ]
}
```

### Gate Execution Pipeline

```python
async def execute_quality_pipeline(merge_request):
    """Execute quality gates with parallel optimization."""

    # Phase 1: Fast checks (parallel)
    fast_results = await asyncio.gather(
        syntax_check(merge_request.branch),
        security_scan_basic(merge_request.files),
        lint_check(merge_request.files)
    )

    if not all(fast_results):
        return reject_merge("Fast quality gates failed")

    # Phase 2: Test execution (parallel where possible)
    test_results = await asyncio.gather(
        run_unit_tests(merge_request.branch),
        run_integration_tests(merge_request.branch),
        run_security_tests(merge_request.files)
    )

    # Phase 3: Integration verification
    integration_result = await run_staging_deployment(merge_request.branch)

    return assess_overall_quality(fast_results, test_results, integration_result)
```

---

## Conflict Resolution Strategies

### Automatic Resolution
```python
def attempt_auto_resolution(conflict):
    """Attempt automatic conflict resolution for common patterns."""

    auto_strategies = {
        "import_order": lambda: sort_and_dedupe_imports(),
        "whitespace": lambda: normalize_whitespace(),
        "formatting": lambda: apply_code_formatter(),
        "simple_additions": lambda: merge_non_overlapping_additions(),
        "documentation": lambda: merge_documentation_changes()
    }

    if conflict.type in auto_strategies:
        return auto_strategies[conflict.type]()

    return None  # Requires manual resolution
```

### Coordinated Manual Resolution
```python
def coordinate_conflict_resolution(conflict):
    """Coordinate manual conflict resolution between agents."""

    resolution_plan = {
        "conflict_owner": determine_primary_owner(conflict.files),
        "collaborating_agents": identify_affected_agents(conflict),
        "resolution_strategy": suggest_resolution_approach(conflict),
        "timeline": estimate_resolution_time(conflict.complexity)
    }

    # Create temporary branch for resolution
    resolution_branch = create_resolution_branch(conflict)

    # Coordinate resolution work
    coordinate_resolution_work(resolution_plan, resolution_branch)

    return resolution_plan
```

---

## Integration Patterns

### Sequential Integration (Default)
```python
# One merge at a time, full validation each step
async def sequential_integration():
    for merge_request in merge_queue.prioritized_order():
        if await validate_merge(merge_request):
            await execute_merge(merge_request)
            await run_post_merge_validation()
        else:
            await handle_merge_failure(merge_request)
```

### Batched Integration (Convoy Mode)
```python
# Group related changes for efficient integration
async def convoy_batch_integration(convoy_id):
    convoy_merges = get_convoy_merge_requests(convoy_id)

    # Create integration branch
    integration_branch = create_convoy_integration_branch(convoy_id)

    # Merge all convoy work to integration branch
    for merge_request in convoy_merges:
        await merge_to_integration(merge_request, integration_branch)

    # Comprehensive validation
    if await validate_integration_branch(integration_branch):
        await promote_integration_to_main(integration_branch)
    else:
        await rollback_convoy_integration(convoy_id)
```

### Parallel Track Integration
```python
# Independent tracks can merge in parallel
async def parallel_track_integration():
    independent_tracks = identify_independent_tracks(merge_queue)

    for track in independent_tracks:
        asyncio.create_task(
            process_track_merges(track)
        )

    await asyncio.gather(*track_tasks)
```

---

## Refinery Dashboard

### Real-Time Queue Status
```
🏭 REFINERY MERGE QUEUE DASHBOARD - Project: DEERE
═══════════════════════════════════════════════════════════════

QUEUE OVERVIEW:
  📊 Total Items: 8       │ 🏃 In Progress: 2    │ ⏳ Waiting: 6
  ⏱️  Avg Wait Time: 12m  │ 🎯 Success Rate: 94% │ 🔄 Queue Velocity: 5/hour

CURRENT PROCESSING:
  🔥 hotfix/security-patch │ Stage: Quality Gates │ Progress: ████▓▓▓▓▓▓ 40%
  📦 convoy/user-auth     │ Stage: Integration   │ Progress: ████████▓▓ 80%

NEXT IN QUEUE:
  1. ⭐ feature/dashboard-ui    │ ETA: 8m  │ Risk: Low    │ Agent: GreenCastle
  2. 🔧 refactor/auth-cleanup  │ ETA: 18m │ Risk: Med    │ Agent: RedBear
  3. 📝 docs/api-updates       │ ETA: 25m │ Risk: Low    │ Agent: BlueLake

RECENT COMPLETIONS:
  ✅ feature/user-profile   │ 5m ago │ BlueLake   │ Duration: 8m
  ✅ hotfix/validation-bug  │ 12m ago│ RedBear    │ Duration: 6m
  ✅ convoy/payment-flow    │ 25m ago│ 3 agents   │ Duration: 22m

QUALITY GATE METRICS:
  🧪 Tests: 98.5% pass rate    │ 🔒 Security: 2 low findings avg
  📝 Review: 6m avg review     │ 🚀 Deploy: 94% success rate

ALERTS:
  ⚠️  Queue building up - consider adding merge capacity
  📈 Security scan times increased 15% this week
```

---

## Integration with Gas Town Systems

### Mayor Coordination
```python
# Refinery reports integration status to Mayor
integration_report = {
    "queue_health": "good",
    "current_throughput": "5 merges/hour",
    "bottlenecks": ["security_scan_duration"],
    "convoy_integrations": [
        {"convoy_id": "user-auth", "status": "in_progress", "eta": "15 minutes"}
    ],
    "recommendations": [
        "Consider parallel security scanning",
        "Convoy user-auth ready for final integration"
    ]
}

send_mayor_integration_report(integration_report)
```

### Convoy System Integration
```python
# Update convoy status based on integration progress
convoy_integration_update = {
    "convoy_id": "user-auth-system",
    "integration_stage": "quality_gates",
    "gate_results": {
        "tests": "passed",
        "security": "passed",
        "review": "pending"
    },
    "eta_main_merge": "15 minutes",
    "integration_branch": "integration/convoy-user-auth-20260104"
}

update_convoy_integration_status(convoy_integration_update)
```

### Witness Health Integration
```python
# Coordinate with Witness for health-aware merging
health_check = request_merge_health_assessment(
    affected_agents=["BlueLake", "RedBear"],
    merge_complexity="high",
    estimated_duration="20 minutes"
)

if health_check.agents_healthy and health_check.system_capacity_ok:
    proceed_with_merge()
else:
    defer_merge_until_healthy()
```

---

## Refinery Command Interface

### Queue Management Commands
```bash
# View merge queue status
refinery queue --status --detailed

# Add merge request to queue
refinery enqueue feature/new-auth --priority medium --agent BlueLake

# Adjust queue order
refinery reorder --move feature/dashboard-ui --position 1

# Remove from queue
refinery dequeue feature/broken-feature --reason "fails quality gates"
```

### Integration Commands
```bash
# Manual merge execution
refinery merge feature/auth-ui --strategy sequential --quality-gates standard

# Convoy integration
refinery convoy-merge user-auth-system --validate-dependencies

# Emergency integration (bypass some gates)
refinery emergency-merge hotfix/critical-bug --gates fast_track
```

### Quality Gate Commands
```bash
# Run quality gates manually
refinery quality-gates feature/auth-ui --gates unit,security,integration

# Configure gate requirements
refinery configure-gates --profile convoy --add performance_regression

# View gate history
refinery gate-history --branch feature/auth-ui --last 10
```

---

## Conflict Resolution Workflows

### Type 1: Semantic Conflicts
```python
def resolve_semantic_conflict(conflict):
    """Handle conflicts requiring logic understanding."""

    # Analyze intent of both changes
    change_intents = analyze_change_intentions(
        conflict.branch_a_changes,
        conflict.branch_b_changes
    )

    # Determine if intents are compatible
    if change_intents.compatible:
        return merge_compatible_changes(change_intents)
    else:
        return coordinate_intent_resolution(conflict.affecting_agents)
```

### Type 2: API Breaking Changes
```python
def handle_breaking_changes(breaking_change):
    """Coordinate resolution of breaking API changes."""

    impact_analysis = analyze_breaking_change_impact(
        breaking_change.modified_apis,
        codebase_scan=True
    )

    if impact_analysis.safe_to_proceed:
        return execute_coordinated_api_migration(breaking_change)
    else:
        return require_deprecation_cycle(breaking_change)
```

### Type 3: Database Schema Conflicts
```python
def resolve_schema_conflicts(schema_conflict):
    """Handle database schema migration conflicts."""

    migration_order = determine_migration_order(
        schema_conflict.competing_migrations
    )

    # Create unified migration sequence
    unified_migration = create_unified_migration_sequence(migration_order)

    # Validate migration safety
    if validate_migration_sequence(unified_migration):
        return execute_unified_migration(unified_migration)
    else:
        return require_manual_migration_review(schema_conflict)
```

---

## Performance Optimization

### Parallel Quality Gates
```python
async def optimized_quality_execution(merge_request):
    """Execute quality gates with intelligent parallelization."""

    # Group gates by resource requirements
    cpu_intensive = ["unit_tests", "integration_tests"]
    io_intensive = ["security_scan", "dependency_check"]
    network_dependent = ["deployment_test", "external_api_test"]

    # Execute groups in parallel, serialize within groups
    results = await asyncio.gather(
        execute_gate_group(cpu_intensive, merge_request),
        execute_gate_group(io_intensive, merge_request),
        execute_gate_group(network_dependent, merge_request)
    )

    return aggregate_gate_results(results)
```

### Intelligent Merge Batching
```python
def optimize_merge_batching(queue):
    """Optimize merge order for maximum throughput."""

    # Group compatible changes
    compatible_groups = find_compatible_merge_groups(queue)

    # Optimize within groups
    optimized_queue = []
    for group in compatible_groups:
        ordered_group = optimize_group_order(group)
        optimized_queue.extend(ordered_group)

    return optimized_queue
```

---

## Success Criteria (Phase B)

- ✅ Sequential merge queue with conflict-aware ordering
- ✅ Quality gate framework with configurable requirements
- ✅ Automatic conflict detection and resolution coordination
- ✅ Convoy integration with dependency-aware merging
- ✅ Integration health monitoring with Witness coordination
- ✅ Performance optimization with parallel gate execution

---

## See Also

- `mayor/` — Central coordination and convoy management
- `witness/` — Health monitoring and system oversight
- `deacon/` — Daemon lifecycle and system plugins
- `convoy/` — Work bundling and progress tracking

The Refinery skill transforms chaotic multi-agent code contributions into clean, sequential integration with intelligent conflict resolution and robust quality assurance.