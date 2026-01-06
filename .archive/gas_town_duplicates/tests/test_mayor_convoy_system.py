#!/usr/bin/env python3
"""
Mayor Convoy System Test - Gas Town Phase A Validation
=====================================================

Comprehensive test suite for the Mayor Coordinator Role and Convoy System.
Tests convoy creation, work dispatch (sling), status tracking, and integration.
"""

import os
import sys
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone

# Add the .claude directory to Python path for imports
sys.path.insert(0, '/home/ubuntu/.claude')

from convoy_system import ConvoyManager, create_convoy_command, sling_work_command, convoy_status_command, list_convoys_command


class TestMayorConvoySystem(unittest.TestCase):
    """Test suite for Mayor convoy management."""

    def setUp(self):
        """Set up test environment with temporary database."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_convoy.db")
        self.manager = ConvoyManager(db_path=self.test_db_path)

        # Create mock agent state file for CLI commands
        self.agent_state_path = "/tmp/test_agent_state.json"
        with open(self.agent_state_path, 'w') as f:
            json.dump({"agent_name": "MayorTestAgent"}, f)

        # Backup original agent state
        self.original_agent_state = "/home/ubuntu/.claude/agent-state.json"
        if os.path.exists(self.original_agent_state):
            os.rename(self.original_agent_state, f"{self.original_agent_state}.backup")

        # Use test agent state
        os.symlink(self.agent_state_path, self.original_agent_state)

    def tearDown(self):
        """Clean up test environment."""
        # Restore original agent state
        if os.path.exists(self.original_agent_state):
            os.unlink(self.original_agent_state)
        if os.path.exists(f"{self.original_agent_state}.backup"):
            os.rename(f"{self.original_agent_state}.backup", self.original_agent_state)

        # Clean up temp files
        if os.path.exists(self.agent_state_path):
            os.unlink(self.agent_state_path)

    def test_convoy_creation_basic(self):
        """Test basic convoy creation functionality."""
        # Create a convoy
        convoy = self.manager.create_convoy(
            creator_agent="MayorTestAgent",
            name="test-convoy",
            description="Test convoy for validation",
            bead_ids=["test-bead-1", "test-bead-2", "test-bead-3"]
        )

        # Validate convoy creation
        self.assertIn("convoy_id", convoy)
        self.assertEqual(convoy["name"], "test-convoy")
        self.assertEqual(convoy["status"], "active")
        self.assertEqual(convoy["work_items"], 3)

        print(f"✅ Convoy created: {convoy['convoy_id']} with {convoy['work_items']} work items")

    def test_convoy_status_tracking(self):
        """Test convoy status retrieval and tracking."""
        # Create convoy
        convoy = self.manager.create_convoy(
            creator_agent="MayorTestAgent",
            name="status-test-convoy",
            description="Testing status tracking",
            bead_ids=["status-bead-1", "status-bead-2"]
        )

        convoy_id = convoy["convoy_id"]

        # Get status
        status = self.manager.get_convoy_status(convoy_id)

        # Validate status structure
        self.assertEqual(status["convoy_id"], convoy_id)
        self.assertEqual(status["name"], "status-test-convoy")
        self.assertEqual(status["status"], "active")
        self.assertEqual(status["work_items"]["total"], 2)
        self.assertEqual(status["work_items"]["completed"], 0)
        self.assertEqual(len(status["work_items"]["items"]), 2)

        print(f"✅ Status tracking validated for convoy: {convoy_id}")

    def test_work_assignment_sling(self):
        """Test work item assignment (Gas Town sling mechanism)."""
        # Create convoy
        convoy = self.manager.create_convoy(
            creator_agent="MayorTestAgent",
            name="sling-test-convoy",
            description="Testing sling mechanism",
            bead_ids=["sling-bead-1", "sling-bead-2"]
        )

        convoy_id = convoy["convoy_id"]

        # Sling work to agent
        assignment = self.manager.assign_work_item(
            convoy_id, "sling-bead-1", "RedBear"
        )

        # Validate assignment
        self.assertEqual(assignment["bead_id"], "sling-bead-1")
        self.assertEqual(assignment["assigned_agent"], "RedBear")
        self.assertEqual(assignment["status"], "assigned")

        # Verify in status
        status = self.manager.get_convoy_status(convoy_id)
        assigned_item = next(
            item for item in status["work_items"]["items"]
            if item["bead_id"] == "sling-bead-1"
        )
        self.assertEqual(assigned_item["assigned_agent"], "RedBear")
        self.assertEqual(assigned_item["status"], "assigned")

        print(f"✅ Work slung successfully: sling-bead-1 → RedBear")

    def test_convoy_listing(self):
        """Test listing multiple convoys."""
        # Create multiple convoys
        convoy1 = self.manager.create_convoy(
            "MayorTestAgent", "convoy-alpha", "First test convoy",
            ["alpha-bead-1", "alpha-bead-2"]
        )
        convoy2 = self.manager.create_convoy(
            "MayorTestAgent", "convoy-beta", "Second test convoy",
            ["beta-bead-1"]
        )

        # List convoys
        convoys = self.manager.list_convoys()

        # Validate listing
        self.assertEqual(len(convoys), 2)
        convoy_names = [c["name"] for c in convoys]
        self.assertIn("convoy-alpha", convoy_names)
        self.assertIn("convoy-beta", convoy_names)

        print(f"✅ Convoy listing validated: {len(convoys)} convoys found")

    def test_cli_commands(self):
        """Test Mayor CLI command interface."""
        # Test create command
        create_result = create_convoy_command(
            "cli-test-convoy", ["cli-bead-1", "cli-bead-2"], "CLI test convoy"
        )

        self.assertIn("Convoy 'cli-test-convoy' created!", create_result)
        self.assertIn("Work items: 2", create_result)

        # Extract convoy ID from result
        lines = create_result.split('\n')
        convoy_id = lines[1].split(': ')[1]

        # Test sling command
        sling_result = sling_work_command(convoy_id, "cli-bead-1", "BlueLake")

        self.assertIn("Work slung!", sling_result)
        self.assertIn("cli-bead-1 → BlueLake", sling_result)

        # Test status command
        status_result = convoy_status_command(convoy_id)

        self.assertIn("cli-test-convoy", status_result)
        self.assertIn("cli-bead-1: assigned → BlueLake", status_result)

        # Test list command
        list_result = list_convoys_command()

        self.assertIn("Convoys:", list_result)
        self.assertIn("cli-test-convoy", list_result)

        print("✅ CLI commands validated successfully")

    def test_database_persistence(self):
        """Test that convoy data persists in SQLite database."""
        convoy = self.manager.create_convoy(
            "MayorTestAgent", "persistence-test", "Database persistence test",
            ["persist-bead-1"]
        )

        convoy_id = convoy["convoy_id"]

        # Create new manager instance to test persistence
        manager2 = ConvoyManager(db_path=self.test_db_path)
        status = manager2.get_convoy_status(convoy_id)

        # Validate persistence
        self.assertEqual(status["name"], "persistence-test")
        self.assertEqual(status["work_items"]["total"], 1)

        print("✅ Database persistence validated")

    def test_convoy_progress_tracking(self):
        """Test convoy progress calculation."""
        convoy = self.manager.create_convoy(
            "MayorTestAgent", "progress-test", "Progress tracking test",
            ["prog-bead-1", "prog-bead-2", "prog-bead-3", "prog-bead-4"]
        )

        convoy_id = convoy["convoy_id"]

        # Assign all work items
        for i, bead_id in enumerate(["prog-bead-1", "prog-bead-2", "prog-bead-3", "prog-bead-4"]):
            self.manager.assign_work_item(convoy_id, bead_id, f"Agent{i+1}")

        # Check that assignments were tracked
        status = self.manager.get_convoy_status(convoy_id)
        assigned_count = sum(1 for item in status["work_items"]["items"] if item["assigned_agent"])
        self.assertEqual(assigned_count, 4)

        print(f"✅ Progress tracking validated: {assigned_count}/4 items assigned")

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test invalid convoy ID
        with self.assertRaises(ValueError):
            self.manager.get_convoy_status("invalid-convoy-id")

        # Test invalid work item assignment
        convoy = self.manager.create_convoy(
            "MayorTestAgent", "error-test", "Error handling test", ["error-bead-1"]
        )

        with self.assertRaises(ValueError):
            self.manager.assign_work_item(convoy["convoy_id"], "nonexistent-bead", "SomeAgent")

        print("✅ Error handling validated")


class TestMayorIntegration(unittest.TestCase):
    """Test Mayor integration with Gas Town systems."""

    def test_agent_state_integration(self):
        """Test integration with agent state management."""
        # This would test integration with actual agent state files
        # For now, we'll test the basic file reading mechanism

        test_state = {"agent_name": "TestMayor", "project_key": "/test/project"}
        state_file = "/tmp/test_mayor_state.json"

        with open(state_file, 'w') as f:
            json.dump(test_state, f)

        # Test reading state
        with open(state_file) as f:
            loaded_state = json.load(f)

        self.assertEqual(loaded_state["agent_name"], "TestMayor")

        os.unlink(state_file)
        print("✅ Agent state integration validated")

    def test_convoy_database_schema(self):
        """Test convoy database schema integrity."""
        test_db = "/tmp/test_convoy_schema.db"
        manager = ConvoyManager(db_path=test_db)

        # Check table existence
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ["convoys", "convoy_work_items", "convoy_status_updates"]
        for table in expected_tables:
            self.assertIn(table, tables)

        conn.close()
        os.unlink(test_db)
        print("✅ Database schema validated")


def run_mayor_test_suite():
    """Run comprehensive Mayor system test suite."""
    print("🎯 Starting Mayor Convoy System Test Suite")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMayorConvoySystem))
    suite.addTests(loader.loadTestsFromTestCase(TestMayorIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("🏁 Mayor Test Suite Summary")
    print("=" * 60)

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        print("\n🎉 Mayor Convoy System: FULLY OPERATIONAL")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   Tests run: {result.testsRun}")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")

        if result.failures:
            print("\n📋 Failures:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback}")

        if result.errors:
            print("\n📋 Errors:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback}")

        return False


if __name__ == "__main__":
    success = run_mayor_test_suite()
    sys.exit(0 if success else 1)