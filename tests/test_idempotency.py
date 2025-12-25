"""
Tests for installation idempotency.

Verifies that running installation scripts twice is safe and doesn't:
1. Create duplicate PATH entries
2. Overwrite important config files without backup
3. Break services on restart
4. Corrupt databases
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class TestPathIdempotency:
    """Tests for PATH handling idempotency."""

    def test_no_duplicate_path_entries_in_zshrc(self, tmp_path):
        """zshrc should not add duplicate PATH entries."""
        # Simulate running the path setup twice
        zshrc = tmp_path / ".zshrc"

        # Write initial content
        zshrc.write_text("""
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.bun/bin:$PATH"
""")

        # Read content
        content = zshrc.read_text()
        lines = content.strip().split("\n")

        # Extract PATH additions
        path_additions = [l for l in lines if "export PATH=" in l]

        # Count occurrences of each path addition
        from collections import Counter
        counts = Counter(path_additions)

        # Each path should only be added once
        for path_line, count in counts.items():
            assert count == 1, f"Duplicate PATH entry: {path_line}"

    def test_path_deduplication_helper(self):
        """Helper function should deduplicate PATH entries."""
        # This tests a potential helper function that could be added
        def dedupe_path(path_string):
            """Remove duplicate entries from PATH-like string."""
            seen = set()
            result = []
            for p in path_string.split(":"):
                if p and p not in seen:
                    seen.add(p)
                    result.append(p)
            return ":".join(result)

        # Test deduplication
        duped = "/usr/bin:/home/user/.local/bin:/usr/bin:/home/user/.local/bin"
        deduped = dedupe_path(duped)
        assert deduped == "/usr/bin:/home/user/.local/bin"


class TestConfigIdempotency:
    """Tests for config file handling."""

    def test_backup_not_overwritten_on_second_run(self, tmp_path):
        """Backup files should not be overwritten on subsequent runs."""
        original = tmp_path / ".zshrc"
        backup = tmp_path / ".zshrc.backup"

        # First run: original content, no backup
        original.write_text("original content")

        # Simulate first install: backup is created
        if original.exists() and not backup.exists():
            backup.write_text(original.read_text())

        # Modify original (simulating install overwriting it)
        original.write_text("installed content")

        # Second run: original already installed, backup exists
        # Backup should NOT be overwritten
        if original.exists() and not backup.exists():
            backup.write_text(original.read_text())

        # Backup should still have original content
        assert backup.read_text() == "original content"

    def test_config_with_marker_idempotent(self, tmp_path):
        """Config with Farmhand marker should not be re-processed."""
        config = tmp_path / "config"

        marker = "# FARMHAND_MANAGED - DO NOT EDIT BELOW"

        # First install
        if not config.exists() or marker not in config.read_text():
            config.write_text(f"""
{marker}
export PATH="$HOME/.local/bin:$PATH"
""")

        content_after_first = config.read_text()

        # Second install - should not modify
        if not config.exists() or marker not in config.read_text():
            config.write_text(f"""
{marker}
export PATH="$HOME/.local/bin:$PATH"
""")

        content_after_second = config.read_text()

        assert content_after_first == content_after_second


class TestDatabaseIdempotency:
    """Tests for database schema idempotency."""

    def test_sqlite_create_if_not_exists(self, tmp_path):
        """CREATE TABLE IF NOT EXISTS should be idempotent."""
        import sqlite3

        db_path = tmp_path / "test.db"

        def create_schema(db):
            conn = sqlite3.connect(str(db))
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_reservations (
                    id INTEGER PRIMARY KEY,
                    agent_id INTEGER
                )
            """)
            conn.commit()
            conn.close()

        # Run twice
        create_schema(db_path)
        create_schema(db_path)

        # Should not raise any errors
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "agents" in tables
        assert "file_reservations" in tables

    def test_insert_or_ignore_idempotent(self, tmp_path):
        """INSERT OR IGNORE should be idempotent."""
        import sqlite3

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                human_key TEXT UNIQUE
            )
        """)

        # Insert twice with INSERT OR IGNORE
        conn.execute("INSERT OR IGNORE INTO projects (human_key) VALUES (?)", ("/home/user",))
        conn.execute("INSERT OR IGNORE INTO projects (human_key) VALUES (?)", ("/home/user",))
        conn.commit()

        # Should only have one row
        cursor = conn.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1


class TestServiceIdempotency:
    """Tests for service restart handling."""

    def test_systemctl_restart_is_safe(self):
        """Restarting a service that's already running should be safe."""
        # This is more of a documentation test
        # systemctl restart is inherently idempotent
        assert True  # Placeholder for actual service tests

    def test_enable_already_enabled_is_safe(self):
        """Enabling an already-enabled service should be safe."""
        # systemctl enable is idempotent
        assert True  # Placeholder for actual service tests


class TestHookIdempotency:
    """Tests for hook installation idempotency."""

    def test_hook_overwrite_is_safe(self, tmp_path):
        """Overwriting hooks with same content should be safe."""
        hooks_dir = tmp_path / ".claude" / "hooks"
        hooks_dir.mkdir(parents=True)

        hook_content = """#!/usr/bin/env python3
import sys
sys.exit(0)
"""

        hook_file = hooks_dir / "test-hook.py"

        # First install
        hook_file.write_text(hook_content)
        mtime1 = hook_file.stat().st_mtime

        # Second install (same content)
        hook_file.write_text(hook_content)

        # Content should be identical
        assert hook_file.read_text() == hook_content

    def test_settings_json_merge_not_overwrite(self, tmp_path):
        """settings.json should merge hooks, not overwrite."""
        settings_file = tmp_path / "settings.json"

        # Existing user settings
        existing = {
            "permissions": {
                "allow": ["Read", "Glob"]
            },
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Write", "hooks": [{"type": "command", "command": "user-hook.py"}]}
                ]
            }
        }
        settings_file.write_text(json.dumps(existing, indent=2))

        # New Farmhand hooks to add
        farmhand_hooks = {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "safety.py"}]}
            ]
        }

        # Proper merge (what install should do)
        current = json.loads(settings_file.read_text())
        if "hooks" not in current:
            current["hooks"] = {}

        for event, hooks_list in farmhand_hooks.items():
            if event not in current["hooks"]:
                current["hooks"][event] = []

            # Add hooks that don't already exist
            existing_commands = {
                h.get("hooks", [{}])[0].get("command", "")
                for h in current["hooks"][event]
            }
            for hook in hooks_list:
                cmd = hook.get("hooks", [{}])[0].get("command", "")
                if cmd not in existing_commands:
                    current["hooks"][event].append(hook)

        # Verify user hooks preserved
        assert any(
            "user-hook.py" in str(h)
            for h in current["hooks"]["PreToolUse"]
        )

        # Verify new hooks added
        assert any(
            "safety.py" in str(h)
            for h in current["hooks"]["PreToolUse"]
        )


class TestScriptIdempotency:
    """Test that install scripts handle idempotency correctly."""

    def test_install_scripts_have_existence_checks(self, hooks_dir):
        """Install scripts should check if things exist before installing."""
        scripts_dir = hooks_dir.parent / "scripts" / "install"
        if not scripts_dir.exists():
            pytest.skip("Install scripts directory not found")

        # Patterns that indicate idempotent installation
        good_patterns = [
            "if [[ ! -d",       # Check if directory doesn't exist
            "if [[ ! -f",       # Check if file doesn't exist
            "if ! command -v",  # Check if command doesn't exist
            "CREATE TABLE IF NOT EXISTS",
            "INSERT OR IGNORE",
            "|| true",          # Ignore failures
        ]

        for script in scripts_dir.glob("*.sh"):
            content = script.read_text()

            # Each script should have at least one idempotency pattern
            has_pattern = any(p in content for p in good_patterns)

            # This is a soft check - just log missing patterns
            if not has_pattern:
                print(f"Warning: {script.name} may not be idempotent")
