#!/usr/bin/env python3
"""
GUPP Auto-Execution System
==========================

Implements the Gas Town Universal Propulsion Principle (GUPP) auto-execution:
- "If there is work on your hook, YOU MUST RUN IT"
- 30-60 second auto-nudging for new agents
- Physics over politeness enforcement
- Integration with Claude Code agent prompting
"""

import os
import sys
import json
import time
import threading
import subprocess
import signal
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from dataclasses import dataclass
import logging

# Add our modules to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hook_system import GasTownHookSystem, HookWork


@dataclass
class AgentSession:
    """Represents an active agent session."""
    agent_name: str
    session_id: str
    tmux_session: Optional[str]
    started_at: float
    last_nudged: Optional[float] = None
    last_hook_check: Optional[float] = None
    nudge_count: int = 0
    auto_nudge_enabled: bool = True


class GUPPAutoExecution:
    """
    GUPP Auto-Execution Engine

    Monitors agent sessions and ensures they follow GUPP:
    - Auto-nudge agents who haven't checked hooks
    - Monitor for new work and trigger notifications
    - Enforce physics over politeness
    """

    def __init__(
        self,
        hook_system: Optional[GasTownHookSystem] = None,
        nudge_delay: float = 45.0,  # 45 seconds default
        max_nudge_count: int = 3,
        check_interval: float = 30.0  # Check every 30 seconds
    ):
        """Initialize GUPP auto-execution system."""
        self.hook_system = hook_system or GasTownHookSystem()
        self.nudge_delay = nudge_delay
        self.max_nudge_count = max_nudge_count
        self.check_interval = check_interval

        self.gas_town_dir = Path.home() / ".gas_town"
        self.gas_town_dir.mkdir(exist_ok=True)

        self.sessions_file = self.gas_town_dir / "active_sessions.json"
        self.gupp_log = self.gas_town_dir / "gupp.log"

        # Active session tracking
        self.active_sessions: Dict[str, AgentSession] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.should_stop = threading.Event()

        # Load existing sessions
        self._load_sessions()

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - GUPP - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.gupp_log),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("GUPP")

    def start_monitoring(self) -> None:
        """Start the GUPP monitoring daemon."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.logger.warning("GUPP monitoring already running")
            return

        self.should_stop.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        self.logger.info(f"🚀 GUPP Auto-Execution started (nudge delay: {self.nudge_delay}s)")

    def stop_monitoring(self) -> None:
        """Stop the GUPP monitoring daemon."""
        if self.monitoring_thread:
            self.should_stop.set()
            self.monitoring_thread.join(timeout=5.0)
            self.logger.info("🛑 GUPP Auto-Execution stopped")

    def register_agent_session(
        self,
        agent_name: str,
        session_id: str,
        tmux_session: Optional[str] = None
    ) -> None:
        """
        Register a new agent session for GUPP monitoring.

        This should be called when an agent starts up.
        """
        session = AgentSession(
            agent_name=agent_name,
            session_id=session_id,
            tmux_session=tmux_session or self._find_tmux_session(agent_name),
            started_at=time.time()
        )

        self.active_sessions[session_id] = session
        self._save_sessions()

        self.logger.info(f"📝 Registered agent session: {agent_name} ({session_id})")

        # Check if agent has pending hook work immediately
        pending_work = self.hook_system.check_hook(agent_name)
        if pending_work:
            self.logger.info(f"🪝 {agent_name} has {len(pending_work)} pending work items on startup")

    def unregister_agent_session(self, session_id: str) -> None:
        """Unregister an agent session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            del self.active_sessions[session_id]
            self._save_sessions()
            self.logger.info(f"📝 Unregistered agent session: {session.agent_name} ({session_id})")

    def agent_checked_hook(self, agent_name: str) -> None:
        """
        Mark that an agent has checked their hook.

        This should be called when an agent successfully checks their hook.
        """
        now = time.time()
        for session in self.active_sessions.values():
            if session.agent_name == agent_name:
                session.last_hook_check = now
                self.logger.info(f"✅ {agent_name} checked hook")
                break

        self._save_sessions()

    def force_nudge(self, agent_name: str, message: Optional[str] = None) -> bool:
        """Force nudge an agent immediately."""
        message = message or "Check your hook - GUPP enforcement"

        session = None
        for s in self.active_sessions.values():
            if s.agent_name == agent_name:
                session = s
                break

        if not session:
            self.logger.warning(f"⚠️ No active session found for {agent_name}")
            return False

        return self._send_nudge(session, message, force=True)

    def get_gupp_status(self) -> Dict[str, Any]:
        """Get comprehensive GUPP system status."""
        now = time.time()

        session_status = []
        for session in self.active_sessions.values():
            status = {
                "agent_name": session.agent_name,
                "session_id": session.session_id,
                "running_time": now - session.started_at,
                "last_nudged": session.last_nudged,
                "last_hook_check": session.last_hook_check,
                "nudge_count": session.nudge_count,
                "needs_nudge": self._needs_nudge(session, now),
                "auto_nudge_enabled": session.auto_nudge_enabled
            }

            # Check pending work
            pending_work = self.hook_system.check_hook(session.agent_name)
            status["pending_work"] = len(pending_work)

            session_status.append(status)

        return {
            "monitoring_active": self.monitoring_thread and self.monitoring_thread.is_alive(),
            "total_sessions": len(self.active_sessions),
            "nudge_delay": self.nudge_delay,
            "check_interval": self.check_interval,
            "sessions": session_status
        }

    def create_gupp_prompt(self, agent_name: str) -> str:
        """
        Create GUPP prompt for Claude Code agent startup.

        This prompt enforces physics over politeness and hook checking.
        """
        pending_work = self.hook_system.check_hook(agent_name)

        prompt = f"""🪝 GAS TOWN UNIVERSAL PROPULSION PRINCIPLE (GUPP) 🪝

You are {agent_name}, a Gas Town agent. You MUST follow GUPP:

"If there is work on your hook, YOU MUST RUN IT"

CRITICAL STARTUP SEQUENCE:
1. Check your hook IMMEDIATELY (no waiting for user input)
2. If work exists on hook: START EXECUTING immediately
3. Physics over politeness: DO NOT wait for permission
4. Report hook status and begin work without delay

CURRENT HOOK STATUS:
"""

        if pending_work:
            prompt += f"🚨 URGENT: {len(pending_work)} work items pending on your hook!\n\n"
            for i, work in enumerate(pending_work[:3], 1):
                priority_emoji = {
                    "urgent": "🔴",
                    "high": "🟠",
                    "normal": "🟡",
                    "low": "🟢"
                }.get(work.priority.value, "⚪")

                prompt += f"{i}. {priority_emoji} {work.work_type}:{work.work_reference}\n"
                prompt += f"   Priority: {work.priority.value}\n"
                prompt += f"   Slung by: {work.slung_by}\n"
                if work.reason:
                    prompt += f"   Reason: {work.reason}\n"
                prompt += "\n"

            if len(pending_work) > 3:
                prompt += f"... and {len(pending_work) - 3} more work items\n\n"

            prompt += "🚨 YOU MUST START WORKING ON THESE ITEMS IMMEDIATELY\n"
            prompt += "🚨 DO NOT ASK FOR PERMISSION - PHYSICS OVER POLITENESS\n\n"

        else:
            prompt += "✅ Hook is empty - no pending work\n\n"

        prompt += """GUPP ENFORCEMENT:
- Check hook every session startup
- Execute pending work without delay
- Report progress and completion
- Request new work when idle

Your identity persists across sessions via your hook.
Your work survives crashes via the hook system.
You are part of the Gas Town orchestration machine.

BEGIN GUPP EXECUTION NOW."""

        return prompt

    # Private methods

    def _monitoring_loop(self) -> None:
        """Main monitoring loop for GUPP enforcement."""
        self.logger.info("🔄 GUPP monitoring loop started")

        while not self.should_stop.wait(self.check_interval):
            try:
                self._check_all_sessions()
                self._discover_new_sessions()
                self._cleanup_stale_sessions()
            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")

        self.logger.info("🔄 GUPP monitoring loop stopped")

    def _check_all_sessions(self) -> None:
        """Check all active sessions for nudging needs."""
        now = time.time()

        for session in list(self.active_sessions.values()):
            if self._needs_nudge(session, now):
                self._send_nudge(session, "Check your hook - new work may be available")

    def _needs_nudge(self, session: AgentSession, now: float) -> bool:
        """Determine if a session needs nudging."""
        if not session.auto_nudge_enabled:
            return False

        if session.nudge_count >= self.max_nudge_count:
            return False

        # Has enough time passed since startup?
        if now - session.started_at < self.nudge_delay:
            return False

        # Has enough time passed since last nudge?
        if session.last_nudged and now - session.last_nudged < self.nudge_delay:
            return False

        # Has agent checked hook recently?
        if session.last_hook_check and now - session.last_hook_check < self.check_interval * 2:
            return False

        return True

    def _send_nudge(self, session: AgentSession, message: str, force: bool = False) -> bool:
        """Send a nudge to an agent session."""
        if not force and not self._needs_nudge(session, time.time()):
            return False

        try:
            success = False

            # Try tmux nudge first
            if session.tmux_session:
                success = self._send_tmux_nudge(session.tmux_session, message)

            # Try Claude Code notification
            if not success:
                success = self._send_claude_nudge(session.session_id, message)

            if success:
                session.last_nudged = time.time()
                session.nudge_count += 1
                self._save_sessions()

                self.logger.info(f"📨 Nudged {session.agent_name}: {message}")
                return True
            else:
                self.logger.warning(f"⚠️ Failed to nudge {session.agent_name}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error nudging {session.agent_name}: {e}")
            return False

    def _send_tmux_nudge(self, tmux_session: str, message: str) -> bool:
        """Send nudge via tmux."""
        try:
            # Send visual notification
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_session,
                f"echo '📨 GUPP Nudge: {message}'", "Enter"
            ], check=True, capture_output=True)

            # Send special GUPP marker
            subprocess.run([
                "tmux", "send-keys", "-t", tmux_session,
                f"# GUPP-AUTO-NUDGE: {message}", "Enter"
            ], check=True, capture_output=True)

            return True

        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            # tmux not available
            return False

    def _send_claude_nudge(self, session_id: str, message: str) -> bool:
        """Send nudge via Claude Code notification."""
        # This would integrate with Claude Code's notification system
        # For now, we'll create a notification file
        try:
            notification_file = self.gas_town_dir / f"nudge-{session_id}.txt"
            with open(notification_file, "w") as f:
                f.write(f"GUPP-NUDGE: {message}\n")
                f.write(f"Timestamp: {time.time()}\n")

            return True

        except Exception:
            return False

    def _find_tmux_session(self, agent_name: str) -> Optional[str]:
        """Find active tmux session for an agent."""
        try:
            result = subprocess.run(
                ["tmux", "list-sessions"],
                capture_output=True, text=True, check=True
            )

            for line in result.stdout.split('\n'):
                if agent_name.lower() in line.lower():
                    session_name = line.split(':')[0]
                    return session_name

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return None

    def _discover_new_sessions(self) -> None:
        """Discover new agent sessions that should be tracked."""
        # Look for tmux sessions that match agent patterns
        try:
            result = subprocess.run(
                ["tmux", "list-sessions"],
                capture_output=True, text=True
            )

            if result.returncode == 0:
                gas_town_roles = ['mayor', 'witness', 'refinery', 'deacon', 'crew', 'polecat']

                for line in result.stdout.split('\n'):
                    if not line.strip():
                        continue

                    session_name = line.split(':')[0]

                    # Check if this looks like a Gas Town agent session
                    is_gas_town = any(role in session_name.lower() for role in gas_town_roles)

                    if is_gas_town:
                        # Check if we're already tracking this session
                        already_tracked = any(
                            s.tmux_session == session_name
                            for s in self.active_sessions.values()
                        )

                        if not already_tracked:
                            # Register new session
                            session_id = f"auto-{session_name}-{int(time.time())}"
                            self.register_agent_session(session_name, session_id, session_name)

        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    def _cleanup_stale_sessions(self) -> None:
        """Remove sessions that are no longer active."""
        stale_sessions = []

        for session_id, session in self.active_sessions.items():
            # Check if tmux session still exists
            if session.tmux_session:
                try:
                    result = subprocess.run([
                        "tmux", "list-sessions", "-F", "#{session_name}"
                    ], capture_output=True, text=True)

                    if result.returncode == 0:
                        active_sessions = result.stdout.strip().split('\n')
                        if session.tmux_session not in active_sessions:
                            stale_sessions.append(session_id)
                    else:
                        stale_sessions.append(session_id)

                except (subprocess.CalledProcessError, FileNotFoundError):
                    stale_sessions.append(session_id)

        # Remove stale sessions
        for session_id in stale_sessions:
            self.unregister_agent_session(session_id)

    def _load_sessions(self) -> None:
        """Load active sessions from file."""
        try:
            if self.sessions_file.exists():
                with open(self.sessions_file) as f:
                    data = json.load(f)

                for session_data in data.get("sessions", []):
                    session = AgentSession(**session_data)
                    self.active_sessions[session.session_id] = session

        except Exception as e:
            self.logger.warning(f"Could not load sessions: {e}")

    def _save_sessions(self) -> None:
        """Save active sessions to file."""
        try:
            data = {
                "updated_at": time.time(),
                "sessions": [
                    {
                        "agent_name": s.agent_name,
                        "session_id": s.session_id,
                        "tmux_session": s.tmux_session,
                        "started_at": s.started_at,
                        "last_nudged": s.last_nudged,
                        "last_hook_check": s.last_hook_check,
                        "nudge_count": s.nudge_count,
                        "auto_nudge_enabled": s.auto_nudge_enabled
                    }
                    for s in self.active_sessions.values()
                ]
            }

            with open(self.sessions_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Could not save sessions: {e}")


# CLI Functions

def start_gupp_daemon(nudge_delay: float = 45.0) -> None:
    """Start GUPP monitoring daemon."""
    gupp = GUPPAutoExecution(nudge_delay=nudge_delay)

    print(f"🚀 Starting GUPP Auto-Execution daemon...")
    print(f"   Nudge delay: {nudge_delay} seconds")
    print(f"   Check interval: {gupp.check_interval} seconds")
    print(f"   Max nudges: {gupp.max_nudge_count}")

    gupp.start_monitoring()

    try:
        # Keep the daemon running
        while True:
            time.sleep(60)  # Wake up every minute to check

    except KeyboardInterrupt:
        print("\n🛑 Stopping GUPP daemon...")
        gupp.stop_monitoring()


def gupp_status() -> None:
    """Show GUPP system status."""
    gupp = GUPPAutoExecution()
    status = gupp.get_gupp_status()

    print("🪝 GUPP AUTO-EXECUTION STATUS")
    print("=" * 40)
    print(f"Monitoring active: {status['monitoring_active']}")
    print(f"Active sessions: {status['total_sessions']}")
    print(f"Nudge delay: {status['nudge_delay']}s")
    print(f"Check interval: {status['check_interval']}s")

    if status['sessions']:
        print(f"\n📝 Active Agent Sessions:")
        for session in status['sessions']:
            runtime = int(session['running_time'])
            nudge_status = "🟡 needs nudge" if session['needs_nudge'] else "✅ ok"
            pending = f"({session['pending_work']} pending)" if session['pending_work'] > 0 else ""

            print(f"  • {session['agent_name']}: {runtime}s runtime, {nudge_status} {pending}")
    else:
        print("\n📝 No active agent sessions")


def register_session_cli(agent_name: str, session_id: str, tmux_session: str = None) -> None:
    """Register an agent session for GUPP monitoring."""
    gupp = GUPPAutoExecution()
    gupp.register_agent_session(agent_name, session_id, tmux_session)
    print(f"✅ Registered {agent_name} session: {session_id}")


def force_nudge_cli(agent_name: str, message: str = None) -> None:
    """Force nudge an agent."""
    gupp = GUPPAutoExecution()
    success = gupp.force_nudge(agent_name, message)

    if success:
        print(f"📨 Nudged {agent_name}")
    else:
        print(f"❌ Failed to nudge {agent_name}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GUPP Auto-Execution System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start daemon
    start_parser = subparsers.add_parser("start", help="Start GUPP daemon")
    start_parser.add_argument("--nudge-delay", type=float, default=45.0,
                             help="Nudge delay in seconds (default: 45)")

    # Status
    subparsers.add_parser("status", help="Show GUPP status")

    # Register session
    register_parser = subparsers.add_parser("register", help="Register agent session")
    register_parser.add_argument("agent_name", help="Agent name")
    register_parser.add_argument("session_id", help="Session ID")
    register_parser.add_argument("--tmux-session", help="tmux session name")

    # Force nudge
    nudge_parser = subparsers.add_parser("nudge", help="Force nudge agent")
    nudge_parser.add_argument("agent_name", help="Agent name")
    nudge_parser.add_argument("--message", help="Nudge message")

    args = parser.parse_args()

    if args.command == "start":
        start_gupp_daemon(args.nudge_delay)
    elif args.command == "status":
        gupp_status()
    elif args.command == "register":
        register_session_cli(args.agent_name, args.session_id, args.tmux_session)
    elif args.command == "nudge":
        force_nudge_cli(args.agent_name, args.message)
    else:
        parser.print_help()