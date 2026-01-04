#!/usr/bin/env python3
"""
Hook-Based Work Distribution System - Gas Town Phase A Implementation
====================================================================

Implements per-agent persistent work queues (hooks) with autonomous activation.
Core principle: "If your hook has work, YOU MUST RUN IT"
"""

import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path


class HookManager:
    """Manages agent hooks and work distribution."""

    def __init__(self, db_path: str = "/home/ubuntu/.beads/hooks.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize hook database tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Agent hooks table - each agent has one hook
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_hooks (
                agent_name TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                last_checked TEXT,
                status TEXT DEFAULT 'active'
            )
        """)

        # Hook work items - work assigned to agent hooks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hook_work_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                work_type TEXT NOT NULL,
                work_item_id TEXT NOT NULL,
                work_data TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                assigned_at TEXT NOT NULL,
                picked_up_at TEXT,
                completed_at TEXT,
                status TEXT DEFAULT 'pending',
                convoy_id TEXT,
                FOREIGN KEY (agent_name) REFERENCES agent_hooks (agent_name),
                UNIQUE (agent_name, work_item_id)
            )
        """)

        # Hook activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hook_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)

        conn.commit()
        conn.close()

    def create_hook(self, agent_name: str) -> Dict[str, Any]:
        """Create a hook for an agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()

        try:
            cursor.execute("""
                INSERT INTO agent_hooks (agent_name, created_at)
                VALUES (?, ?)
            """, (agent_name, now))

            self._log_activity(cursor, agent_name, "hook_created",
                              f"Hook created for agent {agent_name}")

            conn.commit()
            return {"agent_name": agent_name, "status": "created"}

        except sqlite3.IntegrityError:
            # Hook already exists
            return {"agent_name": agent_name, "status": "exists"}
        finally:
            conn.close()

    def sling_work_to_hook(
        self,
        agent_name: str,
        work_type: str,
        work_item_id: str,
        work_data: Dict[str, Any],
        priority: int = 5,
        convoy_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sling work to an agent's hook.
        This is the core Gas Town mechanism for work distribution.
        """

        # Ensure agent has a hook
        self.create_hook(agent_name)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()

        try:
            cursor.execute("""
                INSERT INTO hook_work_items (
                    agent_name, work_type, work_item_id, work_data,
                    priority, assigned_at, convoy_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_name, work_type, work_item_id, json.dumps(work_data),
                priority, now, convoy_id
            ))

            self._log_activity(cursor, agent_name, "work_slung",
                              f"Work slung: {work_type} {work_item_id} (priority {priority})")

            conn.commit()

            return {
                "agent_name": agent_name,
                "work_item_id": work_item_id,
                "status": "slung",
                "priority": priority
            }

        except sqlite3.IntegrityError:
            return {
                "agent_name": agent_name,
                "work_item_id": work_item_id,
                "status": "already_assigned",
                "error": "Work item already on this agent's hook"
            }
        finally:
            conn.close()

    def check_hook(self, agent_name: str) -> Dict[str, Any]:
        """
        Check an agent's hook for work.
        Returns pending work items in priority order.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update last checked time
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE agent_hooks SET last_checked = ? WHERE agent_name = ?
        """, (now, agent_name))

        # Get pending work items
        cursor.execute("""
            SELECT work_type, work_item_id, work_data, priority, assigned_at, convoy_id
            FROM hook_work_items
            WHERE agent_name = ? AND status = 'pending'
            ORDER BY priority ASC, assigned_at ASC
        """, (agent_name,))

        work_items = cursor.fetchall()

        if work_items:
            self._log_activity(cursor, agent_name, "hook_checked",
                              f"Hook checked: {len(work_items)} pending items")

        conn.commit()
        conn.close()

        return {
            "agent_name": agent_name,
            "has_work": len(work_items) > 0,
            "work_count": len(work_items),
            "work_items": [
                {
                    "work_type": item[0],
                    "work_item_id": item[1],
                    "work_data": json.loads(item[2]),
                    "priority": item[3],
                    "assigned_at": item[4],
                    "convoy_id": item[5]
                }
                for item in work_items
            ]
        }

    def pick_up_work(self, agent_name: str, work_item_id: str) -> Dict[str, Any]:
        """
        Mark work item as picked up by agent.
        This happens when agent starts working on the item.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            UPDATE hook_work_items
            SET status = 'in_progress', picked_up_at = ?
            WHERE agent_name = ? AND work_item_id = ? AND status = 'pending'
        """, (now, agent_name, work_item_id))

        if cursor.rowcount == 0:
            conn.close()
            return {
                "status": "error",
                "message": "Work item not found or already picked up"
            }

        self._log_activity(cursor, agent_name, "work_picked_up",
                          f"Work picked up: {work_item_id}")

        conn.commit()
        conn.close()

        return {
            "agent_name": agent_name,
            "work_item_id": work_item_id,
            "status": "picked_up"
        }

    def complete_work(self, agent_name: str, work_item_id: str) -> Dict[str, Any]:
        """
        Mark work item as completed.
        This removes it from the agent's hook.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            UPDATE hook_work_items
            SET status = 'completed', completed_at = ?
            WHERE agent_name = ? AND work_item_id = ? AND status = 'in_progress'
        """, (now, agent_name, work_item_id))

        if cursor.rowcount == 0:
            conn.close()
            return {
                "status": "error",
                "message": "Work item not found or not in progress"
            }

        self._log_activity(cursor, agent_name, "work_completed",
                          f"Work completed: {work_item_id}")

        conn.commit()
        conn.close()

        return {
            "agent_name": agent_name,
            "work_item_id": work_item_id,
            "status": "completed"
        }

    def get_hook_status(self, agent_name: str) -> Dict[str, Any]:
        """Get comprehensive hook status for an agent."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get hook info
        cursor.execute("""
            SELECT created_at, last_checked, status
            FROM agent_hooks
            WHERE agent_name = ?
        """, (agent_name,))

        hook_info = cursor.fetchone()
        if not hook_info:
            conn.close()
            return {"status": "no_hook", "agent_name": agent_name}

        # Get work item counts by status
        cursor.execute("""
            SELECT status, COUNT(*) FROM hook_work_items
            WHERE agent_name = ?
            GROUP BY status
        """, (agent_name,))

        status_counts = dict(cursor.fetchall())

        # Get recent activity
        cursor.execute("""
            SELECT activity_type, message, timestamp
            FROM hook_activity
            WHERE agent_name = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """, (agent_name,))

        recent_activity = cursor.fetchall()

        conn.close()

        return {
            "agent_name": agent_name,
            "hook": {
                "created_at": hook_info[0],
                "last_checked": hook_info[1],
                "status": hook_info[2]
            },
            "work_counts": {
                "pending": status_counts.get("pending", 0),
                "in_progress": status_counts.get("in_progress", 0),
                "completed": status_counts.get("completed", 0)
            },
            "recent_activity": [
                {
                    "activity": activity[0],
                    "message": activity[1],
                    "timestamp": activity[2]
                }
                for activity in recent_activity
            ]
        }

    def list_all_hooks(self) -> List[Dict[str, Any]]:
        """List all agent hooks and their status."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ah.agent_name, ah.created_at, ah.last_checked, ah.status,
                   COUNT(hwi.id) as total_work,
                   SUM(CASE WHEN hwi.status = 'pending' THEN 1 ELSE 0 END) as pending_work
            FROM agent_hooks ah
            LEFT JOIN hook_work_items hwi ON ah.agent_name = hwi.agent_name
            GROUP BY ah.agent_name
            ORDER BY pending_work DESC, ah.agent_name
        """)

        hooks = cursor.fetchall()
        conn.close()

        return [
            {
                "agent_name": hook[0],
                "created_at": hook[1],
                "last_checked": hook[2],
                "status": hook[3],
                "total_work": hook[4],
                "pending_work": hook[5]
            }
            for hook in hooks
        ]

    def _log_activity(self, cursor, agent_name: str, activity_type: str, message: str, metadata: Optional[Dict] = None):
        """Log activity to the hook activity table."""
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO hook_activity (agent_name, activity_type, message, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_name, activity_type, message, now, json.dumps(metadata or {})))


# CLI Commands for Hook Management

def check_my_hook():
    """Check current agent's hook for work."""
    try:
        with open("/home/ubuntu/.claude/agent-state.json") as f:
            state = json.load(f)
            agent_name = state.get("agent_name", "UnknownAgent")
    except:
        agent_name = "UnknownAgent"

    manager = HookManager()
    result = manager.check_hook(agent_name)

    if result["has_work"]:
        output = [f"🎣 Hook has {result['work_count']} work items:"]
        for item in result["work_items"]:
            convoy_info = f" (convoy: {item['convoy_id']})" if item['convoy_id'] else ""
            output.append(f"   • {item['work_item_id']} ({item['work_type']}) - priority {item['priority']}{convoy_info}")

        output.append(f"\n🚀 GUPP Protocol: YOU MUST RUN IT!")
        return "\n".join(output)
    else:
        return f"📭 Hook empty for agent {agent_name}"

def sling_work_command(agent_name: str, work_type: str, work_item_id: str, priority: int = 5):
    """Sling work to an agent's hook."""
    manager = HookManager()

    # Create basic work data
    work_data = {
        "item_id": work_item_id,
        "type": work_type,
        "slung_at": datetime.now(timezone.utc).isoformat()
    }

    result = manager.sling_work_to_hook(
        agent_name=agent_name,
        work_type=work_type,
        work_item_id=work_item_id,
        work_data=work_data,
        priority=priority
    )

    if result["status"] == "slung":
        return f"🎯 Work slung to {agent_name}!\n" \
               f"   {work_item_id} ({work_type}) - priority {priority}\n" \
               f"   Agent will pick up automatically on next activation"
    else:
        return f"❌ Failed to sling work: {result.get('error', 'Unknown error')}"

def hook_status_command(agent_name: str = None):
    """Get hook status for agent."""
    if not agent_name:
        try:
            with open("/home/ubuntu/.claude/agent-state.json") as f:
                state = json.load(f)
                agent_name = state.get("agent_name", "UnknownAgent")
        except:
            agent_name = "UnknownAgent"

    manager = HookManager()
    status = manager.get_hook_status(agent_name)

    if status.get("status") == "no_hook":
        return f"❌ No hook found for agent {agent_name}"

    output = [
        f"🎣 Hook Status: {agent_name}",
        f"   Created: {status['hook']['created_at']}",
        f"   Last checked: {status['hook']['last_checked'] or 'Never'}",
        f"   Status: {status['hook']['status']}",
        f"",
        f"   Work Items:",
        f"     Pending: {status['work_counts']['pending']}",
        f"     In Progress: {status['work_counts']['in_progress']}",
        f"     Completed: {status['work_counts']['completed']}"
    ]

    if status['recent_activity']:
        output.append("\n   Recent Activity:")
        for activity in status['recent_activity']:
            output.append(f"     • {activity['activity']}: {activity['message']}")

    return "\n".join(output)

def list_all_hooks_command():
    """List all agent hooks."""
    manager = HookManager()
    hooks = manager.list_all_hooks()

    if not hooks:
        return "📭 No hooks found"

    output = ["🎣 All Agent Hooks:"]
    for hook in hooks:
        pending_indicator = f" ({hook['pending_work']} pending)" if hook['pending_work'] > 0 else ""
        output.append(f"   • {hook['agent_name']}: {hook['status']}{pending_indicator}")

    return "\n".join(output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hook_system.py <command> [args...]")
        print("Commands: check, sling, status, list")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "check":
            print(check_my_hook())

        elif command == "sling" and len(sys.argv) >= 5:
            agent_name = sys.argv[2]
            work_type = sys.argv[3]
            work_item_id = sys.argv[4]
            priority = int(sys.argv[5]) if len(sys.argv) > 5 else 5
            print(sling_work_command(agent_name, work_type, work_item_id, priority))

        elif command == "status":
            agent_name = sys.argv[2] if len(sys.argv) > 2 else None
            print(hook_status_command(agent_name))

        elif command == "list":
            print(list_all_hooks_command())

        else:
            print("Invalid command or missing arguments")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)