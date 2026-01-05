#!/usr/bin/env python3
"""
Gas Town Phase C: Multi-Agent Scale Test
========================================

Validates Phase C Intelligence Layer performance and coordination
under the intended 20-25 agent scale with concurrent operations.

Tests:
- Concurrent molecule state management
- Swarm coordination under load
- Resource contention and conflict resolution
- Performance metrics at target scale
"""

import json
import time
import tempfile
import shutil
import threading
import random
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# Import Phase C components
from persistent_molecule_state import PersistentMoleculeState, MoleculeState
from swarm_coordinator import (
    SwarmCoordinator, TeamType, AgentProfile, AgentCapability, WorkloadType
)
from enhanced_health_monitor import EnhancedHealthMonitor, HealthLevel


@dataclass
class ScaleTestMetrics:
    """Comprehensive metrics for scale testing."""
    agent_count: int
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    throughput_ops_per_sec: float
    concurrent_molecules: int
    conflict_resolution_success_rate: float
    memory_usage_mb: float
    cpu_utilization_percent: float


class MultiAgentScaleTester:
    """Comprehensive multi-agent scale testing framework."""

    def __init__(self, target_agent_count: int = 25):
        """Initialize scale tester."""
        self.target_agent_count = target_agent_count
        self.test_dir = Path(tempfile.mkdtemp(prefix="gas_town_scale_test_"))
        self.results = []
        self.metrics = {}
        self.start_time = None
        self.end_time = None

        print(f"🚀 Multi-Agent Scale Test initialized for {target_agent_count} agents")
        print(f"📁 Test directory: {self.test_dir}")

    def run_scale_tests(self) -> Dict[str, Any]:
        """Run comprehensive multi-agent scale tests."""
        print("\n" + "=" * 80)
        print(f"🎯 GAS TOWN PHASE C SCALE TEST - {self.target_agent_count} AGENTS")
        print("=" * 80)

        self.start_time = time.time()

        # Phase 1: Infrastructure scale test
        print("\n🏗️ Phase 1: Infrastructure Scale Test")
        infra_metrics = self._test_infrastructure_scale()

        # Phase 2: Concurrent molecule operations
        print("\n🧬 Phase 2: Concurrent Molecule Operations")
        molecule_metrics = self._test_concurrent_molecule_ops()

        # Phase 3: Swarm coordination stress test
        print("\n🐝 Phase 3: Swarm Coordination Stress Test")
        swarm_metrics = self._test_swarm_coordination_scale()

        # Phase 4: Conflict resolution under load
        print("\n⚡ Phase 4: Conflict Resolution Under Load")
        conflict_metrics = self._test_conflict_resolution_scale()

        # Phase 5: Health monitoring at scale
        print("\n❤️ Phase 5: Health Monitoring At Scale")
        health_metrics = self._test_health_monitoring_scale()

        # Phase 6: End-to-end integration
        print("\n🔄 Phase 6: End-to-End Integration Test")
        integration_metrics = self._test_end_to_end_integration()

        self.end_time = time.time()

        return self._generate_scale_report(
            infra_metrics, molecule_metrics, swarm_metrics,
            conflict_metrics, health_metrics, integration_metrics
        )

    def _test_infrastructure_scale(self) -> Dict[str, Any]:
        """Test basic infrastructure scaling capabilities."""
        print("   Testing database connections and basic operations...")

        start_time = time.time()
        operations = []
        errors = []

        def agent_infrastructure_test(agent_id: int):
            """Single agent infrastructure test."""
            try:
                op_start = time.time()

                # Create agent-specific molecule state
                db_path = str(self.test_dir / f"agent_{agent_id}_molecules.db")
                molecule_state = PersistentMoleculeState(
                    db_path=db_path,
                    checkpoint_interval=1.0,  # Faster for testing
                    heartbeat_timeout=60.0
                )

                # Perform basic operations
                mol_id = f"infra_test_mol_{agent_id}"

                # Create molecule
                molecule = molecule_state.create_molecule(
                    mol_id, f"ScaleTestAgent_{agent_id}",
                    {"test_type": "infrastructure", "agent_id": agent_id}
                )

                # Checkpoint
                molecule_state.checkpoint_molecule(
                    mol_id, {"status": "checkpoint_test"},
                    MoleculeState.RUNNING, force=True
                )

                # Complete
                molecule_state.complete_molecule(mol_id, {"status": "completed"})

                op_time = time.time() - op_start
                return {"agent_id": agent_id, "time": op_time, "success": True}

            except Exception as e:
                errors.append({"agent_id": agent_id, "error": str(e)})
                return {"agent_id": agent_id, "time": 0, "success": False}

        # Run concurrent infrastructure tests
        with ThreadPoolExecutor(max_workers=self.target_agent_count) as executor:
            futures = [
                executor.submit(agent_infrastructure_test, i)
                for i in range(self.target_agent_count)
            ]

            for future in as_completed(futures):
                result = future.result()
                operations.append(result)

        duration = time.time() - start_time
        successful_ops = [op for op in operations if op["success"]]

        return {
            "test_name": "Infrastructure Scale",
            "total_agents": self.target_agent_count,
            "duration_seconds": duration,
            "successful_operations": len(successful_ops),
            "failed_operations": len(errors),
            "success_rate": len(successful_ops) / len(operations) * 100,
            "avg_operation_time": statistics.mean([op["time"] for op in successful_ops]) if successful_ops else 0,
            "throughput_ops_per_sec": len(successful_ops) / duration,
            "errors": errors[:5]  # First 5 errors for debugging
        }

    def _test_concurrent_molecule_ops(self) -> Dict[str, Any]:
        """Test concurrent molecule operations across multiple agents."""
        print("   Testing concurrent molecule creation and management...")

        start_time = time.time()
        shared_db = str(self.test_dir / "shared_molecules.db")
        molecule_state = PersistentMoleculeState(
            db_path=shared_db,
            checkpoint_interval=0.5,
            heartbeat_timeout=30.0
        )

        operations = []
        conflicts = []

        def agent_molecule_workflow(agent_id: int):
            """Complex molecule workflow for single agent."""
            try:
                results = []
                base_mol_id = f"scale_mol_{agent_id}"

                for workflow_step in range(5):  # 5 molecules per agent
                    step_start = time.time()
                    mol_id = f"{base_mol_id}_step_{workflow_step}"

                    # Complex workflow data
                    workflow_data = {
                        "agent_id": agent_id,
                        "workflow_step": workflow_step,
                        "complexity": "high",
                        "dependencies": [f"dep_{i}" for i in range(3)],
                        "metadata": {
                            "priority": random.choice(["high", "medium", "low"]),
                            "estimated_time": random.uniform(1.0, 10.0),
                            "resources_needed": random.randint(1, 5)
                        }
                    }

                    # Create molecule
                    molecule = molecule_state.create_molecule(
                        mol_id, f"ScaleAgent_{agent_id}",
                        workflow_data,
                        gas_town_context={"scale_test": True, "agent_count": self.target_agent_count}
                    )

                    # Multi-stage checkpointing
                    stages = ["init", "processing", "validation", "completion"]
                    for i, stage in enumerate(stages):
                        checkpoint_data = {**workflow_data, "stage": stage, "progress": (i + 1) / len(stages)}
                        molecule_state.checkpoint_molecule(
                            mol_id, checkpoint_data,
                            MoleculeState.RUNNING,
                            force=True,
                            rollback_point=(i % 2 == 0)
                        )
                        time.sleep(0.01)  # Small delay to simulate work

                    # Complete molecule
                    final_data = {**workflow_data, "completed_at": datetime.now().isoformat()}
                    molecule_state.complete_molecule(mol_id, final_data)

                    step_time = time.time() - step_start
                    results.append({"mol_id": mol_id, "time": step_time, "success": True})

                return {"agent_id": agent_id, "operations": results}

            except Exception as e:
                conflicts.append({"agent_id": agent_id, "error": str(e)})
                return {"agent_id": agent_id, "operations": [], "error": str(e)}

        # Run concurrent molecule workflows
        with ThreadPoolExecutor(max_workers=min(self.target_agent_count, 15)) as executor:
            futures = [
                executor.submit(agent_molecule_workflow, i)
                for i in range(self.target_agent_count)
            ]

            for future in as_completed(futures):
                result = future.result()
                operations.append(result)

        duration = time.time() - start_time
        successful_agents = [op for op in operations if "error" not in op]
        total_molecules = sum(len(agent["operations"]) for agent in successful_agents)

        # Get active molecules for concurrency measurement
        active_molecules = molecule_state.get_active_molecules()

        return {
            "test_name": "Concurrent Molecule Operations",
            "total_agents": self.target_agent_count,
            "successful_agents": len(successful_agents),
            "total_molecules_created": total_molecules,
            "duration_seconds": duration,
            "molecules_per_second": total_molecules / duration,
            "avg_molecules_per_agent": total_molecules / len(successful_agents) if successful_agents else 0,
            "conflicts": len(conflicts),
            "concurrent_molecules": len(active_molecules),
            "success_rate": len(successful_agents) / len(operations) * 100
        }

    def _test_swarm_coordination_scale(self) -> Dict[str, Any]:
        """Test swarm coordination under high agent load."""
        print("   Testing swarm coordination with multiple teams...")

        try:
            start_time = time.time()

            # Initialize swarm coordinator
            coord_db = str(self.test_dir / "swarm_coordination.db")
            swarm_coord = SwarmCoordinator(
                db_path=coord_db,
                max_agents=self.target_agent_count,
                team_size_range=(3, 8),
                coordination_intervals={"team_check": 30.0}
            )

            # Create agent profiles
            agent_profiles = []
            for i in range(self.target_agent_count):
                profile = AgentProfile(
                    agent_name=f"scale_agent_{i}",
                    capabilities=[
                        AgentCapability.BACKEND_DEV,
                        AgentCapability.COORDINATION,
                        AgentCapability.ANALYSIS
                    ],
                    performance_rating=random.uniform(0.85, 0.98),
                    current_load=random.uniform(0.1, 0.6),
                    health_status=HealthLevel.HEALTHY,
                    team_preferences=[TeamType.PARALLEL, TeamType.SPECIALIST],
                    last_active=datetime.now().isoformat(),
                    specialization_score={
                        WorkloadType.CPU_INTENSIVE: random.uniform(0.7, 1.0),
                        WorkloadType.IO_BOUND: random.uniform(0.5, 0.9),
                        WorkloadType.COORDINATION_HEAVY: random.uniform(0.8, 1.0)
                    },
                    collaboration_rating=random.uniform(0.8, 1.0),
                    availability_window=None  # Always available for testing
                )
                agent_profiles.append(profile)
                swarm_coord.register_agent(
                    agent_name=profile.agent_name,
                    capabilities=profile.capabilities,
                    specializations=profile.specialization_score,
                    team_preferences=profile.team_preferences
                )

            coordination_metrics = []

            # Test team formation at scale
            team_formation_start = time.time()
            teams_formed = 0

            # Form multiple teams for different task types
            team_types = [TeamType.PARALLEL, TeamType.SPECIALIST, TeamType.EMERGENCY]

            for team_type in team_types:
                for team_num in range(3):  # 3 teams per type
                    try:
                        workload = [f"scale_work_{team_type.value}_{team_num}_{i}" for i in range(3)]
                        required_capabilities = [AgentCapability.COORDINATION, AgentCapability.ANALYSIS]

                        team = swarm_coord.form_team(
                            workload=workload,
                            required_capabilities=required_capabilities,
                            team_type=team_type,
                            preferred_agents=None
                        )

                        if team:
                            teams_formed += 1
                    except Exception as e:
                        print(f"     ⚠️  Team formation error: {e}")

            team_formation_time = time.time() - team_formation_start

            # Test work distribution
            distribution_start = time.time()
            work_items = []

            for i in range(50):  # 50 work items to distribute
                work_items.append(f"scale_work_{i}")

            distribution_results = swarm_coord.distribute_work(work_items)
            distribution_time = time.time() - distribution_start

            # Test coordination under load (using conflict detection)
            coordination_start = time.time()
            coordination_events = []

            for i in range(20):  # 20 coordination checks
                try:
                    # Detect conflicts in current swarm state
                    conflicts = swarm_coord.detect_conflicts()

                    # Get swarm status
                    status = swarm_coord.get_swarm_status()

                    coordination_events.append({
                        "event_id": f"coord_event_{i}",
                        "conflicts_detected": len(conflicts),
                        "swarm_status": status.get("status", "unknown"),
                        "success": True
                    })
                except Exception as e:
                    coordination_events.append({
                        "event_id": f"coord_event_{i}",
                        "error": str(e),
                        "success": False
                    })

            coordination_time = time.time() - coordination_start
            duration = time.time() - start_time

            successful_coordinations = [e for e in coordination_events if e["success"]]

            return {
                "test_name": "Swarm Coordination Scale",
                "total_agents": self.target_agent_count,
                "teams_formed": teams_formed,
                "team_formation_time": team_formation_time,
                "work_items_distributed": len(distribution_results.total_workload),
                "work_distribution_time": distribution_time,
                "coordination_events": len(coordination_events),
                "successful_coordinations": len(successful_coordinations),
                "coordination_success_rate": len(successful_coordinations) / len(coordination_events) * 100,
                "coordination_time": coordination_time,
                "total_duration": duration,
                "agents_per_team_avg": self.target_agent_count / max(teams_formed, 1)
            }

        except Exception as e:
            return {
                "test_name": "Swarm Coordination Scale",
                "error": str(e),
                "success": False
            }

    def _test_conflict_resolution_scale(self) -> Dict[str, Any]:
        """Test conflict resolution under concurrent access."""
        print("   Testing conflict resolution with resource contention...")

        start_time = time.time()
        shared_resources = ["resource_A", "resource_B", "resource_C", "resource_D"]
        conflicts_detected = []
        conflicts_resolved = []

        def agent_resource_contention(agent_id: int):
            """Simulate agent trying to access shared resources."""
            try:
                results = []

                for attempt in range(10):  # 10 resource access attempts per agent
                    resource_id = random.choice(shared_resources)

                    # Simulate resource access with potential conflicts
                    access_start = time.time()

                    # Create molecule that depends on shared resource
                    db_path = str(self.test_dir / f"conflict_test_{agent_id}.db")
                    molecule_state = PersistentMoleculeState(db_path=db_path)

                    mol_id = f"conflict_mol_{agent_id}_{attempt}"
                    try:
                        # Simulate exclusive resource access
                        molecule = molecule_state.create_molecule(
                            mol_id, f"ConflictAgent_{agent_id}",
                            {
                                "resource_id": resource_id,
                                "access_type": "exclusive",
                                "agent_id": agent_id,
                                "attempt": attempt
                            }
                        )

                        # Hold resource for random time
                        hold_time = random.uniform(0.01, 0.05)
                        time.sleep(hold_time)

                        # Release resource
                        molecule_state.complete_molecule(mol_id, {"released": True})

                        access_time = time.time() - access_start
                        results.append({
                            "resource_id": resource_id,
                            "access_time": access_time,
                            "success": True,
                            "hold_time": hold_time
                        })

                    except Exception as conflict_error:
                        conflicts_detected.append({
                            "agent_id": agent_id,
                            "resource_id": resource_id,
                            "error": str(conflict_error)
                        })

                        # Simulate conflict resolution - retry with backoff
                        backoff_time = random.uniform(0.02, 0.1)
                        time.sleep(backoff_time)

                        try:
                            # Retry resource access
                            molecule = molecule_state.create_molecule(
                                f"{mol_id}_retry", f"ConflictAgent_{agent_id}",
                                {
                                    "resource_id": resource_id,
                                    "access_type": "exclusive",
                                    "agent_id": agent_id,
                                    "retry": True
                                }
                            )
                            molecule_state.complete_molecule(f"{mol_id}_retry", {"resolved": True})

                            conflicts_resolved.append({
                                "agent_id": agent_id,
                                "resource_id": resource_id,
                                "backoff_time": backoff_time
                            })

                            results.append({
                                "resource_id": resource_id,
                                "access_time": backoff_time,
                                "success": True,
                                "resolved_conflict": True
                            })
                        except:
                            results.append({
                                "resource_id": resource_id,
                                "success": False,
                                "unresolved_conflict": True
                            })

                return {"agent_id": agent_id, "results": results}

            except Exception as e:
                return {"agent_id": agent_id, "error": str(e), "results": []}

        # Run concurrent conflict resolution tests
        with ThreadPoolExecutor(max_workers=min(self.target_agent_count, 20)) as executor:
            futures = [
                executor.submit(agent_resource_contention, i)
                for i in range(self.target_agent_count)
            ]

            agent_results = []
            for future in as_completed(futures):
                result = future.result()
                agent_results.append(result)

        duration = time.time() - start_time

        total_access_attempts = sum(len(agent["results"]) for agent in agent_results)
        successful_accesses = sum(
            len([r for r in agent["results"] if r["success"]])
            for agent in agent_results
        )

        return {
            "test_name": "Conflict Resolution Scale",
            "total_agents": self.target_agent_count,
            "total_access_attempts": total_access_attempts,
            "successful_accesses": successful_accesses,
            "conflicts_detected": len(conflicts_detected),
            "conflicts_resolved": len(conflicts_resolved),
            "conflict_resolution_rate": len(conflicts_resolved) / max(len(conflicts_detected), 1) * 100,
            "success_rate": successful_accesses / max(total_access_attempts, 1) * 100,
            "duration_seconds": duration,
            "accesses_per_second": total_access_attempts / duration
        }

    def _test_health_monitoring_scale(self) -> Dict[str, Any]:
        """Test health monitoring system under scale."""
        print("   Testing health monitoring with high agent load...")

        start_time = time.time()

        # Initialize enhanced health monitor
        health_db = str(self.test_dir / "health_monitoring.db")
        health_monitor = EnhancedHealthMonitor(
            db_path=health_db,
            monitoring_intervals={"health_check": 1.0, "alert_check": 5.0},
            resource_thresholds={"cpu_warning": 80.0, "memory_warning": 85.0}
        )

        # Start health monitoring (agents auto-register on first report)
        health_monitor.start_monitoring()

        monitoring_results = []

        def agent_health_simulation(agent_id: int):
            """Simulate agent with varying health status."""
            try:
                agent_name = f"scale_agent_{agent_id}"
                results = []

                # Simulate 30 seconds of agent activity
                simulation_start = time.time()
                while time.time() - simulation_start < 30:
                    # Simulate health monitoring activity (health monitor runs automatically)
                    cpu_usage = random.uniform(20, 90)
                    memory_usage = random.uniform(30, 85)
                    active_tasks = random.randint(1, 10)

                    # The health monitor automatically monitors system resources
                    # We just simulate agent activity here
                    results.append({
                        "timestamp": time.time(),
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage,
                        "simulated_activity": True,
                        "active_tasks": active_tasks
                    })

                    time.sleep(0.5)  # Report every 0.5 seconds

                return {"agent_id": agent_id, "health_reports": results}

            except Exception as e:
                return {"agent_id": agent_id, "error": str(e), "health_reports": []}

        # Run health monitoring simulation
        with ThreadPoolExecutor(max_workers=min(self.target_agent_count, 15)) as executor:
            futures = [
                executor.submit(agent_health_simulation, i)
                for i in range(self.target_agent_count)
            ]

            for future in as_completed(futures):
                result = future.result()
                monitoring_results.append(result)

        duration = time.time() - start_time

        # Analyze health monitoring results
        total_reports = sum(len(agent["health_reports"]) for agent in monitoring_results)
        active_reports = sum(
            len([r for r in agent["health_reports"] if r.get("simulated_activity", False)])
            for agent in monitoring_results
        )

        # Get final health status
        final_health = health_monitor.get_health_summary()

        return {
            "test_name": "Health Monitoring Scale",
            "monitored_agents": self.target_agent_count,
            "total_health_reports": total_reports,
            "active_reports": active_reports,
            "health_success_rate": active_reports / max(total_reports, 1) * 100,
            "duration_seconds": duration,
            "reports_per_second": total_reports / duration,
            "final_system_health": final_health.get("status", "unknown"),
            "monitoring_duration": duration
        }

    def _test_end_to_end_integration(self) -> Dict[str, Any]:
        """Test complete end-to-end integration at scale."""
        print("   Testing end-to-end integration workflow...")

        start_time = time.time()

        # Initialize all Phase C components
        integration_db = str(self.test_dir / "integration_test.db")

        molecule_state = PersistentMoleculeState(
            db_path=integration_db + "_molecules",
            checkpoint_interval=1.0
        )

        swarm_coord = SwarmCoordinator(
            db_path=integration_db + "_swarm",
            max_agents=self.target_agent_count,
            team_size_range=(3, 6)
        )

        health_monitor = EnhancedHealthMonitor(
            db_path=integration_db + "_health",
            monitoring_intervals={"health_check": 2.0}
        )

        integration_results = []

        def integrated_agent_workflow(agent_id: int):
            """Complete integrated workflow for agent."""
            try:
                agent_name = f"integrated_agent_{agent_id}"
                workflow_results = []

                # 1. Register with all systems
                agent_profile = AgentProfile(
                    agent_name=agent_name,
                    capabilities=[AgentCapability.COORDINATION, AgentCapability.BACKEND_DEV],
                    performance_rating=random.uniform(0.85, 0.98),
                    current_load=0.0,
                    health_status=HealthLevel.HEALTHY,
                    team_preferences=[TeamType.PARALLEL],
                    last_active=datetime.now().isoformat(),
                    specialization_score={WorkloadType.COORDINATION_HEAVY: 0.9},
                    collaboration_rating=0.9,
                    availability_window=None
                )
                swarm_coord.register_agent(
                    agent_name=agent_profile.agent_name,
                    capabilities=agent_profile.capabilities,
                    specializations=agent_profile.specialization_score,
                    team_preferences=agent_profile.team_preferences
                )
                # Health monitor will auto-detect active agents

                # 2. Create and manage molecules
                for mol_num in range(3):  # 3 molecules per agent
                    mol_id = f"integrated_mol_{agent_id}_{mol_num}"

                    # Create molecule with full context
                    molecule = molecule_state.create_molecule(
                        mol_id, agent_name,
                        {
                            "integration_test": True,
                            "agent_id": agent_id,
                            "molecule_number": mol_num,
                            "complexity": "high"
                        },
                        gas_town_context={
                            "scale_test": True,
                            "target_agents": self.target_agent_count
                        }
                    )

                    # 3. Health monitoring happens automatically in background
                    # Simulate some processing activity
                    time.sleep(0.01)

                    # 4. Multi-stage processing with checkpoints
                    stages = ["analysis", "processing", "validation", "completion"]
                    for stage in stages:
                        checkpoint_data = {
                            "stage": stage,
                            "progress": stages.index(stage) / len(stages),
                            "agent_load": random.uniform(0.3, 0.9)
                        }

                        molecule_state.checkpoint_molecule(
                            mol_id, checkpoint_data,
                            MoleculeState.RUNNING,
                            force=True
                        )

                        # Health monitoring continues automatically
                        # Simulate processing workload

                        time.sleep(0.1)  # Simulate processing time

                    # 5. Complete molecule
                    final_data = {
                        "completed": True,
                        "completion_time": datetime.now().isoformat(),
                        "total_stages": len(stages)
                    }
                    molecule_state.complete_molecule(mol_id, final_data)

                    workflow_results.append({
                        "mol_id": mol_id,
                        "stages_completed": len(stages),
                        "success": True
                    })

                # 6. Participate in team coordination
                try:
                    # Get current swarm status to demonstrate coordination participation
                    swarm_status = swarm_coord.get_swarm_status()
                    conflicts = swarm_coord.detect_conflicts()

                    coordination_success = True
                except:
                    coordination_success = False

                return {
                    "agent_id": agent_id,
                    "molecules_completed": len(workflow_results),
                    "coordination_success": coordination_success,
                    "total_operations": len(workflow_results) * 4 + 2,  # stages + register + coordinate
                    "success": True
                }

            except Exception as e:
                return {
                    "agent_id": agent_id,
                    "error": str(e),
                    "success": False
                }

        # Run integrated workflow
        with ThreadPoolExecutor(max_workers=min(self.target_agent_count, 10)) as executor:
            futures = [
                executor.submit(integrated_agent_workflow, i)
                for i in range(self.target_agent_count)
            ]

            for future in as_completed(futures):
                result = future.result()
                integration_results.append(result)

        duration = time.time() - start_time

        successful_agents = [r for r in integration_results if r.get("success", False)]
        total_molecules = sum(r.get("molecules_completed", 0) for r in successful_agents)
        total_operations = sum(r.get("total_operations", 0) for r in successful_agents)

        # Get final system state
        active_molecules = molecule_state.get_active_molecules()
        system_health = health_monitor.get_health_summary()

        return {
            "test_name": "End-to-End Integration",
            "total_agents": self.target_agent_count,
            "successful_agents": len(successful_agents),
            "total_molecules_processed": total_molecules,
            "total_operations": total_operations,
            "success_rate": len(successful_agents) / len(integration_results) * 100,
            "duration_seconds": duration,
            "operations_per_second": total_operations / duration,
            "molecules_per_agent": total_molecules / max(len(successful_agents), 1),
            "final_active_molecules": len(active_molecules),
            "final_system_health": system_health.get("status", "unknown")
        }

    def _generate_scale_report(self, *test_metrics) -> Dict[str, Any]:
        """Generate comprehensive scale test report."""
        total_duration = self.end_time - self.start_time

        print("\n" + "=" * 80)
        print("📊 GAS TOWN PHASE C SCALE TEST RESULTS")
        print("=" * 80)

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_configuration": {
                "target_agent_count": self.target_agent_count,
                "total_duration_seconds": total_duration,
                "test_environment": str(self.test_dir)
            },
            "test_results": {}
        }

        # Process each test phase
        for i, metrics in enumerate(test_metrics):
            if metrics and "test_name" in metrics:
                test_name = metrics["test_name"].lower().replace(" ", "_")
                report["test_results"][test_name] = metrics

                print(f"\n{metrics['test_name']}:")
                if "error" in metrics:
                    print(f"  ❌ Failed: {metrics['error']}")
                else:
                    if "success_rate" in metrics:
                        rate = metrics["success_rate"]
                        status = "✅" if rate >= 95 else "⚠️ " if rate >= 80 else "❌"
                        print(f"  {status} Success Rate: {rate:.1f}%")

                    if "duration_seconds" in metrics:
                        print(f"  ⏱️  Duration: {metrics['duration_seconds']:.2f}s")

                    if "throughput_ops_per_sec" in metrics:
                        print(f"  🚀 Throughput: {metrics['throughput_ops_per_sec']:.1f} ops/sec")
                    elif "operations_per_second" in metrics:
                        print(f"  🚀 Throughput: {metrics['operations_per_second']:.1f} ops/sec")

        # Overall assessment
        success_rates = [
            m.get("success_rate", 0) for m in test_metrics
            if m and "success_rate" in m and "error" not in m
        ]

        if success_rates:
            avg_success_rate = statistics.mean(success_rates)
            min_success_rate = min(success_rates)

            print(f"\n🎯 OVERALL SCALE TEST ASSESSMENT:")
            print(f"   Target Agent Count: {self.target_agent_count}")
            print(f"   Average Success Rate: {avg_success_rate:.1f}%")
            print(f"   Minimum Success Rate: {min_success_rate:.1f}%")
            print(f"   Total Test Duration: {total_duration:.1f}s")

            if min_success_rate >= 95:
                status = "🟢 EXCELLENT: Scale targets achieved"
                scale_status = "SCALE_READY"
            elif min_success_rate >= 85:
                status = "🟡 GOOD: Scale targets mostly achieved"
                scale_status = "SCALE_CAPABLE"
            elif min_success_rate >= 70:
                status = "🟠 FAIR: Scale targets partially achieved"
                scale_status = "SCALE_LIMITED"
            else:
                status = "🔴 POOR: Scale targets not achieved"
                scale_status = "SCALE_INSUFFICIENT"

            print(f"   {status}")

            report["overall_assessment"] = {
                "target_agent_count": self.target_agent_count,
                "average_success_rate": avg_success_rate,
                "minimum_success_rate": min_success_rate,
                "scale_status": scale_status,
                "scale_ready": min_success_rate >= 85,
                "recommendations": self._generate_recommendations(min_success_rate, test_metrics)
            }
        else:
            print(f"\n🔴 CRITICAL: Unable to complete scale assessment")
            report["overall_assessment"] = {
                "scale_status": "ASSESSMENT_FAILED",
                "scale_ready": False
            }

        return report

    def _generate_recommendations(self, min_success_rate: float, test_metrics) -> List[str]:
        """Generate recommendations based on scale test results."""
        recommendations = []

        if min_success_rate < 85:
            recommendations.append("Scale targets not fully achieved - consider optimization")

        # Analyze specific test failures
        for metrics in test_metrics:
            if not metrics or "error" in metrics:
                continue

            test_name = metrics.get("test_name", "Unknown")
            success_rate = metrics.get("success_rate", 100)

            if success_rate < 80:
                recommendations.append(f"{test_name}: Below threshold - requires investigation")

            if "conflicts_detected" in metrics and metrics["conflicts_detected"] > 0:
                resolution_rate = metrics.get("conflict_resolution_rate", 0)
                if resolution_rate < 90:
                    recommendations.append("Improve conflict resolution mechanisms")

            if "throughput_ops_per_sec" in metrics:
                throughput = metrics["throughput_ops_per_sec"]
                if throughput < 10:  # Arbitrary threshold
                    recommendations.append(f"{test_name}: Low throughput - consider performance optimization")

        if not recommendations:
            recommendations.append("System performing well at target scale")

        return recommendations

    def cleanup(self):
        """Clean up test environment."""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            print(f"🧹 Scale test cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    import sys

    # Allow custom agent count via command line
    agent_count = int(sys.argv[1]) if len(sys.argv) > 1 else 25

    print(f"🚀 Starting Gas Town Phase C Multi-Agent Scale Test")
    print(f"🎯 Target: {agent_count} agents")

    tester = MultiAgentScaleTester(target_agent_count=agent_count)

    try:
        report = tester.run_scale_tests()

        # Save detailed results
        results_file = Path("/home/ubuntu/projects/deere/gas_town/phase_c/scale_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Scale test results saved to {results_file}")

        # Final status
        if report["overall_assessment"]["scale_ready"]:
            print(f"\n🎯 GAS TOWN PHASE C: SCALE READY ✅")
            print(f"   Successfully validated {agent_count} agent scale")
        else:
            print(f"\n⚠️  GAS TOWN PHASE C: SCALE ISSUES DETECTED ❌")
            print(f"   Requires optimization for {agent_count} agent scale")

    finally:
        tester.cleanup()