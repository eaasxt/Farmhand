"""
Gas Town MEOW Stack - Molecule Marketplace Database Interface
Provides SQLite database management for template storage and analytics.
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MoleculeDB:
    """Database interface for the molecule marketplace."""

    def __init__(self, db_path: str = "~/.local/share/molecule-marketplace/marketplace.db"):
        """Initialize database connection."""
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema if it doesn't exist."""
        with self.get_connection() as conn:
            # Check if tables already exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='templates'
            """)

            if cursor.fetchone() is None:
                # Database doesn't exist, create it
                schema_path = Path(__file__).parent / "schema.sql"
                if schema_path.exists():
                    schema_sql = schema_path.read_text()
                    conn.executescript(schema_sql)
                    logger.info(f"Database initialized at {self.db_path}")
                else:
                    logger.warning(f"Schema file not found at {schema_path}")
            else:
                logger.info(f"Database already exists at {self.db_path}")

    @contextmanager
    def get_connection(self):
        """Get database connection with proper transaction handling."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # Template management methods

    def create_template(self,
                       name: str,
                       title: str,
                       category: str,
                       tech_stack: str,
                       description: str = "",
                       version: str = "1.0.0",
                       author: str = "",
                       tags: List[str] = None,
                       difficulty: str = "beginner",
                       estimated_time: int = None,
                       requirements: List[str] = None,
                       variables: Dict[str, Any] = None,
                       readme_content: str = "") -> int:
        """Create a new template."""

        tags_json = json.dumps(tags or [])
        requirements_json = json.dumps(requirements or [])
        variables_json = json.dumps(variables or {})

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO templates
                (name, title, description, category, tech_stack, version, author,
                 tags, difficulty, estimated_time, requirements, variables, readme_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, title, description, category, tech_stack, version, author,
                  tags_json, difficulty, estimated_time, requirements_json,
                  variables_json, readme_content))

            template_id = cursor.lastrowid
            logger.info(f"Created template: {name} (ID: {template_id})")
            return template_id

    def get_template(self, template_id: int = None, name: str = None) -> Optional[Dict]:
        """Get template by ID or name."""
        with self.get_connection() as conn:
            if template_id:
                cursor = conn.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
            elif name:
                cursor = conn.execute("SELECT * FROM templates WHERE name = ?", (name,))
            else:
                raise ValueError("Either template_id or name must be provided")

            row = cursor.fetchone()
            if row:
                template = dict(row)
                # Parse JSON fields
                template['tags'] = json.loads(template['tags'] or '[]')
                template['requirements'] = json.loads(template['requirements'] or '[]')
                template['variables'] = json.loads(template['variables'] or '{}')
                return template
            return None

    def list_templates(self,
                      category: str = None,
                      tech_stack: str = None,
                      limit: int = 50,
                      offset: int = 0,
                      sort_by: str = "download_count") -> List[Dict]:
        """List templates with optional filtering."""

        query = "SELECT * FROM template_summary WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if tech_stack:
            query += " AND tech_stack = ?"
            params.append(tech_stack)

        # Add sorting
        valid_sorts = ["download_count", "rating_avg", "created_at", "title"]
        if sort_by not in valid_sorts:
            sort_by = "download_count"

        if sort_by in ["download_count", "rating_avg"]:
            query += f" ORDER BY {sort_by} DESC, title ASC"
        else:
            query += f" ORDER BY {sort_by} ASC"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                # Get tags for search display
                full_template = self.get_template(template_id=template['id'])
                template['tags'] = full_template['tags'] if full_template else []
                templates.append(template)

            return templates

    def search_templates(self, query: str, limit: int = 20) -> List[Dict]:
        """Search templates using full-text search."""
        with self.get_connection() as conn:
            # Use FTS5 for full-text search
            cursor = conn.execute("""
                SELECT t.*, ts.rank
                FROM template_search ts
                JOIN templates t ON t.id = ts.rowid
                WHERE template_search MATCH ?
                AND t.is_active = 1
                ORDER BY ts.rank
                LIMIT ?
            """, (query, limit))

            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                full_template = self.get_template(template_id=template['id'])
                if full_template:
                    template['tags'] = full_template['tags']
                    template['variables'] = full_template['variables']
                    templates.append(template)

            return templates

    def add_template_file(self,
                         template_id: int,
                         file_path: str,
                         content: str,
                         file_type: str = None,
                         is_executable: bool = False) -> int:
        """Add a file to a template."""

        if not file_type:
            file_type = Path(file_path).suffix.lstrip('.')

        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO template_files
                (template_id, file_path, content, file_type, is_executable)
                VALUES (?, ?, ?, ?, ?)
            """, (template_id, file_path, content, file_type, is_executable))

            file_id = cursor.lastrowid
            logger.info(f"Added file to template {template_id}: {file_path}")
            return file_id

    def get_template_files(self, template_id: int) -> List[Dict]:
        """Get all files for a template."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM template_files
                WHERE template_id = ?
                ORDER BY file_path
            """, (template_id,))

            return [dict(row) for row in cursor.fetchall()]

    def record_installation(self,
                           template_id: int,
                           user_identifier: str = "",
                           project_path: str = "",
                           config_values: Dict[str, Any] = None,
                           status: str = "success"):
        """Record a template installation for analytics."""

        config_json = json.dumps(config_values or {})

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO template_installations
                (template_id, user_identifier, project_path, config_values, installation_status)
                VALUES (?, ?, ?, ?, ?)
            """, (template_id, user_identifier, project_path, config_json, status))

            # Update download count
            conn.execute("""
                UPDATE templates
                SET download_count = download_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (template_id,))

            logger.info(f"Recorded installation of template {template_id}")

    def record_usage(self,
                     template_id: int,
                     action_type: str,
                     user_identifier: str = "",
                     metadata: Dict[str, Any] = None):
        """Record usage analytics."""

        metadata_json = json.dumps(metadata or {})

        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO usage_analytics
                (template_id, action_type, user_identifier, metadata)
                VALUES (?, ?, ?, ?)
            """, (template_id, action_type, user_identifier, metadata_json))

    def get_popular_templates(self, limit: int = 10) -> List[Dict]:
        """Get most popular templates."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM popular_templates LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_templates(self, limit: int = 10) -> List[Dict]:
        """Get most recently created templates."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM recent_templates LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_categories(self) -> List[Tuple[str, int]]:
        """Get all categories with template counts."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM templates
                WHERE is_active = 1
                GROUP BY category
                ORDER BY count DESC, category ASC
            """)

            return [(row['category'], row['count']) for row in cursor.fetchall()]

    def get_tech_stacks(self) -> List[Tuple[str, int]]:
        """Get all tech stacks with template counts."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT tech_stack, COUNT(*) as count
                FROM templates
                WHERE is_active = 1
                GROUP BY tech_stack
                ORDER BY count DESC, tech_stack ASC
            """)

            return [(row['tech_stack'], row['count']) for row in cursor.fetchall()]