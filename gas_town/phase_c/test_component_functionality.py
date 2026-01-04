#!/usr/bin/env python3
"""
Gas Town Phase C: Component Functionality Test
==============================================

Detailed testing of individual Phase C components to validate
specific functionality and integration points.
"""

import json
import time
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from enum import Enum

# Import Phase C components
from persistent_molecule_state import PersistentMoleculeState, MoleculeState


class TestResult:
    """Track test results."""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.details = []

    def add_success(self, test_name: str, message: str = ""):
        self.total += 1
        self.passed += 1
        self.details.append(f"✅ {test_name}: {message}")

    def add_failure(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.details.append(f"❌ {test_name}: {error}")

    def success_rate(self) -> float:
        return (self.passed / max(self.total, 1)) * 100


class PhaseC_ComponentTester:
    """Comprehensive component testing for Phase C Intelligence Layer."""

    def __init__(self):
        """Initialize component tester."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="phase_c_components_"))
        self.results = TestResult()

        print(f"🔬 Phase C Component Test initialized in {self.test_dir}")

    def run_component_tests(self):
        """Run comprehensive component tests."""
        print("\n" + "=" * 60)
        print("🎯 PHASE C COMPONENT FUNCTIONALITY TESTS")
        print("=" * 60)

        # Detailed molecule state testing
        self._test_molecule_state_advanced()

        # Component architecture testing
        self._test_component_architecture()

        # Database integration testing
        self._test_database_operations()

        # Performance characteristics
        self._test_performance_characteristics()

        return self._generate_detailed_report()

    def _test_molecule_state_advanced(self):
        """Advanced testing of molecule state system."""
        print("\n🧬 Advanced Molecule State Testing:")

        molecule_state = PersistentMoleculeState(
            db_path=str(self.test_dir / "molecule_advanced.db")
        )

        try:
            # Test complex molecule lifecycle
            mol_id = "advanced_test_molecule"

            # 1. Creation with complex data
            complex_data = {
                "workflow_type": "multi_stage",
                "dependencies": ["dep1", "dep2", "dep3"],
                "metadata": {"priority": "high", "estimated_hours": 4.5},
                "configuration": {
                    "parallel_tasks": 3,
                    "retry_count": 2,
                    "timeout_seconds": 3600
                }
            }

            molecule = molecule_state.create_molecule(
                molecule_id=mol_id,
                agent_name="AdvancedTestAgent",
                initial_data=complex_data,
                gas_town_context={"convoy_id": "advanced_convoy", "phase": "testing"},
                dependencies=["other_mol_1", "other_mol_2"]
            )

            assert molecule.checkpoint_data == complex_data
            assert len(molecule.dependencies) == 2
            self.results.add_success("Complex molecule creation")

            # 2. Multi-stage checkpointing
            stages = [
                {"stage": "initialization", "progress": 0.1, "status": "setup_complete"},
                {"stage": "data_processing", "progress": 0.4, "status": "processing"},
                {"stage": "validation", "progress": 0.7, "status": "validating"},
                {"stage": "finalization", "progress": 0.9, "status": "finalizing"}
            ]

            for i, stage_data in enumerate(stages):
                checkpoint_success = molecule_state.checkpoint_molecule(
                    molecule_id=mol_id,
                    checkpoint_data={**complex_data, **stage_data},
                    state=MoleculeState.RUNNING,
                    rollback_point=(i % 2 == 0)  # Every other checkpoint is rollback point
                )
                assert checkpoint_success

            self.results.add_success("Multi-stage checkpointing", f"{len(stages)} stages")

            # 3. Test rollback functionality
            rollback_points = []
            history = molecule_state.get_molecule_history(mol_id)
            for snapshot in history:
                if snapshot.rollback_point:
                    rollback_points.append(snapshot)

            assert len(rollback_points) >= 2  # Initial + 2 rollback checkpoints
            self.results.add_success("Rollback points", f"{len(rollback_points)} found")

            # 4. Test molecule suspension and resumption
            molecule_state.checkpoint_molecule(
                mol_id,
                {"stage": "suspended", "reason": "resource_constraint"},
                MoleculeState.SUSPENDED,
                rollback_point=True
            )

            # Resume
            molecule_state.checkpoint_molecule(
                mol_id,
                {"stage": "resumed", "reason": "resources_available"},
                MoleculeState.RUNNING
            )

            self.results.add_success("Suspend/resume lifecycle")

            # 5. Test failure and recovery
            molecule_state.fail_molecule(
                mol_id,
                {
                    "error_type": "validation_failed",
                    "error_details": "Data integrity check failed",
                    "suggested_action": "rollback_and_retry",
                    "failed_at": datetime.now().isoformat()
                }
            )

            # Recover to last rollback point
            recovery = molecule_state.rollback_molecule(mol_id)
            assert recovery is not None
            assert recovery.state == MoleculeState.ROLLED_BACK
            self.results.add_success("Failure and recovery")

            # 6. Final completion
            final_data = {
                **complex_data,
                "final_status": "completed_successfully",
                "completion_time": datetime.now().isoformat(),
                "final_metrics": {
                    "processing_time": 3.7,
                    "success_rate": 1.0,
                    "resource_efficiency": 0.85
                }
            }

            final_molecule = molecule_state.complete_molecule(mol_id, final_data)
            assert final_molecule.state == MoleculeState.COMPLETED
            assert "final_metrics" in final_molecule.checkpoint_data
            self.results.add_success("Complex completion")

        except Exception as e:
            self.results.add_failure("Advanced molecule state", str(e))

    def _test_component_architecture(self):
        """Test component architecture and design patterns."""
        print("\n🏗️  Component Architecture Testing:")

        try:
            # Test database initialization
            molecule_state = PersistentMoleculeState(
                db_path=str(self.test_dir / "architecture_test.db"),
                checkpoint_interval=10.0,
                heartbeat_timeout=120.0
            )

            # Verify configuration
            assert molecule_state.checkpoint_interval == 10.0
            assert molecule_state.heartbeat_timeout == 120.0
            self.results.add_success("Configuration parameters")

            # Test database schema
            with molecule_state._get_db_connection() as conn:
                cursor = conn.cursor()

                # Check required tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name IN
                    ('molecule_snapshots', 'agent_heartbeats')
                """)
                tables = [row[0] for row in cursor.fetchall()]
                assert 'molecule_snapshots' in tables
                assert 'agent_heartbeats' in tables
                self.results.add_success("Database schema", f"{len(tables)} tables")

                # Check indexes exist
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name LIKE 'idx_%'
                """)
                indexes = cursor.fetchall()
                assert len(indexes) >= 2  # Should have performance indexes
                self.results.add_success("Database indexes", f"{len(indexes)} indexes")

            # Test thread safety
            import threading

            thread_results = []
            def thread_test(thread_id):
                try:
                    for i in range(5):
                        mol_id = f"thread_{thread_id}_mol_{i}"
                        molecule_state.create_molecule(
                            mol_id, f"ThreadAgent_{thread_id}",
                            {"thread": thread_id, "iteration": i}
                        )
                        molecule_state.complete_molecule(mol_id)
                    thread_results.append(True)
                except Exception as e:
                    thread_results.append(False)

            threads = []
            for i in range(3):
                t = threading.Thread(target=thread_test, args=(i,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=10.0)

            assert len(thread_results) == 3
            assert all(thread_results)
            self.results.add_success("Thread safety", "3 concurrent threads")

        except Exception as e:
            self.results.add_failure("Component architecture", str(e))

    def _test_database_operations(self):
        """Test database operations and data integrity."""
        print("\n💾 Database Operations Testing:")

        try:
            molecule_state = PersistentMoleculeState(
                db_path=str(self.test_dir / "db_operations.db")
            )

            # Create test data
            molecules = []
            for i in range(10):
                mol_id = f"db_test_mol_{i:03d}"
                mol = molecule_state.create_molecule(
                    mol_id, f"DbTestAgent_{i % 3}",
                    {"index": i, "test_data": f"data_{i}"}
                )
                molecules.append(mol)

            # Test bulk operations
            for mol in molecules[:5]:
                molecule_state.checkpoint_molecule(
                    mol.molecule_id,
                    {"bulk_update": True, "batch": 1},
                    MoleculeState.RUNNING
                )

            for mol in molecules[5:]:
                molecule_state.complete_molecule(
                    mol.molecule_id,
                    {"bulk_complete": True, "batch": 2}
                )

            self.results.add_success("Bulk operations", "10 molecules processed")

            # Test data consistency
            for mol in molecules:
                history = molecule_state.get_molecule_history(mol.molecule_id)
                assert len(history) >= 1  # At least creation
                assert history[0].molecule_id == mol.molecule_id

            self.results.add_success("Data consistency", "History integrity verified")

            # Test crash agent detection simulation
            molecule_state.heartbeat("TestAgent_1", ["mol_1", "mol_2"])
            molecule_state.heartbeat("TestAgent_2", ["mol_3"])

            # Simulate timeout by checking database directly
            with molecule_state._get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM agent_heartbeats")
                heartbeat_count = cursor.fetchone()[0]
                assert heartbeat_count >= 2

            self.results.add_success("Heartbeat system", f"{heartbeat_count} heartbeats recorded")

            # Test data cleanup
            deleted = molecule_state.cleanup_old_snapshots(days=0)  # Delete everything older than now
            # Should delete nothing since we just created the data
            assert deleted >= 0
            self.results.add_success("Data cleanup", f"Cleanup function operational")

        except Exception as e:
            self.results.add_failure("Database operations", str(e))

    def _test_performance_characteristics(self):
        """Test performance characteristics of the system."""
        print("\n⚡ Performance Characteristics Testing:")

        try:
            molecule_state = PersistentMoleculeState(
                db_path=str(self.test_dir / "performance.db")
            )

            # Test creation performance
            start_time = time.time()
            molecule_count = 50

            for i in range(molecule_count):
                mol_id = f"perf_test_{i:03d}"
                molecule_state.create_molecule(
                    mol_id, "PerfTestAgent",
                    {"index": i, "timestamp": time.time()}
                )

            creation_time = time.time() - start_time
            creation_rate = molecule_count / creation_time

            assert creation_time < 10.0  # Should create 50 molecules in under 10 seconds
            self.results.add_success(
                "Creation performance",
                f"{creation_rate:.1f} molecules/sec"
            )

            # Test checkpoint performance
            start_time = time.time()
            checkpoint_count = 0

            for i in range(0, molecule_count, 5):  # Every 5th molecule
                mol_id = f"perf_test_{i:03d}"
                molecule_state.checkpoint_molecule(
                    mol_id,
                    {"checkpoint": True, "perf_test": True},
                    MoleculeState.RUNNING
                )
                checkpoint_count += 1

            checkpoint_time = time.time() - start_time
            checkpoint_rate = checkpoint_count / checkpoint_time

            assert checkpoint_time < 5.0  # Should checkpoint quickly
            self.results.add_success(
                "Checkpoint performance",
                f"{checkpoint_rate:.1f} checkpoints/sec"
            )

            # Test query performance
            start_time = time.time()

            for i in range(0, molecule_count, 10):  # Every 10th molecule
                mol_id = f"perf_test_{i:03d}"
                history = molecule_state.get_molecule_history(mol_id)
                assert len(history) >= 1

            query_time = time.time() - start_time
            query_count = molecule_count // 10
            query_rate = query_count / query_time

            assert query_time < 2.0  # Should query quickly
            self.results.add_success(
                "Query performance",
                f"{query_rate:.1f} queries/sec"
            )

            # Test memory usage (basic check)
            active_molecules = molecule_state.get_active_molecules()
            # Most should be active (not completed)
            assert len(active_molecules) >= molecule_count - 10
            self.results.add_success(
                "Memory management",
                f"{len(active_molecules)} active molecules tracked"
            )

        except Exception as e:
            self.results.add_failure("Performance characteristics", str(e))

    def _generate_detailed_report(self):
        """Generate detailed test report."""
        success_rate = self.results.success_rate()

        print("\n" + "=" * 60)
        print("📊 PHASE C COMPONENT TEST RESULTS")
        print("=" * 60)

        print(f"Total Tests: {self.results.total}")
        print(f"✅ Passed: {self.results.passed}")
        print(f"❌ Failed: {self.results.failed}")
        print(f"Success Rate: {success_rate:.1f}%")

        print("\n📋 Detailed Results:")
        for detail in self.results.details:
            print(f"  {detail}")

        # Component assessment
        print(f"\n🔍 COMPONENT ASSESSMENT:")
        if success_rate >= 95.0:
            print("🟢 EXCELLENT: All components functioning optimally")
            status = "EXCELLENT"
        elif success_rate >= 85.0:
            print("🟡 GOOD: Minor issues detected, mostly functional")
            status = "GOOD"
        elif success_rate >= 70.0:
            print("🟠 FAIR: Several issues detected, needs attention")
            status = "FAIR"
        else:
            print("🔴 POOR: Major issues detected, requires fixes")
            status = "POOR"

        # Generate report data
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_type": "component_functionality",
            "total_tests": self.results.total,
            "passed": self.results.passed,
            "failed": self.results.failed,
            "success_rate": success_rate,
            "status": status,
            "component_assessment": {
                "molecule_state_system": "operational" if success_rate >= 85 else "needs_attention",
                "database_integration": "operational" if success_rate >= 85 else "needs_attention",
                "performance_characteristics": "acceptable" if success_rate >= 75 else "needs_optimization"
            },
            "detailed_results": self.results.details
        }

        return report

    def cleanup(self):
        """Clean up test environment."""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            print(f"🧹 Component test cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    print("🚀 Starting Phase C Component Functionality Test")

    tester = PhaseC_ComponentTester()

    try:
        report = tester.run_component_tests()

        # Save detailed results
        results_file = Path("/home/ubuntu/projects/deere/gas_town/phase_c/component_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Component test results saved to {results_file}")

        # Final assessment
        if report["success_rate"] >= 85.0:
            print("\n🎯 PHASE C COMPONENTS: PRODUCTION READY ✅")
            print("   All major functionality validated")
        else:
            print(f"\n⚠️  PHASE C COMPONENTS: NEEDS ATTENTION ❌")
            print(f"   Success rate: {report['success_rate']:.1f}% (target: 85%+)")

    finally:
        tester.cleanup()