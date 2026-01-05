#!/usr/bin/env python3
"""
Gas Town Phase C: Basic Integration Test
=======================================

Core functionality test for Phase C Intelligence Layer.
Tests basic integration without external dependencies.
"""

import json
import time
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import Phase C components (basic functionality only)
from persistent_molecule_state import PersistentMoleculeState, MoleculeState


class PhaseC_BasicTester:
    """Basic integration tester for Gas Town Phase C core functionality."""

    def __init__(self):
        """Initialize the basic tester."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="phase_c_basic_test_"))
        self.results = {"passed": 0, "failed": 0, "errors": []}

        # Initialize core component
        self.molecule_state = PersistentMoleculeState(
            db_path=str(self.test_dir / "test_molecule_state.db")
        )

        print(f"🧪 Phase C Basic Test initialized in {self.test_dir}")

    def run_basic_tests(self):
        """Run basic integration tests."""
        print("\n" + "=" * 50)
        print("🎯 PHASE C BASIC INTEGRATION TESTS")
        print("=" * 50)

        # Test molecule state system
        self._test_molecule_operations()
        self._test_crash_recovery()
        self._test_concurrent_molecules()

        # Test file system integration
        self._test_file_persistence()

        # Test error handling
        self._test_error_handling()

        return self._generate_report()

    def _test_molecule_operations(self):
        """Test basic molecule operations."""
        print("  🧬 Testing Molecule Operations...")

        try:
            # Create molecule
            molecule = self.molecule_state.create_molecule(
                molecule_id="test_mol_001",
                agent_name="BasicTestAgent",
                initial_data={"status": "initialized", "progress": 0}
            )
            assert molecule.molecule_id == "test_mol_001"
            print("    ✅ Molecule creation")

            # Checkpoint
            success = self.molecule_state.checkpoint_molecule(
                molecule_id="test_mol_001",
                checkpoint_data={"status": "running", "progress": 50},
                state=MoleculeState.RUNNING,
                rollback_point=True
            )
            assert success
            print("    ✅ Molecule checkpointing")

            # History
            history = self.molecule_state.get_molecule_history("test_mol_001")
            assert len(history) >= 2
            print("    ✅ History retrieval")

            # Complete
            final = self.molecule_state.complete_molecule(
                molecule_id="test_mol_001",
                final_data={"status": "completed", "progress": 100}
            )
            assert final.state == MoleculeState.COMPLETED
            print("    ✅ Molecule completion")

            self.results["passed"] += 1

        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Molecule operations: {e}")
            print(f"    ❌ Molecule operations failed: {e}")

    def _test_crash_recovery(self):
        """Test crash recovery functionality."""
        print("  💥 Testing Crash Recovery...")

        try:
            # Create molecule with checkpoints
            mol_id = "crash_test_mol"
            self.molecule_state.create_molecule(
                molecule_id=mol_id,
                agent_name="CrashTestAgent",
                initial_data={"critical_data": True}
            )

            # Add multiple checkpoints
            self.molecule_state.checkpoint_molecule(
                mol_id, {"phase": "setup", "progress": 0.25},
                MoleculeState.RUNNING, rollback_point=True
            )

            self.molecule_state.checkpoint_molecule(
                mol_id, {"phase": "processing", "progress": 0.75},
                MoleculeState.RUNNING, rollback_point=True
            )

            # Simulate crash
            self.molecule_state.fail_molecule(
                mol_id, {"error": "simulated_crash", "timestamp": datetime.now().isoformat()}
            )
            print("    ✅ Crash simulation")

            # Test recovery
            rollback_point = self.molecule_state.find_rollback_point(mol_id)
            assert rollback_point is not None
            print("    ✅ Rollback point found")

            # Perform rollback
            recovery = self.molecule_state.rollback_molecule(mol_id)
            assert recovery is not None
            assert recovery.state == MoleculeState.ROLLED_BACK
            print("    ✅ Recovery successful")

            self.results["passed"] += 1

        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Crash recovery: {e}")
            print(f"    ❌ Crash recovery failed: {e}")

    def _test_concurrent_molecules(self):
        """Test concurrent molecule operations."""
        print("  ⚡ Testing Concurrent Operations...")

        try:
            import threading

            errors = []
            successes = 0

            def create_molecules(thread_id):
                try:
                    for i in range(3):
                        mol_id = f"concurrent_{thread_id}_{i}"
                        mol = self.molecule_state.create_molecule(
                            molecule_id=mol_id,
                            agent_name=f"Agent_{thread_id}",
                            initial_data={"thread": thread_id, "index": i}
                        )

                        # Quick checkpoint and complete
                        self.molecule_state.checkpoint_molecule(
                            mol_id, {"status": "processing"}, MoleculeState.RUNNING
                        )
                        self.molecule_state.complete_molecule(mol_id, {"status": "done"})

                    nonlocal successes
                    successes += 1

                except Exception as e:
                    errors.append(f"Thread {thread_id}: {e}")

            # Start multiple threads
            threads = []
            for i in range(3):
                t = threading.Thread(target=create_molecules, args=(i,))
                threads.append(t)
                t.start()

            # Wait for completion
            for t in threads:
                t.join(timeout=10.0)

            assert len(errors) == 0, f"Concurrent errors: {errors}"
            assert successes == 3
            print(f"    ✅ {successes} threads completed successfully")

            self.results["passed"] += 1

        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Concurrent operations: {e}")
            print(f"    ❌ Concurrent operations failed: {e}")

    def _test_file_persistence(self):
        """Test file system persistence."""
        print("  💾 Testing File Persistence...")

        try:
            # Create and complete molecule
            mol_id = "persistence_test"
            self.molecule_state.create_molecule(
                mol_id, "PersistenceAgent", {"test": "data"}
            )
            self.molecule_state.complete_molecule(mol_id, {"final": "data"})

            # Verify database file exists and is not empty
            db_file = Path(self.test_dir / "test_molecule_state.db")
            assert db_file.exists()
            assert db_file.stat().st_size > 0
            print("    ✅ Database file created")

            # Create new instance and verify data persisted
            molecule_state_2 = PersistentMoleculeState(
                db_path=str(db_file)
            )

            history = molecule_state_2.get_molecule_history(mol_id)
            assert len(history) > 0
            print("    ✅ Data persisted across instances")

            self.results["passed"] += 1

        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"File persistence: {e}")
            print(f"    ❌ File persistence failed: {e}")

    def _test_error_handling(self):
        """Test error handling and edge cases."""
        print("  🛡️ Testing Error Handling...")

        try:
            # Test invalid operations
            try:
                # Try to checkpoint non-existent molecule
                self.molecule_state.checkpoint_molecule(
                    "nonexistent_mol", {"data": "test"}, MoleculeState.RUNNING
                )
                assert False, "Should have raised exception"
            except ValueError:
                print("    ✅ Invalid checkpoint handled")

            try:
                # Try to complete non-existent molecule
                self.molecule_state.complete_molecule("nonexistent_mol")
                assert False, "Should have raised exception"
            except ValueError:
                print("    ✅ Invalid completion handled")

            # Test empty history
            history = self.molecule_state.get_molecule_history("nonexistent_mol")
            assert len(history) == 0
            print("    ✅ Empty history handled")

            # Test rollback on molecule with no rollback points
            rollback = self.molecule_state.find_rollback_point("nonexistent_mol")
            assert rollback is None
            print("    ✅ No rollback point handled")

            self.results["passed"] += 1

        except Exception as e:
            self.results["failed"] += 1
            self.results["errors"].append(f"Error handling: {e}")
            print(f"    ❌ Error handling test failed: {e}")

    def _generate_report(self):
        """Generate test report."""
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / max(total, 1)) * 100

        print("\n" + "=" * 50)
        print("📊 PHASE C BASIC TEST RESULTS")
        print("=" * 50)

        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"Success Rate: {success_rate:.1f}%")

        if self.results["failed"] == 0:
            print("\n🎉 ALL BASIC TESTS PASSED!")
            print("📦 Phase C Core Components: FUNCTIONAL")
            status = "VALIDATED"
        else:
            print(f"\n⚠️  {self.results['failed']} tests failed")
            for error in self.results["errors"]:
                print(f"   - {error}")
            status = "ISSUES_FOUND"

        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_type": "basic_integration",
            "total_tests": total,
            "passed": self.results["passed"],
            "failed": self.results["failed"],
            "success_rate": success_rate,
            "status": status,
            "errors": self.results["errors"],
            "phase_c_core_functional": self.results["failed"] == 0
        }

        return report

    def cleanup(self):
        """Clean up test environment."""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
            print(f"🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


if __name__ == "__main__":
    print("🚀 Starting Phase C Basic Integration Test")

    tester = PhaseC_BasicTester()

    try:
        report = tester.run_basic_tests()

        # Save results
        results_file = Path("/home/ubuntu/projects/deere/gas_town/phase_c/basic_test_results.json")
        with open(results_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Results saved to {results_file}")

        # Final assessment
        if report["phase_c_core_functional"]:
            print("\n🎯 PHASE C CORE: OPERATIONAL ✅")
        else:
            print("\n⚠️  PHASE C CORE: NEEDS ATTENTION ❌")

    finally:
        tester.cleanup()