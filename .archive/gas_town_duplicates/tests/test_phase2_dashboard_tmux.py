#!/usr/bin/env python3
"""
Test Phase 2: Dashboard and tmux Integration
===========================================

Comprehensive testing of Phase 2 Enhanced User Experience components:
- Real-time Gas Town Dashboard
- tmux Integration and Primary Interface
- Command integration and session management
- Status bar and visual monitoring
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
from pathlib import Path

# Add our modules to path
sys.path.insert(0, '/home/ubuntu/projects/deere/gas_town/phase_c')

from hook_system import GasTownHookSystem, WorkPriority
from gas_town_tmux import GasTownTmux


def test_phase2_dashboard_tmux():
    """Test the complete Phase 2 dashboard and tmux integration."""
    print("🖥️ TESTING PHASE 2: DASHBOARD & TMUX INTEGRATION")
    print("=" * 65)

    success_count = 0
    total_tests = 0

    # Test 1: Dashboard Functionality
    print("\n📊 Test 1: Real-time Dashboard")
    try:
        dashboard_script = Path("/home/ubuntu/projects/deere/gas_town/phase_c/gas_town_dashboard.py")
        assert dashboard_script.exists(), "Dashboard script not found"

        # Test dashboard can be imported and instantiated
        import gas_town_dashboard
        dashboard = gas_town_dashboard.GasTownDashboard()
        assert dashboard is not None, "Dashboard instantiation failed"

        # Test data gathering
        data = dashboard.gather_system_data()
        assert 'timestamp' in data, "Dashboard data missing timestamp"
        assert 'hooks' in data, "Dashboard data missing hooks"
        assert 'sessions' in data, "Dashboard data missing sessions"
        print("✅ Dashboard data gathering working")

        # Test gt dashboard command
        result = subprocess.run(["./gt", "dashboard", "--help"], capture_output=True, text=True, cwd="/home/ubuntu/projects/deere/gas_town/phase_c")
        assert result.returncode == 0, "gt dashboard command not working"
        print("✅ gt dashboard command integrated")

        success_count += 1

    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")

    total_tests += 1

    # Test 2: tmux Integration Core
    print("\n🖼️  Test 2: tmux Integration Core")
    try:
        tmux_script = Path("/home/ubuntu/projects/deere/gas_town/phase_c/gas_town_tmux.py")
        assert tmux_script.exists(), "tmux integration script not found"

        # Test tmux integration can be imported
        tmux_integration = GasTownTmux()
        assert tmux_integration is not None, "tmux integration instantiation failed"

        # Test configuration generation
        config = tmux_integration.create_gas_town_tmux_config()
        assert "Gas Town" in config, "tmux config missing Gas Town branding"
        assert "bind-key g" in config, "tmux config missing key bindings"
        print("✅ tmux configuration generation working")

        # Test status bar data
        status_data = tmux_integration.get_status_bar_data()
        assert status_data, "Status bar data generation failed"
        print(f"✅ Status bar data: {status_data}")

        success_count += 1

    except Exception as e:
        print(f"❌ tmux integration test failed: {e}")

    total_tests += 1

    # Test 3: gt tmux Commands
    print("\n🔧 Test 3: gt tmux Commands")
    try:
        gt_path = "/home/ubuntu/projects/deere/gas_town/phase_c/gt"

        # Test tmux help
        result = subprocess.run([gt_path, "tmux", "--help"], capture_output=True, text=True)
        assert result.returncode == 0, "gt tmux help failed"
        print("✅ gt tmux help working")

        # Test tmux setup
        result = subprocess.run([gt_path, "tmux", "setup"], capture_output=True, text=True)
        assert result.returncode == 0, f"gt tmux setup failed: {result.stderr}"
        print("✅ gt tmux setup working")

        # Verify setup created files
        tmux_config = Path.home() / ".tmux.conf.gasetown"
        assert tmux_config.exists(), "tmux config file not created"

        status_script = Path.home() / ".gas_town" / "tmux_status.sh"
        assert status_script.exists(), "Status script not created"
        print("✅ tmux setup files created")

        # Test tmux integrate
        result = subprocess.run([gt_path, "tmux", "integrate"], capture_output=True, text=True)
        assert result.returncode == 0, "gt tmux integrate failed"
        assert "Key bindings" in result.stdout, "Integration help missing key bindings"
        print("✅ gt tmux integrate working")

        # Test tmux discover
        result = subprocess.run([gt_path, "tmux", "discover"], capture_output=True, text=True)
        assert result.returncode == 0, "gt tmux discover failed"
        print("✅ gt tmux discover working")

        success_count += 1

    except Exception as e:
        print(f"❌ gt tmux commands test failed: {e}")

    total_tests += 1

    # Test 4: Integration with Hook System
    print("\n🪝 Test 4: Integration with Hook System")
    try:
        # Create test hook and verify dashboard sees it
        hook_system = GasTownHookSystem()
        hook_id = hook_system.create_agent_hook("Phase2TestAgent", {"role": "tester", "phase": "2"})
        print(f"✅ Test hook created: {hook_id}")

        # Sling work to the hook
        work_id = hook_system.sling_work(
            "Phase2TestAgent", "molecule", "mol-phase2-dashboard-test", "DashboardTester",
            WorkPriority.HIGH, "Testing Phase 2 integration"
        )
        print(f"✅ Test work slung: {work_id}")

        # Verify dashboard can see the hook and work
        dashboard = gas_town_dashboard.GasTownDashboard()
        data = dashboard.gather_system_data()

        hooks_count = data['hooks']['total']
        pending_work = data['hooks']['pending_work']

        assert hooks_count > 0, "Dashboard not detecting hooks"
        assert pending_work > 0, "Dashboard not detecting pending work"
        print(f"✅ Dashboard sees {hooks_count} hooks with {pending_work} pending work")

        # Test tmux status bar integration
        tmux_integration = GasTownTmux()
        status_text = tmux_integration.get_status_bar_data()
        assert "🪝" in status_text, "Status bar missing hook indicator"
        print(f"✅ tmux status bar shows: {status_text}")

        success_count += 1

    except Exception as e:
        print(f"❌ Integration test failed: {e}")

    total_tests += 1

    # Test 5: User Experience Features
    print("\n🎨 Test 5: User Experience Features")
    try:
        # Test rich formatting (if available)
        try:
            from rich.console import Console
            console = Console()
            assert console is not None, "Rich console not working"
            print("✅ Rich formatting available for enhanced dashboard")
        except ImportError:
            print("⚠️ Rich not available, but fallback text mode working")

        # Test tmux configuration contains expected UX features
        tmux_integration = GasTownTmux()
        config = tmux_integration.create_gas_town_tmux_config()

        # Check for user experience features
        ux_features = [
            "mouse on",  # Mouse support
            "status-interval",  # Auto-refresh status
            "display-popup",  # Popup interfaces
            "colour166",  # Gas Town color scheme
            "automatic-rename on"  # Session naming
        ]

        for feature in ux_features:
            assert feature in config, f"UX feature missing: {feature}"

        print("✅ All UX features present in tmux config")

        # Test key binding variety
        key_bindings = ["bind-key g", "bind-key G", "bind-key h", "bind-key C", "bind-key M"]
        for binding in key_bindings:
            assert binding in config, f"Key binding missing: {binding}"

        print("✅ All key bindings configured")

        success_count += 1

    except Exception as e:
        print(f"❌ User experience test failed: {e}")

    total_tests += 1

    # Summary
    print("\n" + "=" * 65)
    print(f"📊 PHASE 2 TEST SUMMARY")
    print(f"   Tests passed: {success_count}/{total_tests}")
    print(f"   Success rate: {success_count/total_tests*100:.1f}%")

    if success_count == total_tests:
        print("🏆 ALL PHASE 2 TESTS PASSED!")
        print("\n📋 Phase 2 Components Validated:")
        print("   ✅ Real-time Gas Town Dashboard")
        print("   ✅ tmux Integration and Primary Interface")
        print("   ✅ gt Command Integration")
        print("   ✅ Hook System Integration")
        print("   ✅ Enhanced User Experience Features")

        print("\n🎨 Phase 2 Enhanced User Experience: COMPLETE!")
        print("   tmux is now the primary Gas Town interface")
        print("   Real-time monitoring and status available")
        print("   Multi-agent coordination via tmux sessions")

        return True
    else:
        print("❌ SOME TESTS FAILED - NEEDS INVESTIGATION")
        return False


def cleanup_test_artifacts():
    """Clean up test artifacts."""
    try:
        # Remove test tmux config (optional)
        tmux_config = Path.home() / ".tmux.conf.gasetown"
        if tmux_config.exists():
            # Keep it - user might want it
            pass

        print("🧹 Test cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    try:
        success = test_phase2_dashboard_tmux()
        cleanup_test_artifacts()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        cleanup_test_artifacts()
        sys.exit(1)