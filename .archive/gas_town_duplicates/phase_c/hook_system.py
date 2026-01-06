#!/usr/bin/env python3
"""
Gas Town Hook System - GUPP Implementation
==========================================

Implements the core Gas Town Universal Propulsion Principle (GUPP):
"If there is work on your hook, YOU MUST RUN IT"

Each agent has a personal hook (special pinned bead) where work gets "slung".
Agents must check their hook on startup and execute any work found.
"""

import json
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class HookState(Enum):
    """Hook work states."""
    PENDING = "pending"
    CLAIMED = "claimed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkPriority(Enum):
    """Work priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class HookWork:
    """Represents work slung to an agent's hook."""
    work_id: str
    agent_name: str
    work_type: str  # "molecule", "bead", "convoy", "task"
    work_reference: str  # ID of the actual work item
    priority: WorkPriority
    slung_at: str  # ISO timestamp
    slung_by: str  # Agent that slung the work
    state: HookState
    claimed_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_data: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    reason: Optional[str] = None  # Why this work was slung

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['priority'] = self.priority.value
        data['state'] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HookWork':
        """Create from dictionary."""
        data = data.copy()
        data['priority'] = WorkPriority(data['priority'])
        data['state'] = HookState(data['state'])
        return cls(**data)


class GasTownHookSystem:
    """
    Core Gas Town hook system implementing GUPP.

    Each agent gets a personal hook where work is slung.
    Agents must check and execute hook work automatically.
    """

    def __init__(self, db_path: str = "/home/ubuntu/.gas_town/hooks.db"):
        """Initialize hook system."""
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize hook database."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Agent hooks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_hooks (
                agent_name TEXT PRIMARY KEY,
                hook_id TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                last_checked TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                hook_metadata TEXT DEFAULT '{}'
            )
        """)

        # Hook work table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hook_work (
                work_id TEXT PRIMARY KEY,
                agent_name TEXT NOT NULL,
                work_type TEXT NOT NULL,
                work_reference TEXT NOT NULL,
                priority TEXT NOT NULL,
                slung_at TEXT NOT NULL,
                slung_by TEXT NOT NULL,
                state TEXT NOT NULL,
                claimed_at TEXT,
                completed_at TEXT,
                execution_data TEXT,
                retry_count INTEGER DEFAULT 0,
                reason TEXT,
                FOREIGN KEY (agent_name) REFERENCES agent_hooks (agent_name)
            )
        """)

        # Hook activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hook_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                activity_data TEXT DEFAULT '{}',
                timestamp TEXT NOT NULL
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hook_work_agent ON hook_work (agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hook_work_state ON hook_work (state)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hook_activity_agent ON hook_activity (agent_name)")

        conn.commit()
        conn.close()

    def create_agent_hook(self, agent_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a personal hook for an agent.

        Returns:
            hook_id: Unique identifier for the agent's hook
        """
        hook_id = f"hook-{agent_name}-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata or {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agent_hooks
            (agent_name, hook_id, created_at, hook_metadata)
            VALUES (?, ?, ?, ?)
        """, (agent_name, hook_id, now, metadata_json))

        # Log hook creation
        self._log_activity(cursor, agent_name, "hook_created", {"hook_id": hook_id})

        conn.commit()
        conn.close()

        print(f"🪝 Created hook for {agent_name}: {hook_id}")
        return hook_id

    def sling_work(
        self,
        agent_name: str,
        work_type: str,
        work_reference: str,
        slung_by: str,
        priority: WorkPriority = WorkPriority.NORMAL,
        reason: Optional[str] = None
    ) -> str:
        """
        Sling work to an agent's hook.

        This is the core Gas Town work distribution mechanism.

        Args:
            agent_name: Target agent
            work_type: Type of work ("molecule", "bead", "convoy", "task")
            work_reference: ID of the work item
            slung_by: Agent doing the slinging
            priority: Work priority
            reason: Why this work is being slung

        Returns:
            work_id: Unique identifier for this work assignment
        """
        # Ensure agent has a hook
        if not self.get_agent_hook(agent_name):
            self.create_agent_hook(agent_name)

        work_id = f"work-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()

        hook_work = HookWork(
            work_id=work_id,
            agent_name=agent_name,
            work_type=work_type,
            work_reference=work_reference,
            priority=priority,
            slung_at=now,
            slung_by=slung_by,
            state=HookState.PENDING,
            reason=reason
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Store the work
        work_data = hook_work.to_dict()
        cursor.execute("""
            INSERT INTO hook_work (
                work_id, agent_name, work_type, work_reference, priority,
                slung_at, slung_by, state, reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            work_data['work_id'], work_data['agent_name'], work_data['work_type'],
            work_data['work_reference'], work_data['priority'], work_data['slung_at'],
            work_data['slung_by'], work_data['state'], work_data['reason']
        ))

        # Log the sling
        self._log_activity(cursor, agent_name, "work_slung", {
            "work_id": work_id,
            "work_type": work_type,
            "work_reference": work_reference,
            "slung_by": slung_by,
            "priority": priority.value
        })

        conn.commit()
        conn.close()

        print(f"🎯 Slung work to {agent_name}: {work_type}:{work_reference} (priority: {priority.value})")
        return work_id

    def check_hook(self, agent_name: str) -> List[HookWork]:
        """
        Check an agent's hook for pending work.

        This is called by agents on startup to implement GUPP.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Update last checked time
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE agent_hooks
            SET last_checked = ?
            WHERE agent_name = ?
        """, (now, agent_name))

        # Get pending work, ordered by priority and slung_at
        cursor.execute("""
            SELECT * FROM hook_work
            WHERE agent_name = ? AND state = ?
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    WHEN 'low' THEN 4
                END,
                slung_at ASC
        """, (agent_name, HookState.PENDING.value))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Convert to HookWork objects
        pending_work = []
        for row in rows:
            work_dict = dict(zip(columns, row))
            # Handle None values
            for key in ['claimed_at', 'completed_at', 'execution_data', 'reason']:
                if work_dict[key] is None:
                    work_dict[key] = None
                elif key == 'execution_data' and work_dict[key]:
                    work_dict[key] = json.loads(work_dict[key])

            pending_work.append(HookWork.from_dict(work_dict))

        # Log hook check
        self._log_activity(cursor, agent_name, "hook_checked", {
            "pending_work_count": len(pending_work),
            "checked_at": now
        })

        conn.commit()
        conn.close()

        if pending_work:
            print(f"🪝 {agent_name} hook check: {len(pending_work)} pending work items")
        else:
            print(f"🪝 {agent_name} hook check: No pending work")

        return pending_work

    def claim_work(self, agent_name: str, work_id: str) -> bool:
        """
        Claim work from hook (mark as being executed).

        Returns:
            bool: True if successfully claimed, False if already claimed/completed
        """
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Try to claim the work (atomic update)
        cursor.execute("""
            UPDATE hook_work
            SET state = ?, claimed_at = ?
            WHERE work_id = ? AND agent_name = ? AND state = ?
        """, (HookState.CLAIMED.value, now, work_id, agent_name, HookState.PENDING.value))

        claimed = cursor.rowcount > 0

        if claimed:
            self._log_activity(cursor, agent_name, "work_claimed", {
                "work_id": work_id,
                "claimed_at": now
            })
            print(f"✅ {agent_name} claimed work: {work_id}")
        else:
            print(f"⚠️ {agent_name} could not claim work: {work_id} (already claimed or completed)")

        conn.commit()
        conn.close()

        return claimed

    def start_execution(self, agent_name: str, work_id: str, execution_data: Optional[Dict[str, Any]] = None) -> bool:
        """Mark work as executing."""
        now = datetime.now(timezone.utc).isoformat()
        execution_json = json.dumps(execution_data or {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE hook_work
            SET state = ?, execution_data = ?
            WHERE work_id = ? AND agent_name = ? AND state = ?
        """, (HookState.EXECUTING.value, execution_json, work_id, agent_name, HookState.CLAIMED.value))

        started = cursor.rowcount > 0

        if started:
            self._log_activity(cursor, agent_name, "execution_started", {
                "work_id": work_id,
                "started_at": now,
                "execution_data": execution_data
            })

        conn.commit()
        conn.close()

        return started

    def complete_work(
        self,
        agent_name: str,
        work_id: str,
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark work as completed on the hook.

        Returns:
            bool: True if successfully completed
        """
        now = datetime.now(timezone.utc).isoformat()
        result_json = json.dumps(result_data or {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE hook_work
            SET state = ?, completed_at = ?, execution_data = ?
            WHERE work_id = ? AND agent_name = ? AND state IN (?, ?)
        """, (
            HookState.COMPLETED.value, now, result_json,
            work_id, agent_name,
            HookState.CLAIMED.value, HookState.EXECUTING.value
        ))

        completed = cursor.rowcount > 0

        if completed:
            self._log_activity(cursor, agent_name, "work_completed", {
                "work_id": work_id,
                "completed_at": now,
                "result_data": result_data
            })
            print(f"🎉 {agent_name} completed work: {work_id}")
        else:
            print(f"⚠️ Could not complete work: {work_id} (not found or wrong state)")

        conn.commit()
        conn.close()

        return completed

    def fail_work(
        self,
        agent_name: str,
        work_id: str,
        error_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark work as failed."""
        now = datetime.now(timezone.utc).isoformat()
        error_json = json.dumps(error_data or {})

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Increment retry count
        cursor.execute("""
            UPDATE hook_work
            SET state = ?, execution_data = ?, retry_count = retry_count + 1
            WHERE work_id = ? AND agent_name = ?
        """, (HookState.FAILED.value, error_json, work_id, agent_name))

        failed = cursor.rowcount > 0

        if failed:
            self._log_activity(cursor, agent_name, "work_failed", {
                "work_id": work_id,
                "failed_at": now,
                "error_data": error_data
            })

        conn.commit()
        conn.close()

        return failed

    def get_agent_hook(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent's hook information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM agent_hooks WHERE agent_name = ?
        """, (agent_name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            columns = [desc[0] for desc in cursor.description]
            hook_data = dict(zip(columns, row))
            hook_data['hook_metadata'] = json.loads(hook_data['hook_metadata'])
            return hook_data

        return None

    def get_hook_status(self, agent_name: str) -> Dict[str, Any]:
        """Get comprehensive hook status for an agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get hook info
        hook = self.get_agent_hook(agent_name)
        if not hook:
            return {"error": "No hook found for agent"}

        # Get work summary
        cursor.execute("""
            SELECT state, COUNT(*) as count
            FROM hook_work
            WHERE agent_name = ?
            GROUP BY state
        """, (agent_name,))

        work_summary = {row[0]: row[1] for row in cursor.fetchall()}

        # Get recent activity
        cursor.execute("""
            SELECT activity_type, activity_data, timestamp
            FROM hook_activity
            WHERE agent_name = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (agent_name,))

        recent_activity = []
        for row in cursor.fetchall():
            activity_data = json.loads(row[1]) if row[1] else {}
            recent_activity.append({
                "activity_type": row[0],
                "activity_data": activity_data,
                "timestamp": row[2]
            })

        conn.close()

        return {
            "agent_name": agent_name,
            "hook_id": hook["hook_id"],
            "created_at": hook["created_at"],
            "last_checked": hook["last_checked"],
            "is_active": hook["is_active"],
            "work_summary": work_summary,
            "recent_activity": recent_activity
        }

    def list_all_hooks(self) -> List[Dict[str, Any]]:
        """List all agent hooks in the system."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ah.*, COUNT(hw.work_id) as pending_work
            FROM agent_hooks ah
            LEFT JOIN hook_work hw ON ah.agent_name = hw.agent_name
                AND hw.state = ?
            WHERE ah.is_active = TRUE
            GROUP BY ah.agent_name
            ORDER BY ah.created_at DESC
        """, (HookState.PENDING.value,))

        hooks = []
        for row in cursor.fetchall():
            hook_data = {
                "agent_name": row[0],
                "hook_id": row[1],
                "created_at": row[2],
                "last_checked": row[3],
                "is_active": row[4],
                "hook_metadata": json.loads(row[5]),
                "pending_work": row[6]
            }
            hooks.append(hook_data)

        conn.close()
        return hooks

    def _log_activity(
        self,
        cursor: sqlite3.Cursor,
        agent_name: str,
        activity_type: str,
        activity_data: Dict[str, Any]
    ) -> None:
        """Log activity to the hook activity table."""
        now = datetime.now(timezone.utc).isoformat()
        activity_json = json.dumps(activity_data)

        cursor.execute("""
            INSERT INTO hook_activity (agent_name, activity_type, activity_data, timestamp)
            VALUES (?, ?, ?, ?)
        """, (agent_name, activity_type, activity_json, now))

    def cleanup_completed_work(self, days: int = 7) -> int:
        """Clean up completed work older than specified days."""
        cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = cutoff.replace(day=cutoff.day - days).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM hook_work
            WHERE state IN (?, ?) AND completed_at < ?
        """, (HookState.COMPLETED.value, HookState.FAILED.value, cutoff))

        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"🧹 Cleaned up {deleted} completed work items older than {days} days")
        return deleted


# CLI Functions for gt commands

def create_hook_cli(agent_name: str) -> str:
    """CLI function to create an agent hook."""
    hook_system = GasTownHookSystem()
    hook_id = hook_system.create_agent_hook(agent_name)
    return f"✅ Created hook for {agent_name}: {hook_id}"


def sling_work_cli(
    agent_name: str,
    work_type: str,
    work_reference: str,
    slung_by: str = "CLI",
    priority: str = "normal",
    reason: Optional[str] = None
) -> str:
    """CLI function to sling work to an agent."""
    hook_system = GasTownHookSystem()

    try:
        priority_enum = WorkPriority(priority.lower())
    except ValueError:
        return f"❌ Invalid priority: {priority}. Use: low, normal, high, urgent"

    work_id = hook_system.sling_work(
        agent_name, work_type, work_reference, slung_by, priority_enum, reason
    )

    return f"✅ Slung {work_type}:{work_reference} to {agent_name} (work_id: {work_id})"


def check_hook_cli(agent_name: str) -> str:
    """CLI function to check an agent's hook."""
    hook_system = GasTownHookSystem()
    pending_work = hook_system.check_hook(agent_name)

    if not pending_work:
        return f"🪝 {agent_name}: No pending work on hook"

    output = [f"🪝 {agent_name}: {len(pending_work)} pending work items:"]

    for work in pending_work:
        priority_indicator = {
            WorkPriority.URGENT: "🔴",
            WorkPriority.HIGH: "🟠",
            WorkPriority.NORMAL: "🟡",
            WorkPriority.LOW: "🟢"
        }.get(work.priority, "⚪")

        output.append(f"  {priority_indicator} {work.work_type}:{work.work_reference} "
                     f"(slung by {work.slung_by}, priority: {work.priority.value})")

        if work.reason:
            output.append(f"     Reason: {work.reason}")

    return "\n".join(output)


def hook_status_cli(agent_name: str) -> str:
    """CLI function to get hook status."""
    hook_system = GasTownHookSystem()
    status = hook_system.get_hook_status(agent_name)

    if "error" in status:
        return f"❌ {status['error']}"

    output = [
        f"🪝 Hook Status: {agent_name}",
        f"   Hook ID: {status['hook_id']}",
        f"   Created: {status['created_at']}",
        f"   Last Checked: {status['last_checked'] or 'Never'}",
        f"   Active: {status['is_active']}"
    ]

    if status['work_summary']:
        output.append("   Work Summary:")
        for state, count in status['work_summary'].items():
            output.append(f"     {state}: {count}")

    return "\n".join(output)


def list_hooks_cli() -> str:
    """CLI function to list all hooks."""
    hook_system = GasTownHookSystem()
    hooks = hook_system.list_all_hooks()

    if not hooks:
        return "🪝 No active hooks found"

    output = [f"🪝 Active Hooks ({len(hooks)}):"]

    for hook in hooks:
        pending = f" ({hook['pending_work']} pending)" if hook['pending_work'] > 0 else ""
        output.append(f"  • {hook['agent_name']}: {hook['hook_id']}{pending}")

    return "\n".join(output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python hook_system.py <command> [args...]")
        print("Commands: create, sling, check, status, list")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "create" and len(sys.argv) >= 3:
            agent_name = sys.argv[2]
            print(create_hook_cli(agent_name))

        elif command == "sling" and len(sys.argv) >= 6:
            agent_name = sys.argv[2]
            work_type = sys.argv[3]
            work_reference = sys.argv[4]
            slung_by = sys.argv[5]
            priority = sys.argv[6] if len(sys.argv) > 6 else "normal"
            reason = sys.argv[7] if len(sys.argv) > 7 else None
            print(sling_work_cli(agent_name, work_type, work_reference, slung_by, priority, reason))

        elif command == "check" and len(sys.argv) >= 3:
            agent_name = sys.argv[2]
            print(check_hook_cli(agent_name))

        elif command == "status" and len(sys.argv) >= 3:
            agent_name = sys.argv[2]
            print(hook_status_cli(agent_name))

        elif command == "list":
            print(list_hooks_cli())

        else:
            print("Invalid command or missing arguments")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)