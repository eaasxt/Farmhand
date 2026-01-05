#!/usr/bin/env python3
"""
Debug the Advanced Molecule State Test Failure
==============================================

Isolate and debug the specific test that's failing in the component functionality tests.
"""

import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path

from persistent_molecule_state import PersistentMoleculeState, MoleculeState


def debug_advanced_molecule_test():
    """Debug the advanced molecule state test that's failing."""
    print("🔍 Debugging Advanced Molecule State Test Failure")

    test_dir = Path(tempfile.mkdtemp(prefix="debug_molecule_"))

    try:
        molecule_state = PersistentMoleculeState(
            db_path=str(test_dir / "debug_molecule.db")
        )

        print("✅ PersistentMoleculeState initialized")

        # Test complex molecule lifecycle (this is where the failure likely occurs)
        mol_id = "advanced_test_molecule"

        print(f"🧬 Creating complex molecule: {mol_id}")

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

        print(f"✅ Molecule created: {molecule.molecule_id}")

        # Verify creation data
        assert molecule.checkpoint_data == complex_data, f"Expected {complex_data}, got {molecule.checkpoint_data}"
        print("✅ Checkpoint data verified")

        assert len(molecule.dependencies) == 2, f"Expected 2 dependencies, got {len(molecule.dependencies)}"
        print("✅ Dependencies verified")

        # 2. Multi-stage checkpointing
        stages = [
            {"stage": "initialization", "progress": 0.1, "status": "setup_complete"},
            {"stage": "data_processing", "progress": 0.4, "status": "processing"},
            {"stage": "validation", "progress": 0.7, "status": "validating"},
            {"stage": "finalization", "progress": 0.9, "status": "finalizing"}
        ]

        print(f"📊 Testing {len(stages)} checkpoint stages...")

        for i, stage_data in enumerate(stages):
            print(f"   Stage {i+1}: {stage_data['stage']}")

            try:
                checkpoint_success = molecule_state.checkpoint_molecule(
                    molecule_id=mol_id,
                    checkpoint_data={**complex_data, **stage_data},
                    state=MoleculeState.RUNNING,
                    force=True,  # Skip checkpoint interval for testing
                    rollback_point=(i % 2 == 0)  # Every other checkpoint is rollback point
                )

                if not checkpoint_success:
                    print(f"❌ Checkpoint failed for stage {i+1}: {stage_data['stage']}")
                    return False
                else:
                    print(f"   ✅ Stage {i+1} checkpointed successfully")

            except Exception as e:
                print(f"❌ Exception during checkpoint {i+1}: {e}")
                return False

        print("✅ Multi-stage checkpointing completed")

        # 3. Test rollback functionality
        print("🔄 Testing rollback functionality...")

        try:
            rollback_points = []
            history = molecule_state.get_molecule_history(mol_id)
            print(f"   Retrieved history with {len(history)} entries")

            for snapshot in history:
                if snapshot.rollback_point:
                    rollback_points.append(snapshot)
                    print(f"   Found rollback point: {snapshot.timestamp}")

            expected_rollback_points = 1 + 2  # Initial + 2 rollback checkpoints
            if len(rollback_points) < expected_rollback_points:
                print(f"❌ Expected at least {expected_rollback_points} rollback points, found {len(rollback_points)}")
                return False
            else:
                print(f"✅ Found {len(rollback_points)} rollback points")

        except Exception as e:
            print(f"❌ Exception during rollback point check: {e}")
            return False

        # 4. Test molecule suspension and resumption
        print("⏸️ Testing suspension and resumption...")

        try:
            # Suspend
            suspend_success = molecule_state.checkpoint_molecule(
                mol_id,
                {"stage": "suspended", "reason": "resource_constraint"},
                MoleculeState.SUSPENDED,
                force=True,  # Skip checkpoint interval for testing
                rollback_point=True
            )

            if not suspend_success:
                print("❌ Suspension checkpoint failed")
                return False

            print("   ✅ Molecule suspended")

            # Resume
            resume_success = molecule_state.checkpoint_molecule(
                mol_id,
                {"stage": "resumed", "reason": "resources_available"},
                MoleculeState.RUNNING,
                force=True  # Skip checkpoint interval for testing
            )

            if not resume_success:
                print("❌ Resume checkpoint failed")
                return False

            print("   ✅ Molecule resumed")

        except Exception as e:
            print(f"❌ Exception during suspension/resumption: {e}")
            return False

        # 5. Test failure and recovery
        print("💥 Testing failure and recovery...")

        try:
            failure_result = molecule_state.fail_molecule(
                mol_id,
                {
                    "error_type": "validation_failed",
                    "error_details": "Data integrity check failed",
                    "suggested_action": "rollback_and_retry",
                    "failed_at": datetime.now().isoformat()
                }
            )

            if failure_result.state != MoleculeState.FAILED:
                print(f"❌ Expected FAILED state, got {failure_result.state}")
                return False

            print("   ✅ Molecule failure recorded")

            # Recover to last rollback point
            recovery = molecule_state.rollback_molecule(mol_id)
            if recovery is None:
                print("❌ Rollback returned None")
                return False

            if recovery.state != MoleculeState.ROLLED_BACK:
                print(f"❌ Expected ROLLED_BACK state, got {recovery.state}")
                return False

            print("   ✅ Recovery successful")

        except Exception as e:
            print(f"❌ Exception during failure/recovery: {e}")
            return False

        # 6. Final completion
        print("🏁 Testing final completion...")

        try:
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

            if final_molecule.state != MoleculeState.COMPLETED:
                print(f"❌ Expected COMPLETED state, got {final_molecule.state}")
                return False

            if "final_metrics" not in final_molecule.checkpoint_data:
                print("❌ Final metrics not found in checkpoint data")
                return False

            print("   ✅ Completion successful")

        except Exception as e:
            print(f"❌ Exception during completion: {e}")
            return False

        print("🎉 All advanced molecule state tests passed!")
        return True

    except Exception as e:
        print(f"❌ Critical error in advanced molecule test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            if test_dir.exists():
                shutil.rmtree(test_dir)
        except:
            pass


if __name__ == "__main__":
    success = debug_advanced_molecule_test()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Advanced molecule state test")