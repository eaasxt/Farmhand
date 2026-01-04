#!/usr/bin/env python3
"""
Test Gas Town Automation Layer - Phase 1 Complete Validation
===========================================================

Comprehensive testing of all Phase 1 automation components:
- Hook System (GUPP implementation)
- gt CLI Suite (all commands)
- Session Management (handoff/seance)
- Auto-execution readiness
"""

import os
import sys
import subprocess
import json
import time
import tempfile
import shutil
from pathlib import Path

# Add our modules to path
sys.path.insert(0, '/home/ubuntu/projects/deere/gas_town/phase_c')

from hook_system import GasTownHookSystem, WorkPriority


def test_automation_layer():
    """Test the complete Gas Town automation layer."""
    print("🤖 TESTING GAS TOWN AUTOMATION LAYER")
    print("=" * 60)

    success_count = 0
    total_tests = 0

    # Test 1: Hook System Core Functions
    print("\n🪝 Test 1: Hook System Core Functions")
    try:
        hook_system = GasTownHookSystem()

        # Create hook
        hook_id = hook_system.create_agent_hook("AutoTestAgent", {"role": "tester"})
        print(f"✅ Hook created: {hook_id}")

        # Sling work
        work_id = hook_system.sling_work(
            "AutoTestAgent", "molecule", "mol-auto-test-123", "TestRunner",
            WorkPriority.HIGH, "Automated testing"
        )
        print(f"✅ Work slung: {work_id}")

        # Check hook
        pending = hook_system.check_hook("AutoTestAgent")
        assert len(pending) > 0, f"Expected pending work, got {len(pending)}"
        print(f"✅ Hook check: {len(pending)} pending items")

        success_count += 1

    except Exception as e:
        print(f"❌ Hook system test failed: {e}")

    total_tests += 1

    # Test 2: GT CLI Commands
    print("\n🖥️  Test 2: GT CLI Commands")
    gt_path = "/home/ubuntu/projects/deere/gas_town/phase_c/gt"

    try:
        # Test basic commands
        commands_to_test = [
            [gt_path, "--help"],
            [gt_path, "status"],
            [gt_path, "hooks"],
            [gt_path, "hooks", "AutoTestAgent", "--action", "check"]
        ]

        for cmd in commands_to_test:
            result = subprocess.run(cmd, capture_output=True, text=True)
            assert result.returncode == 0, f"Command failed: {' '.join(cmd)}"
            print(f"✅ Command successful: {' '.join(cmd[1:])}")

        success_count += 1

    except Exception as e:
        print(f"❌ GT CLI test failed: {e}")

    total_tests += 1

    # Test 3: Session Management
    print("\n🔄 Test 3: Session Management")
    try:
        # Test handoff
        result = subprocess.run([
            gt_path, "handoff",
            "--agent", "AutoTestAgent",
            "--reason", "Automated testing handoff"
        ], capture_output=True, text=True)

        assert result.returncode == 0, f"Handoff failed: {result.stderr}"
        assert "Ready for handoff" in result.stdout, "Handoff output missing"
        print("✅ Handoff command successful")

        # Check handoff file created
        handoff_file = Path.home() / ".gas_town" / "handoff-AutoTestAgent.json"
        assert handoff_file.exists(), "Handoff file not created"

        with open(handoff_file) as f:
            handoff_data = json.load(f)
            assert handoff_data["agent_name"] == "AutoTestAgent"
            assert "handoff_reason" in handoff_data

        print("✅ Handoff data persistence working")

        # Test seance (should fail gracefully with no session history)
        result = subprocess.run([
            gt_path, "seance", "AutoTestAgent"
        ], capture_output=True, text=True)

        # Should return 1 because no session history, but should handle gracefully
        assert "No predecessor session found" in result.stdout, "Seance error handling incorrect"
        print("✅ Seance command handles missing sessions correctly")

        success_count += 1

    except Exception as e:
        print(f"❌ Session management test failed: {e}")

    total_tests += 1

    # Test 4: Work Slinging Integration
    print("\n⚡ Test 4: Work Slinging Integration")
    try:
        # Sling work via CLI
        result = subprocess.run([
            gt_path, "sling", "AutoTestAgent", "molecule", "mol-integration-test",
            "--priority", "urgent", "--reason", "Integration testing", "--slung-by", "TestRunner"
        ], capture_output=True, text=True)

        assert result.returncode == 0, f"Sling command failed: {result.stderr}"
        assert "Slung molecule" in result.stdout, "Sling output missing"
        print("✅ Work slinging via CLI successful")

        # Verify work is on hook
        result = subprocess.run([
            gt_path, "hooks", "AutoTestAgent", "--action", "check"
        ], capture_output=True, text=True)

        assert "mol-integration-test" in result.stdout, "Work not found on hook"
        assert "urgent" in result.stdout, "Priority not preserved"
        print("✅ Work correctly placed on hook with priority")

        success_count += 1

    except Exception as e:
        print(f"❌ Work slinging integration test failed: {e}")

    total_tests += 1

    # Test 5: Auto-Execution System Readiness
    print("\n🚀 Test 5: Auto-Execution System Readiness")
    try:
        # Check GUPP auto-execution file exists
        gupp_file = Path("/home/ubuntu/projects/deere/gas_town/phase_c/gupp_auto_execution.py")
        assert gupp_file.exists(), "GUPP auto-execution file not found"

        # Test it can be imported
        import gupp_auto_execution
        assert hasattr(gupp_auto_execution, 'GUPPAutoExecution'), "GUPPAutoExecution class not found"
        print("✅ GUPP auto-execution system ready")

        # Test hook system integration
        hooks = hook_system.list_all_hooks()
        assert len(hooks) > 0, "No hooks available for auto-execution"
        print(f"✅ {len(hooks)} hooks available for auto-execution")

        success_count += 1

    except Exception as e:
        print(f"❌ Auto-execution readiness test failed: {e}")

    total_tests += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 AUTOMATION LAYER TEST SUMMARY")
    print(f"   Tests passed: {success_count}/{total_tests}")
    print(f"   Success rate: {success_count/total_tests*100:.1f}%")

    if success_count == total_tests:
        print("🏆 ALL TESTS PASSED - AUTOMATION LAYER COMPLETE!")
        print("\n📋 Phase 1 Components Validated:")
        print("   ✅ Hook System (GUPP implementation)")
        print("   ✅ gt CLI Suite (all core commands)")
        print("   ✅ Session Management (handoff/seance)")
        print("   ✅ Work Slinging Integration")
        print("   ✅ Auto-execution System Readiness")

        print("\n🚀 Gas Town Automation Layer: FULLY OPERATIONAL")
        print("   From 'Enterprise Gas Town' (manual) → 'Autonomous Factory' (automatic)")

        return True
    else:
        print("❌ SOME TESTS FAILED - NEEDS INVESTIGATION")
        return False


if __name__ == "__main__":
    success = test_automation_layer()
    sys.exit(0 if success else 1)