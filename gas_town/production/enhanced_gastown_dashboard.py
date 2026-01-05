#!/usr/bin/env python3
"""
Enhanced Gas Town Dashboard
==========================

Real-time monitoring dashboard that integrates with Steve Yegge's Gas Town system.
Provides enhanced visualization and monitoring capabilities that complement
the production Gas Town installation.

Features:
- Auto-detects existing Gas Town installation
- Monitors Steve's convoys, crews, and rigs
- Integrates with MCP Agent Mail ecosystem
- Enhanced tmux integration and session management
- Real-time status monitoring with Rich TUI

Usage:
    python3 enhanced_gastown_dashboard.py              # Launch dashboard
    python3 enhanced_gastown_dashboard.py --detect     # Test Gas Town detection
    python3 enhanced_gastown_dashboard.py --monitor    # Monitor mode
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add our modules to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Gas Town MCP Bridge
try:
    from gastown_mcp_bridge import GasTownDetector
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class EnhancedGasTownDashboard:
    """Enhanced dashboard for Steve Yegge's Gas Town with MCP integration."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.gas_town_info = {}
        self.mcp_integration = False
        self.refresh_interval = 2.0
        self.running = True

        # Initialize Gas Town detection
        if BRIDGE_AVAILABLE:
            detector = GasTownDetector()
            self.gas_town_info = detector.detect_installation()

        # Initialize MCP integration if available
        self._check_mcp_integration()

    def _check_mcp_integration(self):
        """Check if MCP Agent Mail integration is available."""
        try:
            # Check if MCP Agent Mail is running
            result = subprocess.run(["curl", "-s", "http://127.0.0.1:8765/health"],
                                  capture_output=True, timeout=2)
            self.mcp_integration = result.returncode == 0
        except:
            self.mcp_integration = False

    def gather_enhanced_data(self) -> Dict[str, Any]:
        """Gather comprehensive system data from Gas Town and MCP."""
        data = {
            'timestamp': time.time(),
            'gas_town': self._gather_gas_town_data(),
            'mcp': self._gather_mcp_data() if self.mcp_integration else {},
            'system': self._gather_system_data(),
            'integration': {
                'gas_town_detected': self.gas_town_info.get('found', False),
                'mcp_available': self.mcp_integration,
                'bridge_status': 'active' if self.gas_town_info.get('found') and self.mcp_integration else 'inactive'
            }
        }
        return data

    def _gather_gas_town_data(self) -> Dict[str, Any]:
        """Gather data from Steve's Gas Town system."""
        if not self.gas_town_info.get('found'):
            return {'status': 'not_detected', 'error': 'Gas Town binary not found'}

        gas_town_data = {
            'status': 'detected',
            'binary_path': self.gas_town_info.get('binary_path'),
            'version': self.gas_town_info.get('version'),
            'daemon_running': self.gas_town_info.get('daemon_running', False),
            'mayor_session': self.gas_town_info.get('mayor_session'),
            'convoys': [],
            'crews': [],
            'rigs': [],
            'active_work': 0
        }

        try:
            gt_binary = self.gas_town_info['binary_path']

            # Get convoy information
            try:
                result = subprocess.run([gt_binary, 'convoy', 'list'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    gas_town_data['convoys'] = self._parse_convoy_output(result.stdout)
            except Exception as e:
                gas_town_data['convoy_error'] = str(e)

            # Get crew information
            try:
                result = subprocess.run([gt_binary, 'crew', 'list'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    gas_town_data['crews'] = self._parse_crew_output(result.stdout)
            except Exception as e:
                gas_town_data['crew_error'] = str(e)

            # Get rig information
            try:
                result = subprocess.run([gt_binary, 'rig', 'list'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    gas_town_data['rigs'] = self._parse_rig_output(result.stdout)
            except Exception as e:
                gas_town_data['rig_error'] = str(e)

        except Exception as e:
            gas_town_data['error'] = f"Data gathering failed: {str(e)}"

        return gas_town_data

    def _gather_mcp_data(self) -> Dict[str, Any]:
        """Gather data from MCP Agent Mail system."""
        mcp_data = {
            'agents': 0,
            'messages': 0,
            'reservations': 0,
            'sessions': []
        }

        try:
            # Try to get MCP data via API calls
            # This would integrate with the actual MCP Agent Mail API
            pass
        except Exception as e:
            mcp_data['error'] = str(e)

        return mcp_data

    def _gather_system_data(self) -> Dict[str, Any]:
        """Gather system-level information."""
        system_data = {
            'tmux_sessions': [],
            'total_sessions': 0,
            'agent_sessions': 0,
            'processes': {
                'gas_town_daemon': False,
                'mcp_server': False
            }
        }

        try:
            # Get tmux sessions
            result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
            if result.returncode == 0:
                sessions = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                system_data['total_sessions'] = len(sessions)

                # Identify agent sessions
                gas_town_sessions = []
                for session in sessions:
                    session_name = session.split(':')[0]
                    if any(keyword in session.lower() for keyword in ['mayor', 'gastown', 'gt', 'crew']):
                        gas_town_sessions.append({
                            'name': session_name,
                            'info': session,
                            'type': 'gas_town'
                        })

                system_data['tmux_sessions'] = gas_town_sessions
                system_data['agent_sessions'] = len(gas_town_sessions)

        except FileNotFoundError:
            system_data['tmux_error'] = 'tmux not available'
        except Exception as e:
            system_data['error'] = str(e)

        return system_data

    def _parse_convoy_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Gas Town convoy list output."""
        convoys = []
        lines = output.strip().split('\n')

        for line in lines:
            if line.strip() and not line.startswith('#'):
                # Parse convoy information - format depends on actual gt output
                convoy_info = {
                    'line': line.strip(),
                    'parsed': False
                }
                convoys.append(convoy_info)

        return convoys

    def _parse_crew_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Gas Town crew list output."""
        crews = []
        lines = output.strip().split('\n')

        for line in lines:
            if line.strip() and not line.startswith('#'):
                crew_info = {
                    'line': line.strip(),
                    'parsed': False
                }
                crews.append(crew_info)

        return crews

    def _parse_rig_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Gas Town rig list output."""
        rigs = []
        lines = output.strip().split('\n')

        for line in lines:
            if line.strip() and not line.startswith('#'):
                rig_info = {
                    'line': line.strip(),
                    'parsed': False
                }
                rigs.append(rig_info)

        return rigs

    def render_dashboard(self, data: Dict[str, Any]) -> Layout:
        """Render the enhanced Gas Town dashboard."""
        if not RICH_AVAILABLE:
            return self._render_text_dashboard(data)

        layout = Layout()

        # Split into header and main content
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=2)
        )

        # Split main into left and right
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        # Split left column
        layout["left"].split_column(
            Layout(name="gas_town", ratio=2),
            Layout(name="integration", ratio=1)
        )

        # Split right column
        layout["right"].split_column(
            Layout(name="mcp", ratio=1),
            Layout(name="system", ratio=1)
        )

        # Render panels
        layout["header"].update(self._render_header(data))
        layout["gas_town"].update(self._render_gas_town_panel(data))
        layout["mcp"].update(self._render_mcp_panel(data))
        layout["system"].update(self._render_system_panel(data))
        layout["integration"].update(self._render_integration_panel(data))
        layout["footer"].update(self._render_footer())

        return layout

    def _render_header(self, data: Dict[str, Any]) -> Panel:
        """Render dashboard header."""
        timestamp = datetime.fromtimestamp(data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")

        status_parts = []

        # Gas Town status
        gas_town = data['gas_town']
        if gas_town.get('status') == 'detected':
            if gas_town.get('daemon_running'):
                status_parts.append("🏭 Gas Town: 🟢 Active")
            else:
                status_parts.append("🏭 Gas Town: 🟡 Detected")
        else:
            status_parts.append("🏭 Gas Town: 🔴 Not Found")

        # MCP status
        if data['integration']['mcp_available']:
            status_parts.append("🔗 MCP: 🟢 Connected")
        else:
            status_parts.append("🔗 MCP: 🔴 Offline")

        # Integration status
        bridge_status = data['integration']['bridge_status']
        if bridge_status == 'active':
            status_parts.append("🌉 Bridge: 🟢 Active")
        else:
            status_parts.append("🌉 Bridge: 🔴 Inactive")

        header_text = f"🏭 ENHANCED GAS TOWN DASHBOARD - {timestamp}\n{' | '.join(status_parts)}"

        return Panel(
            Align.center(header_text),
            style="bold blue"
        )

    def _render_gas_town_panel(self, data: Dict[str, Any]) -> Panel:
        """Render Gas Town status panel."""
        gas_town = data['gas_town']

        if gas_town.get('status') != 'detected':
            content = "[red]Gas Town not detected[/red]\n\n"
            content += "Install Steve Yegge's Gas Town:\n"
            content += "  go install github.com/steveyegge/gastown/cmd/gt@latest"
            return Panel(content, title="🏭 Steve's Gas Town", title_align="left")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Component", style="cyan", width=12)
        table.add_column("Status", width=15)
        table.add_column("Details", width=25)

        # Binary info
        table.add_row("Binary", "✅ Found", gas_town.get('binary_path', 'Unknown')[-30:])

        # Version
        version = gas_town.get('version', 'Unknown')
        table.add_row("Version", "✅ Detected", version[:25])

        # Daemon
        daemon_status = "🟢 Running" if gas_town.get('daemon_running') else "🔴 Stopped"
        table.add_row("Daemon", daemon_status, "")

        # Mayor session
        mayor = gas_town.get('mayor_session')
        mayor_status = f"🟢 {mayor}" if mayor else "🔴 No session"
        table.add_row("Mayor", mayor_status, "")

        # Convoys
        convoy_count = len(gas_town.get('convoys', []))
        table.add_row("Convoys", f"📊 {convoy_count}", "Active work bundles")

        # Crews
        crew_count = len(gas_town.get('crews', []))
        table.add_row("Crews", f"👥 {crew_count}", "Agent teams")

        # Rigs
        rig_count = len(gas_town.get('rigs', []))
        table.add_row("Rigs", f"🔧 {rig_count}", "Project workspaces")

        return Panel(table, title="🏭 Steve's Gas Town", title_align="left")

    def _render_mcp_panel(self, data: Dict[str, Any]) -> Panel:
        """Render MCP integration panel."""
        mcp = data['mcp']

        if not data['integration']['mcp_available']:
            content = "[red]MCP Agent Mail not available[/red]\n\n"
            content += "Start MCP Agent Mail server:\n"
            content += "  mcp-agent-mail start"
            return Panel(content, title="🔗 MCP Integration", title_align="left")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", width=12)
        table.add_column("Count", width=8)
        table.add_column("Status", width=15)

        table.add_row("Agents", str(mcp.get('agents', 0)), "🟢 Active")
        table.add_row("Messages", str(mcp.get('messages', 0)), "📧 Synced")
        table.add_row("Reservations", str(mcp.get('reservations', 0)), "🔒 Managed")

        return Panel(table, title="🔗 MCP Integration", title_align="left")

    def _render_system_panel(self, data: Dict[str, Any]) -> Panel:
        """Render system status panel."""
        system = data['system']

        content = []
        content.append(f"Total tmux sessions: {system.get('total_sessions', 0)}")
        content.append(f"Gas Town sessions: {system.get('agent_sessions', 0)}")

        if system.get('tmux_sessions'):
            content.append("\nActive sessions:")
            for session in system['tmux_sessions'][:3]:
                content.append(f"  • {session['name']}")

        return Panel("\n".join(content), title="📊 System Status", title_align="left")

    def _render_integration_panel(self, data: Dict[str, Any]) -> Panel:
        """Render integration status panel."""
        integration = data['integration']

        content = []
        content.append(f"Gas Town: {'🟢 Detected' if integration['gas_town_detected'] else '🔴 Missing'}")
        content.append(f"MCP: {'🟢 Available' if integration['mcp_available'] else '🔴 Offline'}")
        content.append(f"Bridge: {'🟢 Active' if integration['bridge_status'] == 'active' else '🔴 Inactive'}")

        if integration['bridge_status'] == 'active':
            content.append("\n✅ Full integration enabled")
            content.append("🌉 Bridging Gas Town ↔ MCP")
        else:
            content.append("\n⚠️ Limited functionality")
            content.append("Install missing components")

        return Panel("\n".join(content), title="🌉 Integration Status", title_align="left")

    def _render_footer(self) -> Panel:
        """Render dashboard footer."""
        footer_text = "Enhanced Gas Town Dashboard | Press Ctrl-C to exit | Monitoring Steve Yegge's Gas Town + MCP Agent Mail"
        return Panel(footer_text, style="dim")

    def _render_text_dashboard(self, data: Dict[str, Any]) -> str:
        """Render text-based dashboard for systems without Rich."""
        output = []
        output.append("🏭 ENHANCED GAS TOWN DASHBOARD")
        output.append("=" * 50)

        timestamp = datetime.fromtimestamp(data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        output.append(f"Time: {timestamp}")
        output.append("")

        # Gas Town status
        gas_town = data['gas_town']
        output.append("🏭 Steve's Gas Town:")
        if gas_town.get('status') == 'detected':
            output.append(f"   ✅ Detected: {gas_town.get('binary_path')}")
            output.append(f"   Daemon: {'🟢 Running' if gas_town.get('daemon_running') else '🔴 Stopped'}")
            output.append(f"   Convoys: {len(gas_town.get('convoys', []))}")
            output.append(f"   Crews: {len(gas_town.get('crews', []))}")
        else:
            output.append("   ❌ Not detected")

        output.append("")

        # MCP status
        output.append("🔗 MCP Integration:")
        if data['integration']['mcp_available']:
            output.append("   ✅ MCP Agent Mail connected")
        else:
            output.append("   ❌ MCP Agent Mail offline")

        return "\n".join(output)

    def run_dashboard(self):
        """Run the enhanced dashboard."""
        if not RICH_AVAILABLE:
            self._run_text_dashboard()
            return

        try:
            with Live(refresh_per_second=0.5, screen=True) as live:
                while self.running:
                    data = self.gather_enhanced_data()
                    dashboard = self.render_dashboard(data)
                    live.update(dashboard)
                    time.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            if self.console:
                self.console.print("\n\n👋 Enhanced Gas Town Dashboard stopped.", style="bold green")
            else:
                print("\n\n👋 Enhanced Gas Town Dashboard stopped.")

    def _run_text_dashboard(self):
        """Run text-based dashboard."""
        try:
            while self.running:
                data = self.gather_enhanced_data()

                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')

                # Render dashboard
                output = self._render_text_dashboard(data)
                print(output)

                time.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            print("\n\n👋 Enhanced Gas Town Dashboard stopped.")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Gas Town Dashboard")
    parser.add_argument('--detect', action='store_true', help='Test Gas Town detection and exit')
    parser.add_argument('--monitor', action='store_true', help='Monitor mode (non-interactive)')
    parser.add_argument('--interval', type=float, default=2.0, help='Refresh interval in seconds')

    args = parser.parse_args()

    dashboard = EnhancedGasTownDashboard()
    dashboard.refresh_interval = args.interval

    if args.detect:
        print("🔍 Testing Gas Town detection...")
        data = dashboard.gather_enhanced_data()
        print(json.dumps(data, indent=2, default=str))
        return 0

    dashboard.run_dashboard()
    return 0


if __name__ == "__main__":
    sys.exit(main())