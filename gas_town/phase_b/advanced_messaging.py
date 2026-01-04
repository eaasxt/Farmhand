#!/usr/bin/env python3
"""
Advanced Messaging Architecture - Gas Town Phase B Implementation
================================================================

Sophisticated messaging with multi-destination routing, workflow embedding,
Git-backed audit trails, and complex dependency DAG support.

Core Gas Town Principles:
- Messages ARE workflows (molecules embedded in messages)
- Git version control for all communication audit trails
- Complex routing: channel/role/broadcast with intelligent delivery
- Dependency DAG for message coordination and workflow orchestration
"""

import json
import sqlite3
import hashlib
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Set
from pathlib import Path
import enum
from dataclasses import dataclass, asdict
import asyncio
import git


class MessageType(enum.Enum):
    """Enhanced message types for Gas Town communication."""
    DIRECT = "direct"                    # Agent-to-agent direct message
    BROADCAST = "broadcast"              # All agents in project
    CHANNEL = "channel"                  # Topic-based channel communication
    ROLE_BASED = "role_based"           # Message to specific role (mayor, witness, etc.)
    WORKFLOW_EMBEDDED = "workflow"       # Message contains executable workflow (molecule)
    CONVOY_COORDINATION = "convoy"       # Convoy-specific coordination
    DEPENDENCY_SIGNAL = "dependency"     # Dependency graph signaling
    AUDIT_TRAIL = "audit"               # System audit and compliance
    EMERGENCY = "emergency"              # High-priority system alerts


class MessagePriority(enum.Enum):
    """Message priority levels for routing and processing."""
    CRITICAL = 0    # Emergency alerts, system failures
    HIGH = 1        # Convoy coordination, important updates
    NORMAL = 2      # Standard agent communication
    LOW = 3         # Informational updates, logs
    BACKGROUND = 4  # Metrics, background processing


class RoutingStrategy(enum.Enum):
    """Message routing and delivery strategies."""
    IMMEDIATE = "immediate"              # Send immediately, synchronous
    QUEUED = "queued"                   # Add to queue, asynchronous delivery
    BROADCAST_PARALLEL = "broadcast_parallel"  # Parallel delivery to all recipients
    DEPENDENCY_ORDERED = "dependency_ordered"  # Respect dependency ordering
    ROLE_HIERARCHY = "role_hierarchy"   # Follow Gas Town role hierarchy


@dataclass
class MessageRecipient:
    """Enhanced recipient specification for complex routing."""
    type: str                           # "agent", "role", "channel", "convoy"
    identifier: str                     # Agent name, role name, channel name, convoy ID
    required: bool = True               # Is delivery to this recipient required?
    acknowledgment_required: bool = False  # Does recipient need to acknowledge?
    timeout_seconds: int = 300          # Delivery timeout


@dataclass
class WorkflowEmbedding:
    """Workflow (molecule) embedded in message for execution."""
    workflow_type: str                  # "molecule", "convoy_task", "dependency_signal"
    workflow_id: str                    # Unique workflow identifier
    workflow_content: Dict[str, Any]    # The actual workflow definition
    execution_context: Dict[str, Any]   # Context for workflow execution
    dependency_requirements: List[str] = None  # Required dependencies for execution
    auto_execute: bool = True           # Should workflow execute automatically?


@dataclass
class DependencyNode:
    """Node in the message dependency DAG."""
    node_id: str                        # Unique node identifier
    message_id: str                     # Associated message ID
    dependencies: Set[str]              # Set of dependency node IDs
    dependents: Set[str]                # Set of dependent node IDs
    status: str                         # "pending", "ready", "processing", "completed", "failed"
    metadata: Dict[str, Any] = None     # Additional node metadata


class AdvancedMessagingSystem:
    """Advanced messaging with routing, workflows, and audit trails."""

    def __init__(
        self,
        db_path: str = "/home/ubuntu/.beads/advanced_messaging.db",
        git_audit_path: str = "/home/ubuntu/.claude/message_audit"
    ):
        self.db_path = db_path
        self.git_audit_path = git_audit_path
        self.message_channels = {}          # Active message channels
        self.dependency_dag = {}            # Message dependency graph
        self.role_registry = {}             # Agent role assignments
        self._init_db()
        self._init_git_audit()

    def _init_db(self):
        """Initialize advanced messaging database tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Enhanced messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS advanced_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                message_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                routing_strategy TEXT NOT NULL,
                sender_agent TEXT NOT NULL,
                sender_role TEXT,
                project_path TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_content TEXT NOT NULL,
                workflow_embedded TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                git_commit_hash TEXT,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                parent_message_id TEXT,
                conversation_thread_id TEXT
            )
        """)

        # Message recipients table (supports complex routing)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                recipient_type TEXT NOT NULL,
                recipient_identifier TEXT NOT NULL,
                delivery_required BOOLEAN DEFAULT TRUE,
                acknowledgment_required BOOLEAN DEFAULT FALSE,
                timeout_seconds INTEGER DEFAULT 300,
                delivery_status TEXT DEFAULT 'pending',
                delivered_at TEXT,
                acknowledged_at TEXT,
                FOREIGN KEY (message_id) REFERENCES advanced_messages (message_id)
            )
        """)

        # Dependency DAG table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT UNIQUE NOT NULL,
                message_id TEXT NOT NULL,
                dependencies TEXT DEFAULT '[]',
                dependents TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES advanced_messages (message_id)
            )
        """)

        # Message channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_name TEXT UNIQUE NOT NULL,
                channel_type TEXT NOT NULL,
                description TEXT DEFAULT '',
                project_path TEXT NOT NULL,
                subscribers TEXT DEFAULT '[]',
                moderators TEXT DEFAULT '[]',
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        """)

        # Role assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                role_name TEXT NOT NULL,
                project_path TEXT NOT NULL,
                assigned_at TEXT NOT NULL,
                assigned_by TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                UNIQUE (agent_name, role_name, project_path)
            )
        """)

        # Audit trail table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_description TEXT NOT NULL,
                agent_name TEXT,
                timestamp TEXT NOT NULL,
                git_commit_hash TEXT,
                metadata TEXT DEFAULT '{}'
            )
        """)

        conn.commit()
        conn.close()

    def _init_git_audit(self):
        """Initialize Git repository for message audit trail."""
        audit_path = Path(self.git_audit_path)
        audit_path.mkdir(parents=True, exist_ok=True)

        if not (audit_path / '.git').exists():
            # Initialize Git repository
            repo = git.Repo.init(str(audit_path))

            # Create initial commit
            readme_path = audit_path / 'README.md'
            readme_path.write_text("""# Gas Town Message Audit Trail

This repository contains the complete audit trail of all Gas Town messaging.

- Each message is stored as a JSON file
- Git commits provide immutable audit history
- Workflow executions are tracked with full context
- Dependency relationships are preserved

## Structure
- `messages/` - Individual message files
- `workflows/` - Executed workflow records
- `dependencies/` - Dependency graph snapshots
""")

            repo.index.add(['README.md'])
            repo.index.commit("Initialize Gas Town message audit repository")

    def send_advanced_message(
        self,
        message_type: MessageType,
        sender_agent: str,
        sender_role: Optional[str],
        project_path: str,
        subject: str,
        body_content: str,
        recipients: List[MessageRecipient],
        priority: MessagePriority = MessagePriority.NORMAL,
        routing_strategy: RoutingStrategy = RoutingStrategy.QUEUED,
        workflow_embedding: Optional[WorkflowEmbedding] = None,
        conversation_thread_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
        dependency_requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send advanced message with complex routing and workflow embedding.

        This is the core Gas Town messaging capability with full feature support.
        """

        # Generate unique message ID
        message_id = f"msg_{str(uuid.uuid4())[:8]}_{int(datetime.now().timestamp())}"

        # Prepare message data
        message_data = {
            "message_id": message_id,
            "message_type": message_type.value,
            "priority": priority.value,
            "routing_strategy": routing_strategy.value,
            "sender_agent": sender_agent,
            "sender_role": sender_role,
            "project_path": project_path,
            "subject": subject,
            "body_content": body_content,
            "recipients": [asdict(r) for r in recipients],
            "workflow_embedding": asdict(workflow_embedding) if workflow_embedding else None,
            "conversation_thread_id": conversation_thread_id,
            "parent_message_id": parent_message_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Store message in database
            message_db_id = self._store_message_in_db(message_data, workflow_embedding)

            # Create Git audit entry
            git_commit_hash = self._create_git_audit_entry(message_data)

            # Update Git commit hash in database
            self._update_message_git_hash(message_id, git_commit_hash)

            # Handle dependency DAG if requirements specified
            if dependency_requirements:
                dependency_node = self._add_to_dependency_dag(
                    message_id, dependency_requirements
                )

            # Route and deliver message based on strategy
            delivery_result = self._route_and_deliver_message(
                message_data, routing_strategy
            )

            # Execute embedded workflow if applicable
            workflow_result = None
            if workflow_embedding and workflow_embedding.auto_execute:
                workflow_result = self._execute_embedded_workflow(
                    message_id, workflow_embedding
                )

            return {
                "status": "success",
                "message_id": message_id,
                "git_commit_hash": git_commit_hash,
                "delivery_result": delivery_result,
                "workflow_result": workflow_result,
                "dependency_node": dependency_node.node_id if dependency_requirements else None
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Message sending failed: {str(e)}",
                "message_id": message_id
            }

    def create_message_channel(
        self,
        channel_name: str,
        channel_type: str,
        description: str,
        project_path: str,
        created_by: str,
        initial_subscribers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new message channel for topic-based communication."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            subscribers = json.dumps(initial_subscribers or [])

            cursor.execute("""
                INSERT INTO message_channels (
                    channel_name, channel_type, description, project_path,
                    subscribers, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                channel_name, channel_type, description, project_path,
                subscribers, created_by, timestamp
            ))

            conn.commit()

            # Create Git audit entry for channel creation
            channel_audit = {
                "event_type": "channel_created",
                "channel_name": channel_name,
                "channel_type": channel_type,
                "created_by": created_by,
                "subscribers": initial_subscribers or [],
                "timestamp": timestamp
            }

            git_hash = self._create_git_audit_entry(channel_audit, "channels")

            return {
                "status": "success",
                "channel_name": channel_name,
                "git_commit_hash": git_hash
            }

        except sqlite3.IntegrityError:
            return {
                "status": "error",
                "error": f"Channel {channel_name} already exists"
            }
        finally:
            conn.close()

    def assign_agent_role(
        self,
        agent_name: str,
        role_name: str,
        project_path: str,
        assigned_by: str
    ) -> Dict[str, Any]:
        """Assign role to agent for role-based messaging."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            timestamp = datetime.now(timezone.utc).isoformat()

            cursor.execute("""
                INSERT INTO agent_roles (
                    agent_name, role_name, project_path, assigned_at, assigned_by
                ) VALUES (?, ?, ?, ?, ?)
            """, (agent_name, role_name, project_path, timestamp, assigned_by))

            conn.commit()

            # Update in-memory role registry
            project_roles = self.role_registry.setdefault(project_path, {})
            agent_roles = project_roles.setdefault(agent_name, set())
            agent_roles.add(role_name)

            return {
                "status": "success",
                "agent_name": agent_name,
                "role_name": role_name
            }

        except sqlite3.IntegrityError:
            return {
                "status": "error",
                "error": f"Agent {agent_name} already has role {role_name}"
            }
        finally:
            conn.close()

    def fetch_messages_advanced(
        self,
        agent_name: str,
        project_path: str,
        message_types: Optional[List[MessageType]] = None,
        priorities: Optional[List[MessagePriority]] = None,
        channels: Optional[List[str]] = None,
        unread_only: bool = True,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Fetch messages with advanced filtering and routing awareness."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Build dynamic query based on filters
            query_conditions = ["mr.recipient_identifier = ? OR mr.recipient_type = 'broadcast'"]
            query_params = [agent_name]

            if message_types:
                type_conditions = ",".join(["?" for _ in message_types])
                query_conditions.append(f"am.message_type IN ({type_conditions})")
                query_params.extend([mt.value for mt in message_types])

            if priorities:
                priority_conditions = ",".join(["?" for _ in priorities])
                query_conditions.append(f"am.priority IN ({priority_conditions})")
                query_params.extend([p.value for p in priorities])

            if channels:
                channel_conditions = ",".join(["?" for _ in channels])
                query_conditions.append(f"mr.recipient_identifier IN ({channel_conditions})")
                query_params.extend(channels)

            if unread_only:
                query_conditions.append("mr.acknowledged_at IS NULL")

            query_conditions.append("am.project_path = ?")
            query_params.append(project_path)

            query = f"""
                SELECT DISTINCT am.message_id, am.message_type, am.priority,
                       am.sender_agent, am.sender_role, am.subject, am.body_content,
                       am.workflow_embedded, am.created_at, am.git_commit_hash,
                       mr.delivery_status, mr.acknowledgment_required
                FROM advanced_messages am
                JOIN message_recipients mr ON am.message_id = mr.message_id
                WHERE {' AND '.join(query_conditions)}
                ORDER BY am.priority ASC, am.created_at DESC
                LIMIT ?
            """
            query_params.append(limit)

            cursor.execute(query, query_params)
            messages = cursor.fetchall()

            # Process messages with workflow extraction
            processed_messages = []
            for message_row in messages:
                message_data = {
                    "message_id": message_row[0],
                    "message_type": message_row[1],
                    "priority": message_row[2],
                    "sender_agent": message_row[3],
                    "sender_role": message_row[4],
                    "subject": message_row[5],
                    "body_content": message_row[6],
                    "workflow_embedded": json.loads(message_row[7]) if message_row[7] else None,
                    "created_at": message_row[8],
                    "git_commit_hash": message_row[9],
                    "delivery_status": message_row[10],
                    "acknowledgment_required": message_row[11]
                }

                processed_messages.append(message_data)

            return {
                "status": "success",
                "message_count": len(processed_messages),
                "messages": processed_messages,
                "agent_name": agent_name,
                "filters_applied": {
                    "message_types": [mt.value for mt in message_types] if message_types else None,
                    "priorities": [p.value for p in priorities] if priorities else None,
                    "channels": channels,
                    "unread_only": unread_only
                }
            }

        finally:
            conn.close()

    def acknowledge_message(
        self,
        message_id: str,
        agent_name: str,
        acknowledgment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Acknowledge message receipt and process any embedded workflows."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            timestamp = datetime.now(timezone.utc).isoformat()

            # Update acknowledgment status
            cursor.execute("""
                UPDATE message_recipients
                SET acknowledged_at = ?
                WHERE message_id = ? AND recipient_identifier = ?
            """, (timestamp, message_id, agent_name))

            if cursor.rowcount == 0:
                return {
                    "status": "error",
                    "error": f"Message {message_id} not found for agent {agent_name}"
                }

            # Check if message has embedded workflow requiring execution
            cursor.execute("""
                SELECT workflow_embedded FROM advanced_messages WHERE message_id = ?
            """, (message_id,))

            workflow_data = cursor.fetchone()
            workflow_result = None

            if workflow_data and workflow_data[0]:
                workflow_embedding = json.loads(workflow_data[0])
                if not workflow_embedding.get("auto_execute", True):  # Manual execution
                    workflow_result = self._execute_embedded_workflow(
                        message_id, WorkflowEmbedding(**workflow_embedding)
                    )

            conn.commit()

            # Create audit trail entry
            audit_entry = {
                "message_id": message_id,
                "event_type": "message_acknowledged",
                "agent_name": agent_name,
                "acknowledgment_data": acknowledgment_data,
                "timestamp": timestamp
            }

            git_hash = self._create_git_audit_entry(audit_entry, "acknowledgments")

            return {
                "status": "success",
                "message_id": message_id,
                "acknowledged_at": timestamp,
                "workflow_executed": workflow_result is not None,
                "workflow_result": workflow_result,
                "git_commit_hash": git_hash
            }

        finally:
            conn.close()

    def get_dependency_dag_status(self, project_path: str) -> Dict[str, Any]:
        """Get current status of the message dependency DAG."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT md.node_id, md.message_id, md.dependencies, md.dependents,
                       md.status, am.subject, am.sender_agent, md.created_at
                FROM message_dependencies md
                JOIN advanced_messages am ON md.message_id = am.message_id
                WHERE am.project_path = ?
                ORDER BY md.created_at DESC
            """, (project_path,))

            dag_nodes = cursor.fetchall()

            # Process DAG structure
            dag_status = {
                "total_nodes": len(dag_nodes),
                "status_counts": {},
                "nodes": [],
                "ready_for_execution": [],
                "blocked_nodes": []
            }

            for node_row in dag_nodes:
                node_data = {
                    "node_id": node_row[0],
                    "message_id": node_row[1],
                    "dependencies": json.loads(node_row[2]),
                    "dependents": json.loads(node_row[3]),
                    "status": node_row[4],
                    "subject": node_row[5],
                    "sender_agent": node_row[6],
                    "created_at": node_row[7]
                }

                dag_status["nodes"].append(node_data)

                # Count statuses
                status = node_data["status"]
                dag_status["status_counts"][status] = dag_status["status_counts"].get(status, 0) + 1

                # Identify ready and blocked nodes
                if status == "ready":
                    dag_status["ready_for_execution"].append(node_data)
                elif status == "pending" and node_data["dependencies"]:
                    dag_status["blocked_nodes"].append(node_data)

            return {
                "status": "success",
                "dag_status": dag_status,
                "project_path": project_path
            }

        finally:
            conn.close()

    def _store_message_in_db(
        self,
        message_data: Dict[str, Any],
        workflow_embedding: Optional[WorkflowEmbedding]
    ) -> int:
        """Store message and recipients in database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Store main message
            cursor.execute("""
                INSERT INTO advanced_messages (
                    message_id, message_type, priority, routing_strategy,
                    sender_agent, sender_role, project_path, subject, body_content,
                    workflow_embedded, created_at, parent_message_id, conversation_thread_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message_data["message_id"],
                message_data["message_type"],
                message_data["priority"],
                message_data["routing_strategy"],
                message_data["sender_agent"],
                message_data["sender_role"],
                message_data["project_path"],
                message_data["subject"],
                message_data["body_content"],
                json.dumps(message_data["workflow_embedding"]) if workflow_embedding else None,
                message_data["created_at"],
                message_data.get("parent_message_id"),
                message_data.get("conversation_thread_id")
            ))

            message_db_id = cursor.lastrowid

            # Store recipients
            for recipient_data in message_data["recipients"]:
                cursor.execute("""
                    INSERT INTO message_recipients (
                        message_id, recipient_type, recipient_identifier,
                        delivery_required, acknowledgment_required, timeout_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    message_data["message_id"],
                    recipient_data["type"],
                    recipient_data["identifier"],
                    recipient_data["required"],
                    recipient_data["acknowledgment_required"],
                    recipient_data["timeout_seconds"]
                ))

            conn.commit()
            return message_db_id

        finally:
            conn.close()

    def _create_git_audit_entry(
        self,
        data: Dict[str, Any],
        subfolder: str = "messages"
    ) -> str:
        """Create Git audit entry for immutable message trail."""

        try:
            audit_path = Path(self.git_audit_path)
            subfolder_path = audit_path / subfolder
            subfolder_path.mkdir(exist_ok=True)

            # Create audit file
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{data.get('message_id', str(uuid.uuid4())[:8])}.json"
            audit_file = subfolder_path / filename

            # Write audit data
            with open(audit_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Git commit
            repo = git.Repo(str(audit_path))
            repo.index.add([str(audit_file.relative_to(audit_path))])

            commit_message = f"Gas Town message audit: {data.get('subject', 'System event')}"
            commit = repo.index.commit(commit_message)

            return commit.hexsha[:8]

        except Exception as e:
            # Fallback: continue without Git audit if it fails
            print(f"Warning: Git audit failed: {e}")
            return "no_git_audit"

    def _update_message_git_hash(self, message_id: str, git_commit_hash: str):
        """Update message with Git commit hash."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE advanced_messages SET git_commit_hash = ? WHERE message_id = ?
        """, (git_commit_hash, message_id))

        conn.commit()
        conn.close()

    def _add_to_dependency_dag(
        self,
        message_id: str,
        dependency_requirements: List[str]
    ) -> DependencyNode:
        """Add message to dependency DAG with specified requirements."""

        node_id = f"dag_{str(uuid.uuid4())[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create dependency node
        dependency_node = DependencyNode(
            node_id=node_id,
            message_id=message_id,
            dependencies=set(dependency_requirements),
            dependents=set(),
            status="pending"
        )

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO message_dependencies (
                node_id, message_id, dependencies, dependents, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id, message_id, json.dumps(list(dependency_node.dependencies)),
            json.dumps(list(dependency_node.dependents)), dependency_node.status,
            timestamp, timestamp
        ))

        conn.commit()
        conn.close()

        # Update in-memory DAG
        self.dependency_dag[node_id] = dependency_node

        return dependency_node

    def _route_and_deliver_message(
        self,
        message_data: Dict[str, Any],
        routing_strategy: RoutingStrategy
    ) -> Dict[str, Any]:
        """Route and deliver message based on strategy."""

        # This is a simplified implementation
        # In production, this would integrate with actual message delivery systems

        delivery_results = {
            "strategy": routing_strategy.value,
            "recipients_targeted": len(message_data["recipients"]),
            "delivery_attempts": [],
            "successful_deliveries": 0,
            "failed_deliveries": 0
        }

        for recipient in message_data["recipients"]:
            # Simulate delivery attempt
            delivery_attempt = {
                "recipient": recipient,
                "status": "delivered",  # Simulated success
                "delivered_at": datetime.now(timezone.utc).isoformat()
            }

            delivery_results["delivery_attempts"].append(delivery_attempt)
            delivery_results["successful_deliveries"] += 1

        return delivery_results

    def _execute_embedded_workflow(
        self,
        message_id: str,
        workflow_embedding: WorkflowEmbedding
    ) -> Dict[str, Any]:
        """Execute workflow embedded in message."""

        # This is a simplified implementation
        # In production, this would integrate with the actual workflow engine

        workflow_result = {
            "workflow_id": workflow_embedding.workflow_id,
            "workflow_type": workflow_embedding.workflow_type,
            "execution_status": "completed",  # Simulated success
            "execution_output": f"Workflow {workflow_embedding.workflow_id} executed successfully",
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

        # Create audit entry for workflow execution
        audit_data = {
            "message_id": message_id,
            "workflow_execution": workflow_result,
            "workflow_content": workflow_embedding.workflow_content
        }

        self._create_git_audit_entry(audit_data, "workflows")

        return workflow_result


# CLI Commands for Advanced Messaging

def send_message_command(
    message_type: str,
    sender_agent: str,
    recipients: str,
    subject: str,
    body: str,
    priority: str = "normal",
    project_path: str = "/home/ubuntu"
):
    """Send advanced message via CLI."""

    messaging = AdvancedMessagingSystem()

    # Parse recipients
    recipient_list = []
    for recipient_str in recipients.split(","):
        parts = recipient_str.strip().split(":")
        recipient_type = parts[0] if len(parts) > 1 else "agent"
        recipient_id = parts[-1]

        recipient_list.append(MessageRecipient(
            type=recipient_type,
            identifier=recipient_id
        ))

    # Send message
    result = messaging.send_advanced_message(
        message_type=MessageType(message_type),
        sender_agent=sender_agent,
        sender_role=None,
        project_path=project_path,
        subject=subject,
        body_content=body,
        recipients=recipient_list,
        priority=MessagePriority[priority.upper()]
    )

    if result["status"] == "success":
        return f"✅ Message sent successfully!\n" \
               f"   Message ID: {result['message_id']}\n" \
               f"   Git Audit: {result['git_commit_hash']}\n" \
               f"   Recipients: {len(recipient_list)}"
    else:
        return f"❌ Message failed: {result.get('error', 'Unknown error')}"


def fetch_messages_command(
    agent_name: str,
    project_path: str = "/home/ubuntu",
    message_type: str = None,
    priority: str = None,
    limit: int = 10
):
    """Fetch messages with advanced filtering."""

    messaging = AdvancedMessagingSystem()

    # Prepare filters
    message_types = [MessageType(message_type)] if message_type else None
    priorities = [MessagePriority[priority.upper()]] if priority else None

    result = messaging.fetch_messages_advanced(
        agent_name=agent_name,
        project_path=project_path,
        message_types=message_types,
        priorities=priorities,
        limit=limit
    )

    if result["status"] == "success":
        output = [f"📬 Messages for {agent_name}: {result['message_count']} found"]

        for msg in result["messages"][:5]:  # Show first 5
            priority_emoji = "🔥" if msg["priority"] <= 1 else "📝"
            workflow_indicator = " 🔄" if msg["workflow_embedded"] else ""

            output.append(
                f"   {priority_emoji} {msg['subject']} (from {msg['sender_agent']}){workflow_indicator}"
            )

        if result["message_count"] > 5:
            output.append(f"   ... and {result['message_count'] - 5} more messages")

        return "\n".join(output)
    else:
        return f"❌ Failed to fetch messages: {result.get('error', 'Unknown error')}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python advanced_messaging.py <command> [args...]")
        print("Commands: send, fetch, create-channel, assign-role, dag-status")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "send" and len(sys.argv) >= 7:
            message_type = sys.argv[2]
            sender_agent = sys.argv[3]
            recipients = sys.argv[4]
            subject = sys.argv[5]
            body = sys.argv[6]
            priority = sys.argv[7] if len(sys.argv) > 7 else "normal"
            print(send_message_command(message_type, sender_agent, recipients, subject, body, priority))

        elif command == "fetch" and len(sys.argv) >= 3:
            agent_name = sys.argv[2]
            project_path = sys.argv[3] if len(sys.argv) > 3 else "/home/ubuntu"
            message_type = sys.argv[4] if len(sys.argv) > 4 else None
            priority = sys.argv[5] if len(sys.argv) > 5 else None
            limit = int(sys.argv[6]) if len(sys.argv) > 6 else 10
            print(fetch_messages_command(agent_name, project_path, message_type, priority, limit))

        else:
            print("Invalid command or missing arguments")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)