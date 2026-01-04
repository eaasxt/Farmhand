#!/usr/bin/env python3
"""
Gas Town Real-Time Dashboard
===========================

Live monitoring interface for Gas Town multi-agent orchestration system.
Provides real-time view of:
- Hook system status (agents, pending work, priorities)
- Convoy system (active convoys, progress tracking)
- Agent sessions (tmux sessions, activity monitoring)
- System metrics (performance, health, auto-execution status)

Usage:
    python3 gas_town_dashboard.py
    ./gt dashboard

Key bindings:
    q/Q/Ctrl-C: Quit
    r: Manual refresh
    h: Toggle hook details
    c: Toggle convoy details
    s: Toggle session details
    Space: Pause/resume auto-refresh
"""

import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Add our modules to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.progress import Progress, TaskID, SpinnerColumn, TimeElapsedColumn
    from rich.align import Align
    from rich.bar import Bar
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from hook_system import GasTownHookSystem, WorkPriority

# Try to import convoy system
try:
    sys.path.insert(0, '/home/ubuntu/.claude')
    from convoy_system import list_convoys_command, convoy_status_command
    CONVOY_AVAILABLE = True
except ImportError:
    CONVOY_AVAILABLE = False


class GasTownDashboard:
    """Real-time Gas Town monitoring dashboard."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.hook_system = GasTownHookSystem()
        self.gas_town_dir = Path.home() / ".gas_town"
        self.gas_town_dir.mkdir(exist_ok=True)

        # Dashboard state
        self.auto_refresh = True
        self.refresh_interval = 2.0  # seconds
        self.show_hook_details = True
        self.show_convoy_details = True
        self.show_session_details = True
        self.running = True

        # Data cache
        self.last_refresh = 0
        self.cached_data = {}

    def gather_system_data(self) -> Dict[str, Any]:
        """Gather all system data for the dashboard."""
        now = time.time()

        try:
            # Hook system data
            all_hooks = self.hook_system.list_all_hooks()
            total_pending_work = sum(hook['pending_work'] for hook in all_hooks)

            # Detailed hook information
            hook_details = []
            for hook in all_hooks:
                try:
                    pending = self.hook_system.check_hook(hook['agent_name'])
                    hook_info = {
                        'agent_name': hook['agent_name'],
                        'hook_id': hook['hook_id'],
                        'pending_count': len(pending),
                        'work_items': pending[:3],  # First 3 items for display
                        'created_at': hook['created_at'],
                        'last_activity': hook.get('last_activity', 'N/A')
                    }
                    hook_details.append(hook_info)
                except Exception as e:
                    hook_details.append({
                        'agent_name': hook['agent_name'],
                        'error': str(e)
                    })

            # Convoy system data
            convoy_data = {'count': 0, 'details': [], 'error': None}
            if CONVOY_AVAILABLE:
                try:
                    convoy_result = list_convoys_command()
                    # Parse convoy output (simplified for dashboard)
                    convoy_lines = [line.strip() for line in convoy_result.split('\n') if line.strip()]
                    convoy_data['count'] = len([line for line in convoy_lines if '🚧' in line or '✅' in line])
                    convoy_data['raw_output'] = convoy_result
                except Exception as e:
                    convoy_data['error'] = str(e)

            # tmux session data
            session_data = {'total': 0, 'agent_sessions': [], 'error': None}
            try:
                result = subprocess.run(["tmux", "list-sessions"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    sessions = result.stdout.strip().split('\n') if result.stdout.strip() else []
                    session_data['total'] = len(sessions)

                    # Identify agent sessions
                    gas_town_roles = ['mayor', 'witness', 'refinery', 'deacon', 'crew', 'polecat', 'gas']
                    agent_sessions = []
                    for session_line in sessions:
                        session_name = session_line.split(':')[0]
                        if any(role in session_name.lower() for role in gas_town_roles):
                            # Parse session details
                            parts = session_line.split(' ')
                            windows = 'unknown'
                            attached = 'detached'
                            for part in parts:
                                if 'windows' in part:
                                    windows = part
                                if 'attached' in part:
                                    attached = 'attached'

                            agent_sessions.append({
                                'name': session_name,
                                'windows': windows,
                                'status': attached,
                                'line': session_line
                            })

                    session_data['agent_sessions'] = agent_sessions
                else:
                    session_data['error'] = f"tmux error: {result.stderr}"
            except subprocess.TimeoutExpired:
                session_data['error'] = "tmux command timeout"
            except FileNotFoundError:
                session_data['error'] = "tmux not found"
            except Exception as e:
                session_data['error'] = str(e)

            # GUPP auto-execution status
            gupp_status = self.check_gupp_status()

            # System performance metrics
            metrics = {
                'uptime': now - self.last_refresh if self.last_refresh > 0 else 0,
                'refresh_count': getattr(self, 'refresh_count', 0) + 1,
                'hooks_per_second': len(all_hooks) / max(now - self.last_refresh, 1) if self.last_refresh > 0 else 0
            }

            self.refresh_count = metrics['refresh_count']
            self.last_refresh = now

            return {
                'timestamp': now,
                'hooks': {
                    'total': len(all_hooks),
                    'pending_work': total_pending_work,
                    'details': hook_details
                },
                'convoys': convoy_data,
                'sessions': session_data,
                'gupp': gupp_status,
                'metrics': metrics
            }

        except Exception as e:
            return {
                'timestamp': now,
                'error': f"Data gathering failed: {str(e)}",
                'hooks': {'total': 0, 'pending_work': 0, 'details': []},
                'convoys': {'count': 0, 'details': [], 'error': str(e)},
                'sessions': {'total': 0, 'agent_sessions': [], 'error': str(e)},
                'metrics': {'uptime': 0, 'refresh_count': 0}
            }

    def check_gupp_status(self) -> Dict[str, Any]:
        """Check GUPP auto-execution system status."""
        gupp_file = Path("/home/ubuntu/projects/deere/gas_town/phase_c/gupp_auto_execution.py")

        status = {
            'available': gupp_file.exists(),
            'running': False,
            'last_nudge': None,
            'error': None
        }

        try:
            # Check for GUPP daemon process
            result = subprocess.run(["pgrep", "-f", "gupp_auto_execution"], capture_output=True)
            status['running'] = result.returncode == 0

            # Check nudge log for recent activity
            nudge_log = self.gas_town_dir / "nudge.log"
            if nudge_log.exists():
                try:
                    with open(nudge_log, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            if last_line:
                                timestamp = last_line.split(',')[0]
                                status['last_nudge'] = float(timestamp)
                except Exception as e:
                    status['error'] = f"Nudge log error: {e}"

        except Exception as e:
            status['error'] = str(e)

        return status

    def create_layout(self) -> Layout:
        """Create the dashboard layout."""
        layout = Layout()

        # Split into header and main content
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", size=None),
            Layout(name="footer", size=2)
        )

        # Split main into left and right columns
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )

        # Split left column
        layout["left"].split_column(
            Layout(name="hooks", ratio=2),
            Layout(name="system", ratio=1)
        )

        # Split right column
        layout["right"].split_column(
            Layout(name="convoys", ratio=1),
            Layout(name="sessions", ratio=1),
            Layout(name="gupp", ratio=1)
        )

        return layout

    def render_header(self, data: Dict[str, Any]) -> Panel:
        """Render the dashboard header."""
        timestamp = datetime.fromtimestamp(data['timestamp']).strftime("%Y-%m-%d %H:%M:%S")

        status_items = []

        # Auto-refresh status
        refresh_status = "🔄 AUTO" if self.auto_refresh else "⏸️ PAUSED"
        status_items.append(f"{refresh_status}")

        # System summary
        hooks_count = data['hooks']['total']
        pending_work = data['hooks']['pending_work']
        status_items.append(f"🪝 {hooks_count} hooks")
        status_items.append(f"📋 {pending_work} pending")

        if data.get('convoys', {}).get('count', 0) > 0:
            status_items.append(f"🚚 {data['convoys']['count']} convoys")

        agent_sessions = len(data.get('sessions', {}).get('agent_sessions', []))
        if agent_sessions > 0:
            status_items.append(f"📺 {agent_sessions} agents")

        status_text = " | ".join(status_items)
        header_text = f"🏭 GAS TOWN DASHBOARD - {timestamp} | {status_text}"

        return Panel(
            Align.center(header_text),
            style="bold blue"
        )

    def render_hooks_panel(self, data: Dict[str, Any]) -> Panel:
        """Render the hook system status panel."""
        hooks_data = data['hooks']

        if not self.show_hook_details:
            summary = f"Total: {hooks_data['total']} | Pending: {hooks_data['pending_work']}"
            return Panel(summary, title="🪝 Hook System", title_align="left")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Agent", style="cyan", width=15)
        table.add_column("Hook ID", width=12)
        table.add_column("Pending", justify="center", width=8)
        table.add_column("Top Work", width=20)
        table.add_column("Priority", width=8)

        for hook in hooks_data['details']:
            if 'error' in hook:
                table.add_row(
                    hook['agent_name'],
                    "[red]ERROR[/red]",
                    "?",
                    hook['error'][:20],
                    ""
                )
                continue

            agent_name = hook['agent_name']
            hook_id = hook['hook_id'][-8:]  # Last 8 chars
            pending_count = str(hook['pending_count'])

            # Get top priority work item
            top_work = ""
            priority_str = ""
            if hook['work_items']:
                top_item = hook['work_items'][0]
                top_work = f"{top_item.work_type}:{top_item.work_reference}"[:20]
                priority_colors = {
                    WorkPriority.URGENT: "[red bold]URGENT[/red bold]",
                    WorkPriority.HIGH: "[yellow]HIGH[/yellow]",
                    WorkPriority.NORMAL: "[white]NORMAL[/white]",
                    WorkPriority.LOW: "[dim]LOW[/dim]"
                }
                priority_str = priority_colors.get(top_item.priority, str(top_item.priority.value))

            # Color-code pending count
            if hook['pending_count'] > 5:
                pending_count = f"[red bold]{pending_count}[/red bold]"
            elif hook['pending_count'] > 2:
                pending_count = f"[yellow]{pending_count}[/yellow]"
            elif hook['pending_count'] > 0:
                pending_count = f"[green]{pending_count}[/green]"
            else:
                pending_count = f"[dim]{pending_count}[/dim]"

            table.add_row(agent_name, hook_id, pending_count, top_work, priority_str)

        return Panel(table, title="🪝 Hook System", title_align="left")

    def render_convoys_panel(self, data: Dict[str, Any]) -> Panel:
        """Render the convoy system status panel."""
        convoy_data = data['convoys']

        if convoy_data.get('error'):
            content = f"[red]Error: {convoy_data['error']}[/red]"
        elif not self.show_convoy_details:
            content = f"Active convoys: {convoy_data['count']}"
        else:
            # Parse convoy output for detailed display
            raw_output = convoy_data.get('raw_output', '')
            if raw_output:
                lines = [line.strip() for line in raw_output.split('\n') if line.strip()]
                content = "\n".join(lines[-10:])  # Last 10 lines
            else:
                content = f"Active convoys: {convoy_data['count']}"

        return Panel(content, title="🚚 Convoy System", title_align="left")

    def render_sessions_panel(self, data: Dict[str, Any]) -> Panel:
        """Render the tmux sessions panel."""
        session_data = data['sessions']

        if session_data.get('error'):
            content = f"[red]Error: {session_data['error']}[/red]"
        elif not self.show_session_details:
            agent_count = len(session_data.get('agent_sessions', []))
            total_count = session_data.get('total', 0)
            content = f"Total: {total_count} | Agent sessions: {agent_count}"
        else:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Session", style="cyan", width=15)
            table.add_column("Windows", width=10)
            table.add_column("Status", width=10)

            for session in session_data.get('agent_sessions', []):
                status_color = "[green]attached[/green]" if session['status'] == 'attached' else "[dim]detached[/dim]"
                table.add_row(session['name'], session['windows'], status_color)

            content = table if session_data.get('agent_sessions') else "No agent sessions detected"

        return Panel(content, title="📺 Agent Sessions", title_align="left")

    def render_gupp_panel(self, data: Dict[str, Any]) -> Panel:
        """Render the GUPP auto-execution status panel."""
        gupp_data = data['gupp']

        status_lines = []

        # Availability
        if gupp_data['available']:
            status_lines.append("⚡ GUPP System: [green]Available[/green]")
        else:
            status_lines.append("⚡ GUPP System: [red]Not Found[/red]")

        # Running status
        if gupp_data['running']:
            status_lines.append("🔧 Daemon: [green]Running[/green]")
        else:
            status_lines.append("🔧 Daemon: [yellow]Stopped[/yellow]")

        # Last nudge
        if gupp_data['last_nudge']:
            time_ago = time.time() - gupp_data['last_nudge']
            if time_ago < 60:
                status_lines.append(f"📨 Last nudge: [green]{time_ago:.0f}s ago[/green]")
            elif time_ago < 300:  # 5 minutes
                status_lines.append(f"📨 Last nudge: [yellow]{time_ago/60:.1f}m ago[/yellow]")
            else:
                status_lines.append(f"📨 Last nudge: [red]{time_ago/60:.1f}m ago[/red]")
        else:
            status_lines.append("📨 Last nudge: [dim]None[/dim]")

        # Errors
        if gupp_data.get('error'):
            status_lines.append(f"[red]Error: {gupp_data['error']}[/red]")

        content = "\n".join(status_lines)
        return Panel(content, title="⚡ GUPP Auto-Execution", title_align="left")

    def render_system_panel(self, data: Dict[str, Any]) -> Panel:
        """Render the system metrics panel."""
        metrics = data['metrics']

        lines = []
        lines.append(f"Uptime: {metrics.get('uptime', 0):.1f}s")
        lines.append(f"Refreshes: {metrics.get('refresh_count', 0)}")
        lines.append(f"Interval: {self.refresh_interval}s")

        if metrics.get('hooks_per_second', 0) > 0:
            lines.append(f"Hook rate: {metrics['hooks_per_second']:.1f}/s")

        content = "\n".join(lines)
        return Panel(content, title="📊 System Metrics", title_align="left")

    def render_footer(self) -> Panel:
        """Render the dashboard footer with key bindings."""
        bindings = [
            "q: Quit",
            "r: Refresh",
            "Space: Pause/Resume",
            "h: Toggle hooks",
            "c: Toggle convoys",
            "s: Toggle sessions"
        ]
        footer_text = " | ".join(bindings)
        return Panel(footer_text, style="dim")

    def render_dashboard(self, data: Dict[str, Any]) -> Layout:
        """Render the complete dashboard."""
        layout = self.create_layout()

        # Render all panels
        layout["header"].update(self.render_header(data))
        layout["hooks"].update(self.render_hooks_panel(data))
        layout["convoys"].update(self.render_convoys_panel(data))
        layout["sessions"].update(self.render_sessions_panel(data))
        layout["gupp"].update(self.render_gupp_panel(data))
        layout["system"].update(self.render_system_panel(data))
        layout["footer"].update(self.render_footer())

        return layout

    def handle_keypress(self, key: str) -> bool:
        """Handle keyboard input. Returns False to quit."""
        if key.lower() in ['q', '\x03']:  # q or Ctrl-C
            return False
        elif key == 'r':
            self.cached_data = {}  # Force refresh
        elif key == ' ':
            self.auto_refresh = not self.auto_refresh
        elif key == 'h':
            self.show_hook_details = not self.show_hook_details
        elif key == 'c':
            self.show_convoy_details = not self.show_convoy_details
        elif key == 's':
            self.show_session_details = not self.show_session_details

        return True

    def run_dashboard_fallback(self):
        """Run a simple text-based dashboard without Rich."""
        print("🏭 GAS TOWN DASHBOARD (Text Mode)")
        print("=" * 50)
        print("Rich library not available. Install with: pip install rich")
        print("Running basic text dashboard...\n")

        try:
            while self.running:
                data = self.gather_system_data()

                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')

                print(f"🏭 GAS TOWN DASHBOARD - {datetime.fromtimestamp(data['timestamp']).strftime('%H:%M:%S')}")
                print("=" * 50)

                # Hook system
                hooks = data['hooks']
                print(f"\n🪝 HOOK SYSTEM:")
                print(f"   Total hooks: {hooks['total']}")
                print(f"   Pending work: {hooks['pending_work']}")

                for hook in hooks['details'][:5]:  # Show first 5
                    if 'error' not in hook:
                        print(f"   • {hook['agent_name']}: {hook['pending_count']} pending")

                # Convoy system
                if CONVOY_AVAILABLE:
                    convoys = data['convoys']
                    print(f"\n🚚 CONVOY SYSTEM:")
                    print(f"   Active convoys: {convoys['count']}")
                    if convoys.get('error'):
                        print(f"   Error: {convoys['error']}")

                # Sessions
                sessions = data['sessions']
                print(f"\n📺 TMUX SESSIONS:")
                print(f"   Total: {sessions['total']}")
                print(f"   Agent sessions: {len(sessions.get('agent_sessions', []))}")
                if sessions.get('error'):
                    print(f"   Error: {sessions['error']}")

                # GUPP status
                gupp = data['gupp']
                print(f"\n⚡ GUPP AUTO-EXECUTION:")
                print(f"   Available: {'Yes' if gupp['available'] else 'No'}")
                print(f"   Running: {'Yes' if gupp['running'] else 'No'}")
                if gupp.get('error'):
                    print(f"   Error: {gupp['error']}")

                print(f"\nPress Ctrl-C to quit. Auto-refresh every {self.refresh_interval}s")

                time.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            print("\n\n👋 Gas Town Dashboard stopped.")

    def run_dashboard(self):
        """Run the real-time dashboard."""
        if not RICH_AVAILABLE:
            self.run_dashboard_fallback()
            return

        try:
            # Initial data load
            data = self.gather_system_data()

            with Live(self.render_dashboard(data), refresh_per_second=4, screen=True) as live:
                last_refresh = time.time()

                while True:
                    current_time = time.time()

                    # Auto-refresh check
                    if self.auto_refresh and (current_time - last_refresh) >= self.refresh_interval:
                        data = self.gather_system_data()
                        last_refresh = current_time
                        live.update(self.render_dashboard(data))

                    # Check for keyboard input (simplified for demo)
                    # In a full implementation, would use proper keyboard handling
                    time.sleep(0.1)

        except KeyboardInterrupt:
            self.console.print("\n\n👋 Gas Town Dashboard stopped.", style="bold green")


def main():
    """Main dashboard entry point."""
    dashboard = GasTownDashboard()

    try:
        dashboard.run_dashboard()
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())