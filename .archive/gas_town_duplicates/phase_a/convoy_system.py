#!/usr/bin/env python3
"""
Convoy Work Bundling System - Gas Town Phase A Implementation
============================================================

Convoys bundle related work items with dependency tracking, visual progress,
and swarm assignment for coordinated multi-agent execution.
"""

import json
import uuid
import sqlite3
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path


class ConvoyManager:
    """Central convoy management and coordination."""

    def __init__(self, db_path: str = "/home/ubuntu/.beads/convoy.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize convoy database tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create convoy tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS convoys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                convoy_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                convoy_type TEXT DEFAULT 'feature',
                created_ts TEXT NOT NULL,
                completed_ts TEXT,
                total_work_items INTEGER DEFAULT 0,
                completed_work_items INTEGER DEFAULT 0,
                progress_percentage REAL DEFAULT 0.0,
                created_by_agent TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS convoy_work_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                convoy_id INTEGER NOT NULL,
                bead_id TEXT NOT NULL,
                bead_title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                assigned_agent TEXT,
                assigned_at TEXT,
                completed_at TEXT,
                parallel_group INTEGER,
                execution_order INTEGER DEFAULT 0,
                FOREIGN KEY (convoy_id) REFERENCES convoys (id),
                UNIQUE (convoy_id, bead_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS convoy_status_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                convoy_id INTEGER NOT NULL,
                agent_name TEXT,
                update_type TEXT NOT NULL,
                message TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (convoy_id) REFERENCES convoys (id)
            )
        """)

        conn.commit()
        conn.close()

    def create_convoy(
        self,
        creator_agent: str,
        name: str,
        description: str = "",
        bead_ids: Optional[List[str]] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Create a new convoy with optional initial work items."""

        convoy_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create convoy record
        cursor.execute("""
            INSERT INTO convoys (
                convoy_id, name, description, priority, created_ts, created_by_agent
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (convoy_id, name, description, priority, now, creator_agent))

        db_convoy_id = cursor.lastrowid

        # Add initial work items if provided
        if bead_ids:
            for i, bead_id in enumerate(bead_ids):
                bead_title = self._get_bead_title(bead_id)
                cursor.execute("""
                    INSERT INTO convoy_work_items (
                        convoy_id, bead_id, bead_title, execution_order
                    ) VALUES (?, ?, ?, ?)
                """, (db_convoy_id, bead_id, bead_title, i))

            cursor.execute("""
                UPDATE convoys SET total_work_items = ? WHERE id = ?
            """, (len(bead_ids), db_convoy_id))

        # Record creation event
        cursor.execute("""
            INSERT INTO convoy_status_updates (
                convoy_id, agent_name, update_type, message, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            db_convoy_id, creator_agent, "created",
            f"Convoy '{name}' created with {len(bead_ids or [])} work items",
            now
        ))

        conn.commit()
        conn.close()

        return {
            "convoy_id": convoy_id,
            "name": name,
            "status": "active",
            "work_items": len(bead_ids or [])
        }

    def assign_work_item(self, convoy_id: str, bead_id: str, agent_name: str) -> Dict[str, Any]:
        """Assign work item to agent (Gas Town 'sling' mechanism)."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get convoy internal ID
        cursor.execute("SELECT id FROM convoys WHERE convoy_id = ?", (convoy_id,))
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Convoy {convoy_id} not found")
        db_convoy_id = result[0]

        now = datetime.now(timezone.utc).isoformat()

        # Update work item assignment
        cursor.execute("""
            UPDATE convoy_work_items
            SET assigned_agent = ?, assigned_at = ?, status = 'assigned'
            WHERE convoy_id = ? AND bead_id = ?
        """, (agent_name, now, db_convoy_id, bead_id))

        if cursor.rowcount == 0:
            raise ValueError(f"Work item {bead_id} not found in convoy {convoy_id}")

        # Record assignment
        cursor.execute("""
            INSERT INTO convoy_status_updates (
                convoy_id, agent_name, update_type, message, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            db_convoy_id, agent_name, "work_assigned",
            f"Work slung: {bead_id} → {agent_name}",
            now
        ))

        conn.commit()
        conn.close()

        return {"bead_id": bead_id, "assigned_agent": agent_name, "status": "assigned"}

    def get_convoy_status(self, convoy_id: str) -> Dict[str, Any]:
        """Get comprehensive convoy status."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get convoy details
        cursor.execute("""
            SELECT * FROM convoys WHERE convoy_id = ?
        """, (convoy_id,))
        convoy_row = cursor.fetchone()

        if not convoy_row:
            raise ValueError(f"Convoy {convoy_id} not found")

        # Get work items
        cursor.execute("""
            SELECT bead_id, bead_title, status, assigned_agent
            FROM convoy_work_items
            WHERE convoy_id = (SELECT id FROM convoys WHERE convoy_id = ?)
            ORDER BY execution_order
        """, (convoy_id,))
        work_items = cursor.fetchall()

        conn.close()

        # Convert convoy row to dict
        columns = ["id", "convoy_id", "name", "description", "priority", "status",
                  "convoy_type", "created_ts", "completed_ts", "total_work_items",
                  "completed_work_items", "progress_percentage", "created_by_agent"]
        convoy_dict = dict(zip(columns, convoy_row))

        return {
            "convoy_id": convoy_id,
            "name": convoy_dict["name"],
            "status": convoy_dict["status"],
            "progress": convoy_dict["progress_percentage"],
            "work_items": {
                "total": convoy_dict["total_work_items"],
                "completed": convoy_dict["completed_work_items"],
                "items": [
                    {
                        "bead_id": item[0],
                        "title": item[1],
                        "status": item[2],
                        "assigned_agent": item[3]
                    } for item in work_items
                ]
            },
            "created": convoy_dict["created_ts"],
            "created_by": convoy_dict["created_by_agent"]
        }

    def list_convoys(self) -> List[Dict[str, Any]]:
        """List all convoys."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT convoy_id, name, status, progress_percentage, total_work_items, created_ts
            FROM convoys ORDER BY created_ts DESC
        """)
        convoys = cursor.fetchall()
        conn.close()

        return [
            {
                "convoy_id": row[0],
                "name": row[1],
                "status": row[2],
                "progress": row[3],
                "work_items": row[4],
                "created": row[5]
            } for row in convoys
        ]

    def _get_bead_title(self, bead_id: str) -> str:
        """Get bead title from beads system."""
        try:
            result = subprocess.run(
                ["bd", "show", bead_id, "--json"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bead_data = json.loads(result.stdout)
                return bead_data.get("title", f"Work item: {bead_id}")
        except:
            pass
        return f"Work item: {bead_id}"


# CLI Commands for Mayor

def create_convoy_command(name: str, bead_ids: List[str], description: str = ""):
    """Mayor command to create a convoy."""
    try:
        with open("/home/ubuntu/.claude/agent-state.json") as f:
            state = json.load(f)
            agent_name = state.get("agent_name", "UnknownAgent")
    except:
        agent_name = "UnknownAgent"

    manager = ConvoyManager()
    convoy = manager.create_convoy(agent_name, name, description, bead_ids)

    return f"✅ Convoy '{name}' created!\n" \
           f"   ID: {convoy['convoy_id']}\n" \
           f"   Work items: {convoy['work_items']}"

def sling_work_command(convoy_id: str, bead_id: str, agent_name: str):
    """Mayor command to sling work to an agent."""
    manager = ConvoyManager()
    result = manager.assign_work_item(convoy_id, bead_id, agent_name)

    return f"✅ Work slung!\n" \
           f"   {result['bead_id']} → {result['assigned_agent']}"

def convoy_status_command(convoy_id: str):
    """Mayor command to get convoy status."""
    manager = ConvoyManager()
    status = manager.get_convoy_status(convoy_id)

    output = [
        f"📊 Convoy: {status['name']} ({status['convoy_id']})",
        f"   Status: {status['status']} | Progress: {status['progress']:.1f}%",
        f"   Work Items: {status['work_items']['completed']}/{status['work_items']['total']}"
    ]

    if status['work_items']['items']:
        output.append("\n   Items:")
        for item in status['work_items']['items']:
            agent = f" → {item['assigned_agent']}" if item['assigned_agent'] else ""
            output.append(f"     • {item['bead_id']}: {item['status']}{agent}")

    return "\n".join(output)

def list_convoys_command():
    """Mayor command to list convoys."""
    manager = ConvoyManager()
    convoys = manager.list_convoys()

    if not convoys:
        return "📋 No convoys found."

    output = ["📋 Convoys:"]
    for convoy in convoys:
        status_emoji = "✅" if convoy['status'] == 'completed' else "🚧"
        output.append(
            f"   {status_emoji} {convoy['name']} ({convoy['convoy_id']}) "
            f"- {convoy['progress']:.1f}%"
        )

    return "\n".join(output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python convoy_system.py <command> [args...]")
        print("Commands: create, sling, status, list")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "create" and len(sys.argv) >= 4:
            name = sys.argv[2]
            bead_ids = sys.argv[3].split(",")
            description = sys.argv[4] if len(sys.argv) > 4 else ""
            print(create_convoy_command(name, bead_ids, description))

        elif command == "sling" and len(sys.argv) >= 5:
            convoy_id = sys.argv[2]
            bead_id = sys.argv[3]
            agent_name = sys.argv[4]
            print(sling_work_command(convoy_id, bead_id, agent_name))

        elif command == "status" and len(sys.argv) >= 3:
            convoy_id = sys.argv[2]
            print(convoy_status_command(convoy_id))

        elif command == "list":
            print(list_convoys_command())

        else:
            print("Invalid command or missing arguments")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)