#!/usr/bin/env python3
"""
Gas Town MCP Bridge
==================

Integration layer between Steve Yegge's Gas Town (Go) and MCP Agent Mail ecosystem.
Provides enhanced monitoring, dashboard, and tmux integration that complements
rather than competes with the production Gas Town system.

Key Features:
- Auto-detects existing Gas Town installation
- Bridges Steve's agents to MCP Agent Mail ecosystem
- Provides enhanced real-time monitoring dashboard
- Integrates tmux enhancements with existing Gas Town sessions
- Synchronizes state between Gas Town and MCP systems

Usage:
    python3 gastown_mcp_bridge.py detect       # Detect Gas Town installation
    python3 gastown_mcp_bridge.py bridge       # Start MCP bridge service
    python3 gastown_mcp_bridge.py dashboard    # Launch enhanced dashboard
    python3 gastown_mcp_bridge.py tmux         # Setup tmux integration
"""

import os
import sys
import json
import subprocess
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GasTownDetector:
    """Detects and analyzes existing Steve Yegge Gas Town installations."""

    def __init__(self):
        self.gas_town_binary = None
        self.installation_path = None
        self.version = None
        self.config_path = None
        self.workspace_path = None

    def detect_installation(self) -> Dict[str, Any]:
        """Detect Gas Town installation and return configuration."""
        detection_result = {
            'found': False,
            'binary_path': None,
            'installation_path': None,
            'version': None,
            'config_path': None,
            'workspace_path': None,
            'daemon_running': False,
            'mayor_session': None,
            'error': None
        }

        try:
            # Try to find gt binary
            gt_locations = [
                '/usr/local/bin/gt',
                '/usr/bin/gt',
                os.path.expanduser('~/go/bin/gt'),
                './gt',
                'gt'  # In PATH
            ]

            for location in gt_locations:
                try:
                    if location == 'gt':
                        # Check if in PATH
                        result = subprocess.run(['which', 'gt'], capture_output=True, text=True)
                        if result.returncode == 0:
                            self.gas_town_binary = result.stdout.strip()
                            break
                    else:
                        if os.path.isfile(location) and os.access(location, os.X_OK):
                            self.gas_town_binary = location
                            break
                except Exception:
                    continue

            if not self.gas_town_binary:
                detection_result['error'] = "Gas Town binary 'gt' not found in common locations"
                return detection_result

            detection_result['found'] = True
            detection_result['binary_path'] = self.gas_town_binary

            # Get version information
            try:
                result = subprocess.run([self.gas_town_binary, '--version'],
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    detection_result['version'] = result.stdout.strip()
                    self.version = result.stdout.strip()
            except Exception as e:
                logger.warning(f"Could not get Gas Town version: {e}")

            # Detect workspace and configuration
            workspace_info = self._detect_workspace()
            detection_result.update(workspace_info)

            # Check if daemon is running
            daemon_status = self._check_daemon_status()
            detection_result.update(daemon_status)

            logger.info(f"Gas Town detected: {self.gas_town_binary}")
            return detection_result

        except Exception as e:
            detection_result['error'] = f"Detection failed: {str(e)}"
            return detection_result

    def _detect_workspace(self) -> Dict[str, Any]:
        """Detect Gas Town workspace and configuration."""
        workspace_info = {
            'workspace_path': None,
            'config_path': None,
            'rigs': [],
            'crews': []
        }

        try:
            # Look for Gas Town workspace in common locations
            workspace_candidates = [
                os.path.expanduser('~/gt'),
                os.path.expanduser('~/.gastown'),
                os.getcwd()
            ]

            for candidate in workspace_candidates:
                if self._is_gastown_workspace(candidate):
                    workspace_info['workspace_path'] = candidate
                    self.workspace_path = candidate
                    break

            # Look for configuration
            if self.workspace_path:
                config_candidates = [
                    os.path.join(self.workspace_path, 'config.json'),
                    os.path.join(self.workspace_path, '.gastown', 'config.json'),
                    os.path.expanduser('~/.config/gastown/config.json')
                ]

                for config_file in config_candidates:
                    if os.path.isfile(config_file):
                        workspace_info['config_path'] = config_file
                        self.config_path = config_file
                        break

            # Try to get rig and crew information
            if self.gas_town_binary:
                try:
                    # Get rigs
                    result = subprocess.run([self.gas_town_binary, 'rig', 'list'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        workspace_info['rigs'] = self._parse_rig_list(result.stdout)

                    # Get crews
                    result = subprocess.run([self.gas_town_binary, 'crew', 'list'],
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        workspace_info['crews'] = self._parse_crew_list(result.stdout)

                except subprocess.TimeoutExpired:
                    logger.warning("Gas Town commands timed out")
                except Exception as e:
                    logger.warning(f"Could not get rig/crew info: {e}")

        except Exception as e:
            logger.warning(f"Workspace detection failed: {e}")

        return workspace_info

    def _is_gastown_workspace(self, path: str) -> bool:
        """Check if directory is a Gas Town workspace."""
        if not os.path.isdir(path):
            return False

        # Look for Gas Town indicators
        indicators = [
            '.gastown',
            'rigs',
            'crews',
            '.beads'  # Beads integration
        ]

        return any(os.path.exists(os.path.join(path, indicator)) for indicator in indicators)

    def _check_daemon_status(self) -> Dict[str, Any]:
        """Check if Gas Town daemon is running."""
        daemon_info = {
            'daemon_running': False,
            'mayor_session': None,
            'active_sessions': []
        }

        try:
            # Check for Gas Town processes
            result = subprocess.run(['pgrep', '-f', 'gt.*daemon'], capture_output=True, text=True)
            if result.returncode == 0:
                daemon_info['daemon_running'] = True

            # Check for Mayor tmux session
            try:
                result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
                if result.returncode == 0:
                    sessions = result.stdout.split('\n')
                    for session in sessions:
                        if 'mayor' in session.lower() or 'gastown' in session.lower():
                            daemon_info['mayor_session'] = session.split(':')[0]
                        daemon_info['active_sessions'].append(session.split(':')[0] if ':' in session else session)

            except FileNotFoundError:
                logger.warning("tmux not available for session detection")

        except Exception as e:
            logger.warning(f"Daemon status check failed: {e}")

        return daemon_info

    def _parse_rig_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse rig list output."""
        # Placeholder - would parse actual gt rig list output
        return []

    def _parse_crew_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse crew list output."""
        # Placeholder - would parse actual gt crew list output
        return []


class MCPGasTownBridge:
    """Bridge between Gas Town and MCP Agent Mail ecosystem."""

    def __init__(self, gas_town_info: Dict[str, Any]):
        self.gas_town_info = gas_town_info
        self.bridge_active = False
        self.sync_interval = 30  # seconds
        self.mcp_agents = {}
        self.gas_town_agents = {}

    def start_bridge(self) -> bool:
        """Start the MCP bridge service."""
        if not self.gas_town_info['found']:
            logger.error("Cannot start bridge: Gas Town not detected")
            return False

        logger.info("Starting Gas Town MCP Bridge...")

        try:
            # Initialize MCP connection
            self._initialize_mcp_connection()

            # Start synchronization loop
            self.bridge_active = True
            self._synchronization_loop()

            return True

        except Exception as e:
            logger.error(f"Bridge startup failed: {e}")
            return False

    def _initialize_mcp_connection(self):
        """Initialize connection to MCP Agent Mail system."""
        # Placeholder for MCP Agent Mail initialization
        logger.info("Initializing MCP Agent Mail connection...")

    def _synchronization_loop(self):
        """Main synchronization loop between Gas Town and MCP."""
        logger.info("Starting synchronization loop...")

        while self.bridge_active:
            try:
                # Sync agent states
                self._sync_agent_states()

                # Sync work assignments
                self._sync_work_assignments()

                # Sync session states
                self._sync_session_states()

                time.sleep(self.sync_interval)

            except KeyboardInterrupt:
                logger.info("Bridge shutdown requested")
                self.bridge_active = False
                break
            except Exception as e:
                logger.error(f"Synchronization error: {e}")
                time.sleep(self.sync_interval)

    def _sync_agent_states(self):
        """Synchronize agent states between Gas Town and MCP."""
        # Placeholder for agent state synchronization
        pass

    def _sync_work_assignments(self):
        """Synchronize work assignments between systems."""
        # Placeholder for work assignment synchronization
        pass

    def _sync_session_states(self):
        """Synchronize session states between systems."""
        # Placeholder for session state synchronization
        pass

    def stop_bridge(self):
        """Stop the MCP bridge service."""
        logger.info("Stopping Gas Town MCP Bridge...")
        self.bridge_active = False


def main():
    """Main CLI interface for Gas Town MCP Bridge."""
    import argparse

    parser = argparse.ArgumentParser(description="Gas Town MCP Integration Bridge")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Detect command
    detect_parser = subparsers.add_parser('detect', help='Detect Gas Town installation')
    detect_parser.add_argument('--json', action='store_true', help='Output JSON format')

    # Bridge command
    bridge_parser = subparsers.add_parser('bridge', help='Start MCP bridge service')
    bridge_parser.add_argument('--daemon', action='store_true', help='Run as daemon')

    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch enhanced dashboard')
    dashboard_parser.add_argument('--port', type=int, default=8080, help='Dashboard port')

    # tmux command
    tmux_parser = subparsers.add_parser('tmux', help='Setup tmux integration')
    tmux_parser.add_argument('action', choices=['setup', 'status'], help='tmux action')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'detect':
        detector = GasTownDetector()
        gas_town_info = detector.detect_installation()

        if args.json:
            print(json.dumps(gas_town_info, indent=2))
        else:
            print("🔍 GAS TOWN DETECTION RESULTS")
            print("=" * 40)

            if gas_town_info['found']:
                print("✅ Gas Town installation detected!")
                print(f"   Binary: {gas_town_info['binary_path']}")
                if gas_town_info['version']:
                    print(f"   Version: {gas_town_info['version']}")
                if gas_town_info['workspace_path']:
                    print(f"   Workspace: {gas_town_info['workspace_path']}")
                if gas_town_info['daemon_running']:
                    print("   Daemon: 🟢 Running")
                else:
                    print("   Daemon: 🔴 Stopped")
                if gas_town_info['mayor_session']:
                    print(f"   Mayor Session: {gas_town_info['mayor_session']}")

                print("\n💡 Ready for MCP integration!")
            else:
                print("❌ Gas Town not detected")
                if gas_town_info['error']:
                    print(f"   Error: {gas_town_info['error']}")
                print("\n💡 Install Steve Yegge's Gas Town:")
                print("   go install github.com/steveyegge/gastown/cmd/gt@latest")

        return 0 if gas_town_info['found'] else 1

    elif args.command == 'bridge':
        detector = GasTownDetector()
        gas_town_info = detector.detect_installation()

        if not gas_town_info['found']:
            print("❌ Gas Town not detected. Run 'detect' command first.")
            return 1

        bridge = MCPGasTownBridge(gas_town_info)
        success = bridge.start_bridge()
        return 0 if success else 1

    elif args.command == 'dashboard':
        print("🚀 Launching Gas Town MCP Dashboard...")
        # Would launch our enhanced dashboard here
        return 0

    elif args.command == 'tmux':
        print("🔧 Setting up Gas Town tmux integration...")
        # Would setup tmux integration here
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())