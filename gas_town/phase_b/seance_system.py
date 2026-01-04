#!/usr/bin/env python3
"""
Seance Communication System - Gas Town Phase B Implementation
============================================================

Session inheritance for knowledge transfer between agent generations.
Enables agents to communicate with predecessor sessions and inherit context.

Core Gas Town Principle: "Talk to your predecessors, learn from the dead"
"""

import json
import sqlite3
import hashlib
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import glob
import os


class SeanceManager:
    """Manages seance communication and session inheritance."""

    def __init__(self, db_path: str = "/home/ubuntu/.beads/seance.db"):
        self.db_path = db_path
        self.session_storage_path = "/home/ubuntu/.claude/sessions"
        self._init_db()
        self._ensure_session_storage()

    def _init_db(self):
        """Initialize seance database tables."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Agent sessions table - tracks all agent session history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                agent_name TEXT NOT NULL,
                project_path TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                session_hash TEXT NOT NULL,
                session_file_path TEXT NOT NULL,
                context_summary TEXT DEFAULT '',
                work_completed TEXT DEFAULT '[]',
                status TEXT DEFAULT 'active',
                parent_session_id TEXT,
                successor_session_id TEXT
            )
        """)

        # Session knowledge table - extractable knowledge from sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                knowledge_type TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                created_at TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id)
            )
        """)

        # Seance communications table - conversations with predecessors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seance_communications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                current_session_id TEXT NOT NULL,
                predecessor_session_id TEXT NOT NULL,
                query_type TEXT NOT NULL,
                query TEXT NOT NULL,
                response TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (current_session_id) REFERENCES agent_sessions (session_id),
                FOREIGN KEY (predecessor_session_id) REFERENCES agent_sessions (session_id)
            )
        """)

        conn.commit()
        conn.close()

    def _ensure_session_storage(self):
        """Ensure session storage directory exists."""
        Path(self.session_storage_path).mkdir(parents=True, exist_ok=True)

    def register_session(
        self,
        agent_name: str,
        project_path: str,
        session_file_path: Optional[str] = None,
        parent_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register a new agent session for seance communication.

        This creates the session lineage that enables predecessor communication.
        """

        # Generate session ID
        timestamp = datetime.now(timezone.utc).isoformat()
        session_data = f"{agent_name}_{project_path}_{timestamp}"
        session_id = hashlib.md5(session_data.encode()).hexdigest()[:12]

        # Generate session hash for integrity
        session_hash = hashlib.sha256(session_data.encode()).hexdigest()[:16]

        # Default session file path
        if not session_file_path:
            session_file_path = f"{self.session_storage_path}/{session_id}.jsonl"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Register new session
            cursor.execute("""
                INSERT INTO agent_sessions (
                    session_id, agent_name, project_path, started_at,
                    session_hash, session_file_path, parent_session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, agent_name, project_path, timestamp,
                session_hash, session_file_path, parent_session_id
            ))

            # Update parent session successor if exists
            if parent_session_id:
                cursor.execute("""
                    UPDATE agent_sessions
                    SET successor_session_id = ?
                    WHERE session_id = ?
                """, (session_id, parent_session_id))

            conn.commit()

            return {
                "session_id": session_id,
                "agent_name": agent_name,
                "session_hash": session_hash,
                "session_file": session_file_path,
                "parent_session": parent_session_id,
                "status": "registered"
            }

        except sqlite3.IntegrityError as e:
            return {
                "status": "error",
                "error": f"Session registration failed: {str(e)}"
            }
        finally:
            conn.close()

    def find_predecessor_sessions(
        self,
        agent_name: str,
        project_path: str,
        max_sessions: int = 5,
        time_window_hours: int = 168  # 1 week default
    ) -> List[Dict[str, Any]]:
        """
        Find predecessor sessions for the current agent in the project.

        This enables the seance communication by identifying relevant past sessions.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate time window
        cutoff_time = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        # Find predecessor sessions
        cursor.execute("""
            SELECT session_id, agent_name, started_at, ended_at,
                   session_file_path, context_summary, work_completed
            FROM agent_sessions
            WHERE project_path = ?
                AND agent_name = ?
                AND started_at >= ?
                AND status IN ('completed', 'active')
            ORDER BY started_at DESC
            LIMIT ?
        """, (project_path, agent_name, cutoff_time, max_sessions))

        sessions = cursor.fetchall()
        conn.close()

        return [
            {
                "session_id": session[0],
                "agent_name": session[1],
                "started_at": session[2],
                "ended_at": session[3],
                "session_file": session[4],
                "context_summary": session[5],
                "work_completed": json.loads(session[6] or "[]")
            }
            for session in sessions
        ]

    def communicate_with_predecessor(
        self,
        current_session_id: str,
        predecessor_session_id: str,
        query: str,
        query_type: str = "context_request"
    ) -> Dict[str, Any]:
        """
        Communicate with a predecessor session via seance.

        This is the core Gas Town seance functionality - talking to the dead.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get predecessor session details
        cursor.execute("""
            SELECT session_file_path, context_summary, work_completed, agent_name
            FROM agent_sessions WHERE session_id = ?
        """, (predecessor_session_id,))

        predecessor_data = cursor.fetchone()
        if not predecessor_data:
            return {
                "status": "error",
                "error": "Predecessor session not found"
            }

        session_file, context_summary, work_completed, agent_name = predecessor_data

        try:
            # Load predecessor session data
            session_content = self._load_session_content(session_file)

            # Generate seance response based on query
            response = self._generate_seance_response(
                query, query_type, session_content, context_summary,
                json.loads(work_completed or "[]")
            )

            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(query, response)

            # Record seance communication
            timestamp = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                INSERT INTO seance_communications (
                    current_session_id, predecessor_session_id, query_type,
                    query, response, relevance_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                current_session_id, predecessor_session_id, query_type,
                query, response, relevance_score, timestamp
            ))

            conn.commit()

            return {
                "status": "success",
                "response": response,
                "predecessor_agent": agent_name,
                "relevance_score": relevance_score,
                "session_file": session_file
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Seance communication failed: {str(e)}"
            }
        finally:
            conn.close()

    def extract_session_knowledge(
        self,
        session_id: str,
        agent_name: str,
        session_file_path: str
    ) -> Dict[str, Any]:
        """
        Extract transferable knowledge from a session for future seances.

        This creates the knowledge base for predecessor communication.
        """

        try:
            session_content = self._load_session_content(session_file_path)
            knowledge_items = self._analyze_session_for_knowledge(session_content)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            timestamp = datetime.now(timezone.utc).isoformat()

            for knowledge_item in knowledge_items:
                cursor.execute("""
                    INSERT INTO session_knowledge (
                        session_id, agent_name, knowledge_type, topic,
                        content, confidence, created_at, tags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, agent_name, knowledge_item["type"],
                    knowledge_item["topic"], knowledge_item["content"],
                    knowledge_item["confidence"], timestamp,
                    json.dumps(knowledge_item.get("tags", []))
                ))

            conn.commit()
            conn.close()

            return {
                "status": "success",
                "knowledge_items_extracted": len(knowledge_items),
                "knowledge_items": knowledge_items
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Knowledge extraction failed: {str(e)}"
            }

    def end_session(
        self,
        session_id: str,
        context_summary: str,
        work_completed: List[str],
        session_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End a session and prepare it for seance communication.

        This finalizes the session and extracts knowledge for future inheritance.
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # Update session with completion data
            cursor.execute("""
                UPDATE agent_sessions
                SET ended_at = ?, context_summary = ?, work_completed = ?, status = 'completed'
                WHERE session_id = ?
            """, (timestamp, context_summary, json.dumps(work_completed), session_id))

            # Get session details for knowledge extraction
            cursor.execute("""
                SELECT agent_name, session_file_path
                FROM agent_sessions WHERE session_id = ?
            """, (session_id,))

            session_data = cursor.fetchone()
            if not session_data:
                raise ValueError(f"Session {session_id} not found")

            agent_name, stored_session_file = session_data
            final_session_file = session_file_path or stored_session_file

            conn.commit()

            # Extract knowledge for future seances
            knowledge_result = self.extract_session_knowledge(
                session_id, agent_name, final_session_file
            )

            return {
                "status": "completed",
                "session_id": session_id,
                "ended_at": timestamp,
                "knowledge_extraction": knowledge_result
            }

        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "error": f"Session completion failed: {str(e)}"
            }
        finally:
            conn.close()

    def _load_session_content(self, session_file_path: str) -> str:
        """Load session content from file for seance analysis."""
        try:
            if session_file_path.endswith('.jsonl'):
                # Load JSONL session file
                content_lines = []
                with open(session_file_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if 'content' in entry:
                                content_lines.append(entry['content'])
                        except json.JSONDecodeError:
                            continue
                return '\n'.join(content_lines)
            else:
                # Load plain text session file
                with open(session_file_path, 'r') as f:
                    return f.read()
        except FileNotFoundError:
            return ""
        except Exception as e:
            raise ValueError(f"Failed to load session content: {str(e)}")

    def _generate_seance_response(
        self,
        query: str,
        query_type: str,
        session_content: str,
        context_summary: str,
        work_completed: List[str]
    ) -> str:
        """Generate seance response based on predecessor session data."""

        # Different response strategies based on query type
        if query_type == "context_request":
            return f"Predecessor Context:\n{context_summary}\n\nWork Completed:\n" + \
                   "\n".join([f"- {work}" for work in work_completed])

        elif query_type == "solution_lookup":
            # Search for solution patterns in session content
            relevant_lines = []
            query_words = query.lower().split()

            for line in session_content.split('\n'):
                if any(word in line.lower() for word in query_words):
                    relevant_lines.append(line.strip())
                    if len(relevant_lines) >= 5:  # Limit response size
                        break

            if relevant_lines:
                return "Predecessor found these relevant approaches:\n\n" + \
                       "\n".join(relevant_lines)
            else:
                return "No specific solutions found in predecessor session."

        elif query_type == "error_help":
            # Look for error patterns and solutions
            error_patterns = []
            for line in session_content.split('\n'):
                if any(word in line.lower() for word in ['error', 'failed', 'exception', 'bug']):
                    error_patterns.append(line.strip())

            if error_patterns:
                return "Predecessor encountered these similar issues:\n\n" + \
                       "\n".join(error_patterns[:3])
            else:
                return "No similar errors found in predecessor session."

        else:
            # General query - return most relevant content
            return f"Predecessor session summary:\n{context_summary}"

    def _calculate_relevance_score(self, query: str, response: str) -> float:
        """Calculate relevance score for seance response quality."""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())

        if not query_words:
            return 0.0

        # Simple word overlap scoring
        overlap = len(query_words.intersection(response_words))
        score = overlap / len(query_words)

        # Boost score for meaningful responses
        if len(response) > 50 and "predecessor" in response.lower():
            score += 0.2

        return min(1.0, score)

    def _analyze_session_for_knowledge(self, session_content: str) -> List[Dict[str, Any]]:
        """Analyze session content and extract transferable knowledge items."""

        knowledge_items = []
        lines = session_content.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Extract code patterns
            if line.startswith('```') and i < len(lines) - 1:
                code_block = []
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith('```'):
                    code_block.append(lines[j])
                    j += 1

                if code_block:
                    knowledge_items.append({
                        "type": "code_pattern",
                        "topic": "implementation",
                        "content": "\n".join(code_block),
                        "confidence": 0.8,
                        "tags": ["code", "implementation"]
                    })

            # Extract error handling
            if any(word in line.lower() for word in ['error', 'exception', 'failed']):
                knowledge_items.append({
                    "type": "error_handling",
                    "topic": "debugging",
                    "content": line,
                    "confidence": 0.7,
                    "tags": ["error", "debugging"]
                })

            # Extract file paths and commands
            if line.startswith('/') or line.startswith('./') or 'cd ' in line:
                knowledge_items.append({
                    "type": "file_operation",
                    "topic": "file_system",
                    "content": line,
                    "confidence": 0.6,
                    "tags": ["files", "commands"]
                })

        return knowledge_items


# CLI Commands for Seance Communication

def register_session_command(agent_name: str, project_path: str, parent_session_id: str = None):
    """Register new session for seance communication."""
    manager = SeanceManager()
    result = manager.register_session(agent_name, project_path, parent_session_id=parent_session_id)

    if result["status"] == "registered":
        return f"✅ Session registered for seance communication!\n" \
               f"   Session ID: {result['session_id']}\n" \
               f"   Agent: {result['agent_name']}\n" \
               f"   Session File: {result['session_file']}"
    else:
        return f"❌ Registration failed: {result.get('error', 'Unknown error')}"

def communicate_with_predecessor_command(session_id: str, query: str, query_type: str = "context_request"):
    """Communicate with predecessor via seance."""
    manager = SeanceManager()

    # Find predecessors
    predecessors = manager.find_predecessor_sessions("CurrentAgent", "/home/ubuntu")

    if not predecessors:
        return "👻 No predecessor sessions found for seance communication"

    # Use most recent predecessor
    predecessor_id = predecessors[0]["session_id"]
    result = manager.communicate_with_predecessor(session_id, predecessor_id, query, query_type)

    if result["status"] == "success":
        return f"👻 Seance Response from {result['predecessor_agent']}:\n\n" \
               f"{result['response']}\n\n" \
               f"Relevance Score: {result['relevance_score']:.2f}"
    else:
        return f"❌ Seance failed: {result.get('error', 'Unknown error')}"

def list_predecessor_sessions_command(agent_name: str, project_path: str):
    """List available predecessor sessions."""
    manager = SeanceManager()
    predecessors = manager.find_predecessor_sessions(agent_name, project_path)

    if not predecessors:
        return f"👻 No predecessor sessions found for {agent_name}"

    output = [f"👻 Predecessor sessions for {agent_name}:"]
    for session in predecessors:
        ended = session['ended_at'] or "Still active"
        output.append(f"   • {session['session_id']}: {session['started_at']} - {ended}")
        if session['context_summary']:
            output.append(f"     Context: {session['context_summary'][:100]}...")

    return "\n".join(output)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python seance_system.py <command> [args...]")
        print("Commands: register, communicate, list")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "register" and len(sys.argv) >= 4:
            agent_name = sys.argv[2]
            project_path = sys.argv[3]
            parent_session = sys.argv[4] if len(sys.argv) > 4 else None
            print(register_session_command(agent_name, project_path, parent_session))

        elif command == "communicate" and len(sys.argv) >= 4:
            session_id = sys.argv[2]
            query = sys.argv[3]
            query_type = sys.argv[4] if len(sys.argv) > 4 else "context_request"
            print(communicate_with_predecessor_command(session_id, query, query_type))

        elif command == "list" and len(sys.argv) >= 4:
            agent_name = sys.argv[2]
            project_path = sys.argv[3]
            print(list_predecessor_sessions_command(agent_name, project_path))

        else:
            print("Invalid command or missing arguments")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)