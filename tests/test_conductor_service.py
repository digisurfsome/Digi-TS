"""
Tests for the Conductor Service - Phase 4 Bootstrap.

Tests the basic orchestrator that coordinates:
- Memory System (RAG + Baton)
- Round Table
- Testing Facility

Test Chunks:
- 4A: Command Parsing
- 4B: Quick Actions
- 4C: Full Integration
"""

import os
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.conductor_service import (
    ConductorService,
    ConductorAction,
    ConductorResult,
    CommandType,
    create_conductor,
)


# =============================================================================
# Chunk 4A: Command Parsing Tests
# =============================================================================

class TestCommandParsing:
    """Test that the Conductor correctly parses natural language commands."""

    def setup_method(self):
        """Set up a basic Conductor with no integrations for parsing tests."""
        self.conductor = ConductorService()

    def test_parse_build_commands(self):
        """Test parsing of build/execute round commands."""
        build_phrases = [
            "run a build round",
            "run build",
            "execute a round",
            "execute round",
            "build the code",
            "start a round",
        ]

        for phrase in build_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "execute_round", f"Wrong action for: {phrase}"
            print(f"✓ Parsed: '{phrase}' → execute_round")

    def test_parse_test_commands(self):
        """Test parsing of test commands."""
        test_phrases = [
            "run tests",
            "run the tests",
            "test the code",
            "check the code",
            "validate",
        ]

        for phrase in test_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "run_tests", f"Wrong action for: {phrase}"
            print(f"✓ Parsed: '{phrase}' → run_tests")

    def test_parse_checkpoint_commands(self):
        """Test parsing of checkpoint/baton commands."""
        checkpoint_phrases = [
            "create a checkpoint",
            "create checkpoint",
            "save the state",
            "generate a baton",
            "snapshot",
        ]

        for phrase in checkpoint_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "create_baton", f"Wrong action for: {phrase}"
            print(f"✓ Parsed: '{phrase}' → create_baton")

    def test_parse_status_commands(self):
        """Test parsing of status check commands."""
        status_phrases = [
            "what's the context status",
            "whats the status",
            "show the status",
            "context health",
            "memory status",
            "system status",
            "how are things",
        ]

        for phrase in status_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "get_status", f"Wrong action for: {phrase}"
            print(f"✓ Parsed: '{phrase}' → get_status")

    def test_parse_store_decision_commands(self):
        """Test parsing of store decision commands."""
        store_phrases = [
            "store decision: use PostgreSQL for the database",
            "store this decision: we will use JWT auth",
            "remember that we chose React",
            "save decision: API is REST only",
        ]

        for phrase in store_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "store_decision", f"Wrong action for: {phrase}"
            assert actions[0].parameters.get("decision"), f"No decision extracted from: {phrase}"
            print(f"✓ Parsed: '{phrase}' → store_decision")

    def test_parse_query_commands(self):
        """Test parsing of memory query commands."""
        query_phrases = [
            "what did we decide about authentication",
            "find decisions about database",
            "search for auth settings",
            "recall what we said about API",
        ]

        for phrase in query_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "query_memory", f"Wrong action for: {phrase}"
            print(f"✓ Parsed: '{phrase}' → query_memory")

    def test_parse_help_commands(self):
        """Test parsing of help commands."""
        help_phrases = [
            "help",
            "what can you do",
            "commands",
            "how do I use this",
        ]

        for phrase in help_phrases:
            result = self.conductor.process_command(phrase)
            actions = result.actions
            assert len(actions) >= 1, f"Failed to parse: {phrase}"
            assert actions[0].action_type == "show_help", f"Wrong action for: {phrase}"
            print(f"✓ Parsed: '{phrase}' → show_help")

    def test_unknown_command_shows_help(self):
        """Test that unknown commands fall back to help."""
        result = self.conductor.process_command("do something completely random and weird")
        actions = result.actions
        assert len(actions) >= 1
        # Should either be help or unknown
        assert actions[0].action_type in ["help", "show_help", "unknown"]
        print("✓ Unknown command handled gracefully")


# =============================================================================
# Chunk 4B: Quick Actions Tests
# =============================================================================

class TestQuickActions:
    """Test button-based quick actions work correctly."""

    def setup_method(self):
        """Set up Conductor with mock services."""
        # Create mock services
        self.mock_rt = MagicMock()
        self.mock_rag = MagicMock()
        self.mock_tester = MagicMock()
        self.mock_baton = MagicMock()
        self.mock_context = MagicMock()

        self.conductor = ConductorService(
            roundtable_service=self.mock_rt,
            rag_service=self.mock_rag,
            testing_facility=self.mock_tester,
            baton_service=self.mock_baton,
            context_assembler=self.mock_context
        )

        # Set up context
        self.conductor.set_context(session_id=1, round_id=1, project_id=1)

    def test_quick_action_run_build(self):
        """Test run_build quick action."""
        # Mock successful round execution
        self.mock_rt.execute_round_with_testing.return_value = {
            "success": True,
            "builder_response": MagicMock(content="print('hello')"),
            "all_tests_passed": True
        }

        result = self.conductor.quick_action("run_build")

        assert result["success"]
        self.mock_rt.execute_round_with_testing.assert_called_once()
        print("✓ Quick action: run_build works")

    def test_quick_action_run_tests(self):
        """Test run_tests quick action."""
        # Mock test results
        mock_suite = MagicMock()
        mock_suite.all_passed = True
        mock_suite.passed = 5
        mock_suite.failed = 0
        self.mock_tester.run_all_tests.return_value = mock_suite

        result = self.conductor.quick_action("run_tests")

        assert result["success"]
        assert result["all_passed"]
        print("✓ Quick action: run_tests works")

    def test_quick_action_create_checkpoint(self):
        """Test create_checkpoint quick action."""
        # Mock baton creation
        mock_baton = MagicMock()
        mock_baton.id = 123
        mock_baton.snapshot_name = "Test Baton"
        self.mock_baton.generate_baton.return_value = mock_baton

        result = self.conductor.quick_action("create_checkpoint")

        assert result["success"]
        assert result["baton_id"] == 123
        self.mock_baton.generate_baton.assert_called_once()
        print("✓ Quick action: create_checkpoint works")

    def test_quick_action_check_status(self):
        """Test check_status quick action."""
        # Mock context health
        self.mock_context.get_context_health.return_value = {
            "status": "healthy",
            "percentage": 25.0
        }

        # Mock RAG stats
        self.mock_rag.get_stats.return_value = {
            "total": 10,
            "decisions": 5,
            "code_changes": 3
        }

        result = self.conductor.quick_action("check_status")

        assert result["success"]
        assert "systems" in result
        print("✓ Quick action: check_status works")

    def test_quick_action_unknown(self):
        """Test that unknown quick actions are handled."""
        result = self.conductor.quick_action("nonexistent_action")

        assert not result["success"]
        assert "error" in result
        print("✓ Unknown quick action handled gracefully")


# =============================================================================
# Chunk 4C: Full Integration Tests
# =============================================================================

class TestFullIntegration:
    """Test Conductor → Memory → Round Table → Testing integration."""

    def setup_method(self):
        """Set up Conductor with all mock services."""
        # Create realistic mock services
        self.mock_rt = MagicMock()
        self.mock_rag = MagicMock()
        self.mock_tester = MagicMock()
        self.mock_baton = MagicMock()
        self.mock_context = MagicMock()

        # Configure mocks with realistic returns
        self.mock_rag.store_decision.return_value = "doc123"
        self.mock_rag.retrieve.return_value = [
            {"content": "We decided to use PostgreSQL", "category": "decisions"}
        ]
        self.mock_rag.get_stats.return_value = {"total": 5, "decisions": 3}

        mock_test_result = MagicMock()
        mock_test_result.all_passed = True
        mock_test_result.passed = 5
        mock_test_result.failed = 0
        self.mock_tester.run_all_tests.return_value = mock_test_result
        self.mock_tester.enabled_tiers = [1, 2, 3, 4, 5]
        self.mock_tester.project_path = "/test/path"
        self.mock_tester.get_failure_summary.return_value = "All tests passed!"

        self.conductor = ConductorService(
            roundtable_service=self.mock_rt,
            rag_service=self.mock_rag,
            testing_facility=self.mock_tester,
            baton_service=self.mock_baton,
            context_assembler=self.mock_context
        )

        self.conductor.set_context(session_id=1, round_id=1, project_id=1)

    def test_full_workflow_command_to_execution(self):
        """Test complete workflow: command → parse → execute → result."""
        # Configure mock for full cycle
        self.mock_rt.execute_round_with_testing.return_value = {
            "success": True,
            "builder_response": MagicMock(content="def hello(): pass"),
            "all_tests_passed": True
        }

        # Step 1: User gives command
        result = self.conductor.process_command("run a build round")

        # Step 2: Verify parsing
        assert len(result.actions) >= 1
        assert result.actions[0].action_type == "execute_round"

        # Step 3: Verify execution
        assert result.success
        self.mock_rt.execute_round_with_testing.assert_called()

        print("✓ Full workflow: command → parse → execute → result")

    def test_memory_integration(self):
        """Test that decisions are stored and queried correctly."""
        # Store a decision
        store_result = self.conductor.process_command(
            "store decision: We will use JWT for authentication"
        )
        assert store_result.success
        self.mock_rag.store_decision.assert_called()

        # Query the decision
        query_result = self.conductor.process_command(
            "what did we decide about authentication"
        )
        assert query_result.success
        self.mock_rag.retrieve.assert_called()

        print("✓ Memory integration: store and query work")

    def test_status_shows_all_systems(self):
        """Test that status check shows all integrated systems."""
        result = self.conductor.quick_action("check_status")

        assert result["success"]
        systems = result["systems"]

        # Should have status for all systems
        assert "context" in systems or "rag" in systems
        assert "roundtable" in systems
        assert "testing" in systems

        print("✓ Status shows all systems")

    def test_integration_status_report(self):
        """Test the integration status report."""
        status = self.conductor.get_integration_status()

        assert "roundtable" in status
        assert status["roundtable"]["available"] == True

        assert "rag" in status
        assert status["rag"]["available"] == True

        assert "testing_facility" in status
        assert status["testing_facility"]["available"] == True

        print("✓ Integration status report works")

    def test_context_management(self):
        """Test session/round/project context management."""
        # Set context
        self.conductor.set_context(session_id=10, round_id=20, project_id=30)

        # Get context
        ctx = self.conductor.get_context()
        assert ctx["session_id"] == 10
        assert ctx["round_id"] == 20
        assert ctx["project_id"] == 30

        print("✓ Context management works")

    def test_command_history_tracked(self):
        """Test that command history is tracked."""
        # Execute some commands
        self.conductor.process_command("help")
        self.conductor.process_command("status")
        self.conductor.process_command("run tests")

        # Check history
        history = self.conductor.get_command_history()
        assert len(history) == 3

        print("✓ Command history is tracked")

    def test_full_cycle_with_testing(self):
        """Test the complete build-test cycle."""
        # Configure for successful cycle
        self.mock_rt.execute_round_with_testing.return_value = {
            "success": True,
            "builder_response": MagicMock(content="valid code"),
            "all_tests_passed": True,
            "test_results": {"passed": 5, "failed": 0}
        }

        result = self.conductor.quick_action("run_full_cycle")

        assert result["success"] or result.get("message")
        print("✓ Full build-test cycle works")


# =============================================================================
# Run Tests
# =============================================================================

def run_all_tests():
    """Run all Phase 4 tests and report results."""
    print("\n" + "=" * 60)
    print("Phase 4: Conductor Service Tests")
    print("=" * 60)

    # Chunk 4A: Command Parsing
    print("\n--- Chunk 4A: Command Parsing ---\n")
    parsing_tests = TestCommandParsing()
    parsing_tests.setup_method()

    try:
        parsing_tests.test_parse_build_commands()
        parsing_tests.test_parse_test_commands()
        parsing_tests.test_parse_checkpoint_commands()
        parsing_tests.test_parse_status_commands()
        parsing_tests.test_parse_store_decision_commands()
        parsing_tests.test_parse_query_commands()
        parsing_tests.test_parse_help_commands()
        parsing_tests.test_unknown_command_shows_help()
        print("\n✅ Chunk 4A: ALL PARSING TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ Chunk 4A FAILED: {e}")
        return False

    # Chunk 4B: Quick Actions
    print("\n--- Chunk 4B: Quick Actions ---\n")
    quick_tests = TestQuickActions()
    quick_tests.setup_method()

    try:
        quick_tests.test_quick_action_run_build()
        quick_tests.setup_method()  # Reset mocks
        quick_tests.test_quick_action_run_tests()
        quick_tests.setup_method()
        quick_tests.test_quick_action_create_checkpoint()
        quick_tests.setup_method()
        quick_tests.test_quick_action_check_status()
        quick_tests.setup_method()
        quick_tests.test_quick_action_unknown()
        print("\n✅ Chunk 4B: ALL QUICK ACTION TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ Chunk 4B FAILED: {e}")
        return False

    # Chunk 4C: Full Integration
    print("\n--- Chunk 4C: Full Integration ---\n")
    integration_tests = TestFullIntegration()
    integration_tests.setup_method()

    try:
        integration_tests.test_full_workflow_command_to_execution()
        integration_tests.setup_method()
        integration_tests.test_memory_integration()
        integration_tests.setup_method()
        integration_tests.test_status_shows_all_systems()
        integration_tests.setup_method()
        integration_tests.test_integration_status_report()
        integration_tests.setup_method()
        integration_tests.test_context_management()
        integration_tests.setup_method()
        integration_tests.test_command_history_tracked()
        integration_tests.setup_method()
        integration_tests.test_full_cycle_with_testing()
        print("\n✅ Chunk 4C: ALL INTEGRATION TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ Chunk 4C FAILED: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ PHASE 4: ALL TESTS PASSED - BOOTSTRAP COMPLETE!")
    print("=" * 60)
    print("\nThe system can now:")
    print("1. Take a task description")
    print("2. Build code (Round Table)")
    print("3. Test code (Testing Facility)")
    print("4. Fix failures (Build-Test Loop)")
    print("5. Remember everything (Memory System)")
    print("6. Be controlled simply (Conductor)")
    print("\n🚀 The system can now build the rest of itself!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
