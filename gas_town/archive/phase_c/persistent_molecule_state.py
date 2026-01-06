#!/usr/bin/env python3
"""
Gas Town Phase C: Persistent Molecule State System
================================================

Implements crash recovery and state persistence for molecular workflows.
This system enables agents to resume work after crashes by persisting
molecule state to SQLite and providing rollback capabilities.

Key Features:
- Automatic checkpoint creation at molecular boundaries
- Crash detection and recovery mechanisms
- State rollback to last known good checkpoint
- Integration with existing GUPP/MEOW stack
- Atomic state transitions with ACID guarantees
"""

import json
import sqlite3
import logging
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from contextlib import contextmanager


class MoleculeState(Enum):
    """Represents the lifecycle state of a molecule."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class MoleculeSnapshot:
    """Immutable snapshot of molecule state at a specific point in time."""
    molecule_id: str
    state: MoleculeState
    checkpoint_data: Dict[str, Any]
    timestamp: str
    agent_name: str
    gas_town_context: Dict[str, Any]
    dependencies: List[str]
    rollback_point: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoleculeSnapshot':
        """Create snapshot from dictionary representation."""
        return cls(
            molecule_id=data['molecule_id'],
            state=MoleculeState(data['state']),
            checkpoint_data=data['checkpoint_data'],
            timestamp=data['timestamp'],
            agent_name=data['agent_name'],
            gas_town_context=data['gas_town_context'],
            dependencies=data['dependencies'],
            rollback_point=data.get('rollback_point', False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary for serialization."""
        result = asdict(self)
        result['state'] = self.state.value
        return result


class PersistentMoleculeState:
    """
    Main class for managing persistent molecule state with crash recovery.

    This system provides:
    1. Automatic checkpointing at molecular boundaries
    2. Crash detection through agent heartbeats
    3. State recovery and rollback capabilities
    4. Integration with Gas Town MEOW stack
    """

    def __init__(self,
                 db_path: str = "/home/ubuntu/.gas_town/molecule_state.db",
                 checkpoint_interval: float = 30.0,
                 heartbeat_timeout: float = 300.0):
        """
        Initialize the persistent molecule state system.

        Args:
            db_path: Path to SQLite database for state persistence
            checkpoint_interval: Minimum seconds between automatic checkpoints
            heartbeat_timeout: Seconds before considering an agent crashed
        """
        self.db_path = Path(db_path)
        self.checkpoint_interval = checkpoint_interval
        self.heartbeat_timeout = heartbeat_timeout

        # Thread-safe access to state
        self._lock = threading.RLock()

        # In-memory cache of active molecules
        self._active_molecules: Dict[str, MoleculeSnapshot] = {}

        # Last checkpoint times to enforce intervals
        self._last_checkpoint: Dict[str, float] = {}

        # Setup database and logging
        self._init_database()
        self._init_logging()

        logging.info(f"PersistentMoleculeState initialized: {self.db_path}")

    def _init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Table for molecule snapshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS molecule_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    molecule_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    checkpoint_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    gas_town_context TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    rollback_point INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL DEFAULT (julianday('now'))
                )
            """)

            # Table for agent heartbeats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_heartbeats (
                    agent_name TEXT PRIMARY KEY,
                    last_heartbeat REAL NOT NULL DEFAULT (julianday('now')),
                    molecule_ids TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active'
                )
            """)

            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_molecule_snapshots_molecule_id
                ON molecule_snapshots(molecule_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_molecule_snapshots_timestamp
                ON molecule_snapshots(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_molecule_snapshots_rollback
                ON molecule_snapshots(rollback_point, timestamp DESC)
            """)

            conn.commit()

    def _init_logging(self) -> None:
        """Setup logging for crash recovery events."""
        log_file = self.db_path.parent / "crash_recovery.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections with proper cleanup."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def create_molecule(self,
                       molecule_id: str,
                       agent_name: str,
                       initial_data: Dict[str, Any] = None,
                       gas_town_context: Dict[str, Any] = None,
                       dependencies: List[str] = None) -> MoleculeSnapshot:
        """
        Create a new molecule and persist its initial state.

        Args:
            molecule_id: Unique identifier for the molecule
            agent_name: Name of the agent creating the molecule
            initial_data: Initial checkpoint data
            gas_town_context: Gas Town workflow context
            dependencies: List of dependent molecule IDs

        Returns:
            Initial molecule snapshot
        """
        with self._lock:
            timestamp = datetime.now(timezone.utc).isoformat()

            snapshot = MoleculeSnapshot(
                molecule_id=molecule_id,
                state=MoleculeState.INITIALIZED,
                checkpoint_data=initial_data or {},
                timestamp=timestamp,
                agent_name=agent_name,
                gas_town_context=gas_town_context or {},
                dependencies=dependencies or [],
                rollback_point=True  # Initial state is always a rollback point
            )

            self._persist_snapshot(snapshot)
            self._active_molecules[molecule_id] = snapshot

            self.logger.info(f"Created molecule {molecule_id} by agent {agent_name}")
            return snapshot

    def checkpoint_molecule(self,
                          molecule_id: str,
                          checkpoint_data: Dict[str, Any],
                          state: MoleculeState = MoleculeState.RUNNING,
                          force: bool = False,
                          rollback_point: bool = False) -> bool:
        """
        Create a checkpoint for a molecule's current state.

        Args:
            molecule_id: ID of molecule to checkpoint
            checkpoint_data: Current state data to persist
            state: Current lifecycle state of molecule
            force: Skip checkpoint interval enforcement
            rollback_point: Mark this checkpoint as a rollback point

        Returns:
            True if checkpoint was created, False if skipped due to interval
        """
        with self._lock:
            if molecule_id not in self._active_molecules:
                raise ValueError(f"Molecule {molecule_id} not found in active set")

            current_time = time.time()
            last_checkpoint = self._last_checkpoint.get(molecule_id, 0)

            # Enforce checkpoint intervals unless forced
            if not force and (current_time - last_checkpoint) < self.checkpoint_interval:
                return False

            current_snapshot = self._active_molecules[molecule_id]
            timestamp = datetime.now(timezone.utc).isoformat()

            new_snapshot = MoleculeSnapshot(
                molecule_id=molecule_id,
                state=state,
                checkpoint_data=checkpoint_data,
                timestamp=timestamp,
                agent_name=current_snapshot.agent_name,
                gas_town_context=current_snapshot.gas_town_context,
                dependencies=current_snapshot.dependencies,
                rollback_point=rollback_point
            )

            self._persist_snapshot(new_snapshot)
            self._active_molecules[molecule_id] = new_snapshot
            self._last_checkpoint[molecule_id] = current_time

            self.logger.info(f"Checkpointed molecule {molecule_id} in state {state.value}")
            return True

    def complete_molecule(self,
                         molecule_id: str,
                         final_data: Dict[str, Any] = None) -> MoleculeSnapshot:
        """
        Mark a molecule as completed and create final checkpoint.

        Args:
            molecule_id: ID of molecule to complete
            final_data: Final state data

        Returns:
            Final molecule snapshot
        """
        with self._lock:
            if molecule_id not in self._active_molecules:
                raise ValueError(f"Molecule {molecule_id} not found in active set")

            current_snapshot = self._active_molecules[molecule_id]
            timestamp = datetime.now(timezone.utc).isoformat()

            final_snapshot = MoleculeSnapshot(
                molecule_id=molecule_id,
                state=MoleculeState.COMPLETED,
                checkpoint_data=final_data or current_snapshot.checkpoint_data,
                timestamp=timestamp,
                agent_name=current_snapshot.agent_name,
                gas_town_context=current_snapshot.gas_town_context,
                dependencies=current_snapshot.dependencies,
                rollback_point=True  # Completion is always a rollback point
            )

            self._persist_snapshot(final_snapshot)

            # Remove from active set
            del self._active_molecules[molecule_id]
            self._last_checkpoint.pop(molecule_id, None)

            self.logger.info(f"Completed molecule {molecule_id}")
            return final_snapshot

    def fail_molecule(self,
                     molecule_id: str,
                     error_info: Dict[str, Any]) -> MoleculeSnapshot:
        """
        Mark a molecule as failed and create failure checkpoint.

        Args:
            molecule_id: ID of molecule that failed
            error_info: Error context and details

        Returns:
            Failure snapshot
        """
        with self._lock:
            if molecule_id not in self._active_molecules:
                raise ValueError(f"Molecule {molecule_id} not found in active set")

            current_snapshot = self._active_molecules[molecule_id]
            timestamp = datetime.now(timezone.utc).isoformat()

            # Merge error info into checkpoint data
            failure_data = current_snapshot.checkpoint_data.copy()
            failure_data.update({
                'error_info': error_info,
                'failed_at': timestamp
            })

            failure_snapshot = MoleculeSnapshot(
                molecule_id=molecule_id,
                state=MoleculeState.FAILED,
                checkpoint_data=failure_data,
                timestamp=timestamp,
                agent_name=current_snapshot.agent_name,
                gas_town_context=current_snapshot.gas_town_context,
                dependencies=current_snapshot.dependencies,
                rollback_point=False  # Failed states are not rollback points
            )

            self._persist_snapshot(failure_snapshot)

            # Keep in active set for potential recovery
            self._active_molecules[molecule_id] = failure_snapshot

            self.logger.error(f"Failed molecule {molecule_id}: {error_info}")
            return failure_snapshot

    def get_molecule_history(self,
                           molecule_id: str,
                           limit: int = 50) -> List[MoleculeSnapshot]:
        """
        Retrieve the complete history of a molecule's state changes.

        Args:
            molecule_id: ID of molecule to query
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshots in reverse chronological order
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM molecule_snapshots
                WHERE molecule_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (molecule_id, limit))

            snapshots = []
            for row in cursor.fetchall():
                snapshot_data = {
                    'molecule_id': row['molecule_id'],
                    'state': row['state'],
                    'checkpoint_data': json.loads(row['checkpoint_data']),
                    'timestamp': row['timestamp'],
                    'agent_name': row['agent_name'],
                    'gas_town_context': json.loads(row['gas_town_context']),
                    'dependencies': json.loads(row['dependencies']),
                    'rollback_point': bool(row['rollback_point'])
                }
                snapshots.append(MoleculeSnapshot.from_dict(snapshot_data))

            return snapshots

    def find_rollback_point(self, molecule_id: str) -> Optional[MoleculeSnapshot]:
        """
        Find the most recent rollback point for a molecule.

        Args:
            molecule_id: ID of molecule to find rollback point for

        Returns:
            Most recent rollback point snapshot, or None if not found
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM molecule_snapshots
                WHERE molecule_id = ? AND rollback_point = 1
                ORDER BY timestamp DESC
                LIMIT 1
            """, (molecule_id,))

            row = cursor.fetchone()
            if not row:
                return None

            snapshot_data = {
                'molecule_id': row['molecule_id'],
                'state': row['state'],
                'checkpoint_data': json.loads(row['checkpoint_data']),
                'timestamp': row['timestamp'],
                'agent_name': row['agent_name'],
                'gas_town_context': json.loads(row['gas_town_context']),
                'dependencies': json.loads(row['dependencies']),
                'rollback_point': bool(row['rollback_point'])
            }
            return MoleculeSnapshot.from_dict(snapshot_data)

    def rollback_molecule(self, molecule_id: str) -> Optional[MoleculeSnapshot]:
        """
        Roll back a molecule to its most recent rollback point.

        Args:
            molecule_id: ID of molecule to roll back

        Returns:
            Rollback snapshot if successful, None if no rollback point found
        """
        with self._lock:
            rollback_point = self.find_rollback_point(molecule_id)
            if not rollback_point:
                self.logger.error(f"No rollback point found for molecule {molecule_id}")
                return None

            timestamp = datetime.now(timezone.utc).isoformat()

            rollback_snapshot = MoleculeSnapshot(
                molecule_id=molecule_id,
                state=MoleculeState.ROLLED_BACK,
                checkpoint_data=rollback_point.checkpoint_data,
                timestamp=timestamp,
                agent_name=rollback_point.agent_name,
                gas_town_context=rollback_point.gas_town_context,
                dependencies=rollback_point.dependencies,
                rollback_point=True  # Rollback creates new rollback point
            )

            self._persist_snapshot(rollback_snapshot)
            self._active_molecules[molecule_id] = rollback_snapshot

            self.logger.info(f"Rolled back molecule {molecule_id} to {rollback_point.timestamp}")
            return rollback_snapshot

    def detect_crashed_agents(self) -> List[Tuple[str, List[str]]]:
        """
        Detect agents that may have crashed based on heartbeat timeouts.

        Returns:
            List of (agent_name, molecule_ids) tuples for crashed agents
        """
        current_time = time.time()
        crashed = []

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT agent_name, molecule_ids, last_heartbeat
                FROM agent_heartbeats
                WHERE status = 'active'
            """)

            for row in cursor.fetchall():
                agent_name = row['agent_name']
                molecule_ids = json.loads(row['molecule_ids'])
                last_heartbeat = row['last_heartbeat']

                # Convert Julian day to Unix timestamp for comparison
                last_heartbeat_time = (last_heartbeat - 2440587.5) * 86400

                if (current_time - last_heartbeat_time) > self.heartbeat_timeout:
                    crashed.append((agent_name, molecule_ids))

                    # Mark agent as crashed
                    cursor.execute("""
                        UPDATE agent_heartbeats
                        SET status = 'crashed'
                        WHERE agent_name = ?
                    """, (agent_name,))

            conn.commit()

        return crashed

    def recover_crashed_molecules(self, agent_name: str) -> List[MoleculeSnapshot]:
        """
        Attempt to recover molecules from a crashed agent.

        Args:
            agent_name: Name of the crashed agent

        Returns:
            List of recovered molecule snapshots
        """
        recovered = []

        # Find all active molecules for this agent
        active_molecules = []
        for molecule_id, snapshot in self._active_molecules.items():
            if snapshot.agent_name == agent_name:
                active_molecules.append(molecule_id)

        for molecule_id in active_molecules:
            self.logger.info(f"Attempting recovery of molecule {molecule_id}")

            # Try to rollback to last known good state
            recovery_snapshot = self.rollback_molecule(molecule_id)
            if recovery_snapshot:
                recovered.append(recovery_snapshot)
                self.logger.info(f"Recovered molecule {molecule_id}")
            else:
                # Mark as failed if no recovery possible
                error_info = {
                    'type': 'agent_crash',
                    'crashed_agent': agent_name,
                    'detection_time': datetime.now(timezone.utc).isoformat()
                }
                self.fail_molecule(molecule_id, error_info)
                self.logger.error(f"Could not recover molecule {molecule_id}")

        return recovered

    def heartbeat(self, agent_name: str, molecule_ids: List[str]) -> None:
        """
        Record a heartbeat from an active agent.

        Args:
            agent_name: Name of the agent sending heartbeat
            molecule_ids: List of molecule IDs the agent is working on
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO agent_heartbeats
                (agent_name, last_heartbeat, molecule_ids, status)
                VALUES (?, julianday('now'), ?, 'active')
            """, (agent_name, json.dumps(molecule_ids)))

            conn.commit()

    def _persist_snapshot(self, snapshot: MoleculeSnapshot) -> None:
        """Persist a molecule snapshot to the database."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO molecule_snapshots
                (molecule_id, state, checkpoint_data, timestamp, agent_name,
                 gas_town_context, dependencies, rollback_point)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.molecule_id,
                snapshot.state.value,
                json.dumps(snapshot.checkpoint_data),
                snapshot.timestamp,
                snapshot.agent_name,
                json.dumps(snapshot.gas_town_context),
                json.dumps(snapshot.dependencies),
                int(snapshot.rollback_point)
            ))

            conn.commit()

    def get_active_molecules(self) -> Dict[str, MoleculeSnapshot]:
        """Get all currently active molecules."""
        with self._lock:
            return self._active_molecules.copy()

    def cleanup_old_snapshots(self, days: int = 30) -> int:
        """
        Clean up old snapshots beyond retention period.

        Args:
            days: Number of days to retain snapshots

        Returns:
            Number of snapshots deleted
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM molecule_snapshots
                WHERE created_at < julianday('now', '-{} days')
                AND rollback_point = 0
            """.format(days))

            deleted_count = cursor.rowcount
            conn.commit()

            self.logger.info(f"Cleaned up {deleted_count} old snapshots")
            return deleted_count


# Example usage and testing
if __name__ == "__main__":
    # Initialize the persistent state system
    state_system = PersistentMoleculeState()

    # Example: Create a molecule for a Gas Town workflow
    molecule = state_system.create_molecule(
        molecule_id="workflow-auth-123",
        agent_name="BlackCastle",
        initial_data={"step": "authentication", "user_id": "user123"},
        gas_town_context={"convoy_id": "conv-456", "mayor_directive": "secure-auth"},
        dependencies=["workflow-session-122"]
    )

    print(f"Created molecule: {molecule.molecule_id}")

    # Simulate work progress with checkpoints
    state_system.checkpoint_molecule(
        molecule_id="workflow-auth-123",
        checkpoint_data={"step": "validation", "user_id": "user123", "validated": True},
        state=MoleculeState.RUNNING,
        rollback_point=True
    )

    # Complete the workflow
    final_snapshot = state_system.complete_molecule(
        molecule_id="workflow-auth-123",
        final_data={"step": "completed", "user_id": "user123", "auth_token": "token789"}
    )

    print(f"Completed molecule: {final_snapshot.timestamp}")

    # Get history
    history = state_system.get_molecule_history("workflow-auth-123")
    print(f"Molecule history: {len(history)} snapshots")