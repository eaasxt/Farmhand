#!/usr/bin/env python3
"""
Gas Town MCP Wrapper
===================

CLI wrapper that enhances Steve Yegge's Gas Town with MCP integration.
Detects existing Gas Town installation and adds monitoring/dashboard capabilities
without conflicting with the production system.

Key Features:
- Passes through to Steve's `gt` commands
- Adds enhanced monitoring and dashboard commands
- Provides MCP Agent Mail integration
- Adds tmux enhancements that complement Gas Town

Usage:
    gt-mcp <command> [args...]           # Enhanced Gas Town commands
    gt-mcp dashboard                     # Launch enhanced dashboard
    gt-mcp bridge start                  # Start MCP bridge
    gt-mcp tmux setup                    # Enhanced tmux integration
    gt-mcp detect                        # Detect Gas Town installation
"""

import os
import sys
import subprocess
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add our modules to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gastown_mcp_bridge import GasTownDetector, MCPGasTownBridge
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False


class GasTownMCPWrapper:
    """CLI wrapper that enhances Steve's Gas Town with MCP capabilities."""

    def __init__(self):
        self.gas_town_binary = None
        self.gas_town_info = {}
        self.detect_gas_town()

    def detect_gas_town(self):
        """Detect existing Gas Town installation."""
        if not BRIDGE_AVAILABLE:
            return

        detector = GasTownDetector()
        self.gas_town_info = detector.detect_installation()

        if self.gas_town_info.get('found'):
            self.gas_town_binary = self.gas_town_info['binary_path']

    def run_command(self, args: List[str]) -> int:
        """Run Gas Town command with MCP enhancements."""
        if not args:
            return self.show_help()

        command = args[0]

        # Handle MCP-specific commands
        if command == 'dashboard':
            return self.run_dashboard(args[1:])
        elif command == 'bridge':
            return self.run_bridge(args[1:])
        elif command == 'tmux':
            return self.run_tmux(args[1:])
        elif command == 'detect':
            return self.run_detect(args[1:])
        elif command == 'status':
            return self.run_enhanced_status(args[1:])
        elif command in ['help', '--help', '-h']:
            return self.show_help()

        # For all other commands, pass through to Steve's Gas Town
        return self.passthrough_to_gas_town(args)

    def passthrough_to_gas_town(self, args: List[str]) -> int:
        """Pass command through to Steve's Gas Town binary."""
        if not self.gas_town_binary:
            print("❌ Gas Town not detected. Install Steve Yegge's Gas Town:")
            print("   go install github.com/steveyegge/gastown/cmd/gt@latest")
            return 1

        try:
            # Execute Steve's gt command
            cmd = [self.gas_town_binary] + args
            result = subprocess.run(cmd)
            return result.returncode

        except FileNotFoundError:
            print(f"❌ Gas Town binary not found: {self.gas_town_binary}")
            return 1
        except Exception as e:
            print(f"❌ Command failed: {str(e)}")
            return 1

    def run_dashboard(self, args: List[str]) -> int:
        """Launch enhanced Gas Town dashboard."""
        try:
            dashboard_script = Path(__file__).parent / "enhanced_gastown_dashboard.py"

            if not dashboard_script.exists():
                print("❌ Enhanced dashboard not found")
                return 1

            print("🚀 Launching Enhanced Gas Town Dashboard...")
            print("💡 Monitoring Steve's Gas Town + MCP Agent Mail")
            print("💡 Press Ctrl-C to exit")

            cmd = ["python3", str(dashboard_script)] + args
            result = subprocess.run(cmd)
            return result.returncode

        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped.")
            return 0
        except Exception as e:
            print(f"❌ Dashboard launch failed: {str(e)}")
            return 1

    def run_bridge(self, args: List[str]) -> int:
        """Manage MCP bridge service."""
        if not BRIDGE_AVAILABLE:
            print("❌ MCP Bridge not available")
            return 1

        try:
            bridge_script = Path(__file__).parent / "gastown_mcp_bridge.py"

            if not bridge_script.exists():
                print("❌ MCP Bridge script not found")
                return 1

            cmd = ["python3", str(bridge_script), "bridge"] + args
            result = subprocess.run(cmd)
            return result.returncode

        except Exception as e:
            print(f"❌ Bridge command failed: {str(e)}")
            return 1

    def run_tmux(self, args: List[str]) -> int:
        """Enhanced tmux integration for Gas Town."""
        try:
            # For now, provide basic tmux enhancements
            if not args or args[0] == 'setup':
                return self.setup_enhanced_tmux()
            elif args[0] == 'status':
                return self.show_tmux_status()
            else:
                print("❌ Unknown tmux command. Available: setup, status")
                return 1

        except Exception as e:
            print(f"❌ tmux command failed: {str(e)}")
            return 1

    def setup_enhanced_tmux(self) -> int:
        """Setup enhanced tmux configuration for Gas Town."""
        print("🔧 Setting up enhanced tmux integration for Gas Town...")

        try:
            # Create enhanced tmux configuration
            tmux_config = self.create_enhanced_tmux_config()

            # Write to tmux config file
            config_file = Path.home() / ".tmux.conf.gastown-mcp"
            with open(config_file, 'w') as f:
                f.write(tmux_config)

            print(f"✅ Enhanced tmux config written to {config_file}")
            print("\n📋 To enable enhanced Gas Town tmux integration:")
            print("   1. Add to your ~/.tmux.conf:")
            print(f"      source-file {config_file}")
            print("   2. Reload tmux config:")
            print("      tmux source-file ~/.tmux.conf")
            print("\n🎯 Enhanced key bindings:")
            print("   Prefix + g     - Gas Town status")
            print("   Prefix + G     - Enhanced dashboard")
            print("   Prefix + m     - MCP status")
            print("   Prefix + b     - Bridge status")

            return 0

        except Exception as e:
            print(f"❌ tmux setup failed: {e}")
            return 1

    def create_enhanced_tmux_config(self) -> str:
        """Create enhanced tmux configuration for Gas Town."""
        current_dir = os.getcwd()
        wrapper_script = os.path.abspath(__file__)

        config = f'''# Gas Town MCP Enhanced tmux Configuration
# Integrates with Steve Yegge's Gas Town + adds MCP enhancements

# Gas Town enhanced key bindings
bind-key g display-popup -E "cd {current_dir} && python3 {wrapper_script} status"
bind-key G display-popup -E -w 90% -h 90% "cd {current_dir} && python3 {wrapper_script} dashboard"
bind-key m display-popup -E "cd {current_dir} && python3 {wrapper_script} bridge status"
bind-key b display-popup -E "cd {current_dir} && python3 {wrapper_script} detect --json | jq ."

# Enhanced status bar
set -g status-right-length 150
set -g status-right "#[fg=yellow]⚡Gas Town #[fg=cyan]🔗MCP #[fg=green]%H:%M #[fg=blue]%Y-%m-%d"
set -g status-interval 10

# Gas Town color scheme (enhanced)
set -g status-style bg=colour235,fg=colour136
set -g status-left "#[fg=colour166,bold]🏭 Gas Town MCP #[fg=colour244]| "
set -g window-status-current-style bg=colour166,fg=colour235,bold

# Enhanced pane borders
set -g pane-border-style fg=colour238
set -g pane-active-border-style fg=colour166

# Mouse support
set -g mouse on

# Message style
set -g message-style bg=colour166,fg=colour235,bold
'''
        return config

    def show_tmux_status(self) -> int:
        """Show enhanced tmux status for Gas Town."""
        print("📺 ENHANCED TMUX STATUS")
        print("=" * 30)

        try:
            # Get tmux sessions
            result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
            if result.returncode == 0:
                sessions = result.stdout.strip().split('\n') if result.stdout.strip() else []
                print(f"Total sessions: {len(sessions)}")

                # Identify Gas Town sessions
                gas_town_sessions = []
                for session in sessions:
                    if any(keyword in session.lower() for keyword in ['mayor', 'gastown', 'gt', 'crew']):
                        gas_town_sessions.append(session)

                if gas_town_sessions:
                    print(f"Gas Town sessions: {len(gas_town_sessions)}")
                    for session in gas_town_sessions:
                        print(f"  • {session}")
                else:
                    print("Gas Town sessions: None detected")

            else:
                print("❌ tmux not available or no sessions")

        except FileNotFoundError:
            print("❌ tmux not installed")
            return 1

        return 0

    def run_detect(self, args: List[str]) -> int:
        """Run Gas Town detection."""
        try:
            bridge_script = Path(__file__).parent / "gastown_mcp_bridge.py"

            if not bridge_script.exists():
                print("❌ Detection script not found")
                return 1

            cmd = ["python3", str(bridge_script), "detect"] + args
            result = subprocess.run(cmd)
            return result.returncode

        except Exception as e:
            print(f"❌ Detection failed: {str(e)}")
            return 1

    def run_enhanced_status(self, args: List[str]) -> int:
        """Show enhanced status combining Gas Town and MCP information."""
        print("🏭 ENHANCED GAS TOWN STATUS")
        print("=" * 40)

        # Show Gas Town status first
        if self.gas_town_binary:
            print("\n🎯 Steve's Gas Town:")
            try:
                # Run original status command
                result = subprocess.run([self.gas_town_binary, 'status'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(result.stdout)
                else:
                    print("   ⚠️ Gas Town status command failed")
            except Exception:
                print("   ⚠️ Could not get Gas Town status")
        else:
            print("\n❌ Steve's Gas Town: Not detected")
            print("   Install: go install github.com/steveyegge/gastown/cmd/gt@latest")

        # Show MCP status
        print("\n🔗 MCP Integration:")
        try:
            # Check MCP Agent Mail
            result = subprocess.run(["curl", "-s", "http://127.0.0.1:8765/health"],
                                  capture_output=True, timeout=3)
            if result.returncode == 0:
                print("   ✅ MCP Agent Mail: Running")
            else:
                print("   ❌ MCP Agent Mail: Offline")
        except:
            print("   ❌ MCP Agent Mail: Not available")

        # Show bridge status
        print("\n🌉 Bridge Status:")
        if self.gas_town_info.get('found'):
            print("   ✅ Gas Town detected")
            if self.gas_town_info.get('daemon_running'):
                print("   ✅ Gas Town daemon running")
            else:
                print("   ⚠️ Gas Town daemon stopped")
        else:
            print("   ❌ Gas Town not found")

        # Show enhancements available
        print("\n⭐ Available Enhancements:")
        print("   gt-mcp dashboard     - Enhanced monitoring dashboard")
        print("   gt-mcp bridge start  - Start MCP integration bridge")
        print("   gt-mcp tmux setup    - Enhanced tmux configuration")

        return 0

    def show_help(self) -> int:
        """Show help information."""
        print("🏭 Gas Town MCP Wrapper")
        print("=" * 30)
        print("Enhances Steve Yegge's Gas Town with MCP Agent Mail integration")
        print()
        print("MCP Enhanced Commands:")
        print("  dashboard              Launch enhanced monitoring dashboard")
        print("  bridge <action>        Manage MCP bridge service")
        print("  tmux <action>         Enhanced tmux integration")
        print("  detect [--json]       Detect Gas Town installation")
        print("  status                Enhanced status (Gas Town + MCP)")
        print("  help                  Show this help")
        print()

        if self.gas_town_binary:
            print("Steve's Gas Town Commands (passthrough):")
            print("  All other commands are passed to Steve's Gas Town binary")
            print(f"  Binary: {self.gas_town_binary}")
            print()
            print("  Examples:")
            print("    gt-mcp convoy list      # Uses Steve's convoy system")
            print("    gt-mcp crew add name    # Uses Steve's crew management")
            print("    gt-mcp mayor attach     # Uses Steve's Mayor session")
        else:
            print("❌ Steve's Gas Town not detected")
            print("   Install: go install github.com/steveyegge/gastown/cmd/gt@latest")

        print()
        print("🔗 Integration Status:")
        if self.gas_town_info.get('found'):
            print("   ✅ Gas Town detected - Full integration available")
        else:
            print("   ❌ Gas Town missing - Limited functionality")

        return 0


def main():
    """Main CLI entry point."""
    wrapper = GasTownMCPWrapper()

    # Get command line arguments (excluding script name)
    args = sys.argv[1:]

    return wrapper.run_command(args)


if __name__ == "__main__":
    sys.exit(main())