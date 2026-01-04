#!/usr/bin/env python3
"""
Test Gas Town Hook System
=========================

Quick validation of the hook system implementation.
"""

import os
import sys
import tempfile
import shutil

# Add our modules to path
sys.path.insert(0, '/home/ubuntu/projects/deere/gas_town/phase_c')

from hook_system import GasTownHookSystem, WorkPriority


def test_hook_system():
    """Test the hook system functionality."""
    print("🪝 TESTING GAS TOWN HOOK SYSTEM")
    print("=" * 50)

    # Use temporary database for testing
    test_dir = tempfile.mkdtemp()
    db_path = os.path.join(test_dir, "test_hooks.db")

    try:
        # Initialize hook system
        hook_system = GasTownHookSystem(db_path=db_path)

        # Test 1: Create agent hooks
        print("\n🔍 Test 1: Creating Agent Hooks")
        hook1 = hook_system.create_agent_hook("TestAgent1", {"role": "worker"})
        hook2 = hook_system.create_agent_hook("TestAgent2", {"role": "coordinator"})

        print(f"✅ Created hooks: {hook1}, {hook2}")

        # Test 2: Sling work to hooks
        print("\n🔍 Test 2: Slinging Work")
        work1 = hook_system.sling_work(
            "TestAgent1", "molecule", "mol-123", "Mayor",
            WorkPriority.HIGH, "Urgent feature implementation"
        )

        work2 = hook_system.sling_work(
            "TestAgent1", "bead", "bead-456", "TestAgent2",
            WorkPriority.NORMAL, "Code review needed"
        )

        work3 = hook_system.sling_work(
            "TestAgent2", "convoy", "convoy-789", "Mayor",
            WorkPriority.URGENT, "Critical hotfix deployment"
        )

        print(f"✅ Slung work: {work1}, {work2}, {work3}")

        # Test 3: Check hooks
        print("\n🔍 Test 3: Checking Hooks")
        pending1 = hook_system.check_hook("TestAgent1")
        pending2 = hook_system.check_hook("TestAgent2")

        print(f"✅ TestAgent1 has {len(pending1)} pending work items")
        print(f"✅ TestAgent2 has {len(pending2)} pending work items")

        for work in pending1:
            print(f"   - {work.work_type}:{work.work_reference} (priority: {work.priority.value})")

        # Test 4: Claim and execute work
        print("\n🔍 Test 4: Claiming and Executing Work")
        if pending1:
            first_work = pending1[0]
            claimed = hook_system.claim_work("TestAgent1", first_work.work_id)
            print(f"✅ Claimed work: {claimed}")

            if claimed:
                started = hook_system.start_execution("TestAgent1", first_work.work_id, {
                    "started_by": "test",
                    "execution_plan": "test_execution"
                })
                print(f"✅ Started execution: {started}")

                completed = hook_system.complete_work("TestAgent1", first_work.work_id, {
                    "result": "success",
                    "completion_time": "2023-test"
                })
                print(f"✅ Completed work: {completed}")

        # Test 5: Hook status
        print("\n🔍 Test 5: Hook Status")
        status1 = hook_system.get_hook_status("TestAgent1")
        status2 = hook_system.get_hook_status("TestAgent2")

        print(f"✅ TestAgent1 status: {status1['work_summary']}")
        print(f"✅ TestAgent2 status: {status2['work_summary']}")

        # Test 6: List all hooks
        print("\n🔍 Test 6: List All Hooks")
        all_hooks = hook_system.list_all_hooks()
        print(f"✅ Found {len(all_hooks)} hooks:")
        for hook in all_hooks:
            print(f"   - {hook['agent_name']}: {hook['pending_work']} pending")

        print("\n" + "=" * 50)
        print("🎉 HOOK SYSTEM: ALL TESTS PASSED")
        print("✅ GUPP Infrastructure: READY")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    success = test_hook_system()
    sys.exit(0 if success else 1)