"""
Tests for Phase 3: Build-Test Loop.

Tests the build-test-fix cycle functionality.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.testing_facility import (
    TestingFacility,
    TestStatus,
)
from app.services.build_test_loop import (
    BuildTestLoop,
    LoopResult,
    LoopStatus,
    LoopIteration,
    create_loop_for_project,
    quick_test_loop,
)


# =============================================================================
# BuildTestLoop Tests
# =============================================================================

class TestBuildTestLoop:
    """Test the BuildTestLoop class."""

    def test_loop_with_passing_code(self):
        """Test loop with code that passes all tests."""
        facility = TestingFacility(enabled_tiers=[1])  # Just syntax
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=3
        )

        result = loop.run_loop(initial_code="x = 1 + 2")

        assert result.success is True
        assert result.status == LoopStatus.PASSED
        assert result.iterations == 1
        print("✅ Loop: Passing code completes in 1 iteration")

    def test_loop_with_failing_code_no_builder(self):
        """Test loop with failing code and no builder to fix."""
        facility = TestingFacility(enabled_tiers=[1])  # Just syntax
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=3
        )

        result = loop.run_loop(initial_code="def broken(")

        assert result.success is False
        assert result.status == LoopStatus.FAILED
        assert result.remaining_failures is not None
        print("✅ Loop: Failing code without builder fails correctly")

    def test_loop_with_builder_function(self):
        """Test loop with a mock builder function."""
        facility = TestingFacility(enabled_tiers=[1])

        # Mock builder that "fixes" the code
        fix_count = [0]
        def mock_builder(prompt: str) -> str:
            fix_count[0] += 1
            if "fix" in prompt.lower() or fix_count[0] > 1:
                return "x = 1 + 2"  # Fixed code
            return "def broken("  # Still broken

        loop = BuildTestLoop(
            testing_facility=facility,
            builder_func=mock_builder,
            max_iterations=5
        )

        result = loop.run_loop(task_prompt="Write some code")

        assert result.success is True
        assert result.iterations <= 3
        print(f"✅ Loop: Builder fixed code in {result.iterations} iterations")

    def test_loop_max_iterations(self):
        """Test that loop respects max iterations."""
        facility = TestingFacility(enabled_tiers=[1])

        # Mock builder that never fixes
        def always_broken(prompt: str) -> str:
            return "def still_broken("

        loop = BuildTestLoop(
            testing_facility=facility,
            builder_func=always_broken,
            max_iterations=3
        )

        result = loop.run_loop(task_prompt="Write some code")

        assert result.success is False
        assert result.status == LoopStatus.MAX_ITERATIONS
        assert result.iterations == 3
        print("✅ Loop: Max iterations respected")

    def test_loop_history_tracking(self):
        """Test that loop tracks iteration history."""
        facility = TestingFacility(enabled_tiers=[1])
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=3
        )

        result = loop.run_loop(initial_code="x = 1")

        assert len(result.history) > 0
        assert all(isinstance(h, LoopIteration) for h in result.history)
        print("✅ Loop: History tracking works")

    def test_loop_result_to_dict(self):
        """Test LoopResult serialization."""
        facility = TestingFacility(enabled_tiers=[1])
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=3
        )

        result = loop.run_loop(initial_code="x = 1")
        result_dict = result.to_dict()

        assert "status" in result_dict
        assert "success" in result_dict
        assert "iterations" in result_dict
        assert "history" in result_dict
        print("✅ Loop: Result serialization works")

    def test_test_code_only(self):
        """Test the test_code_only method."""
        facility = TestingFacility(enabled_tiers=[1, 2])
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=3
        )

        result = loop.test_code_only("x = 1 + 2")

        assert result.total_tests > 0
        print("✅ Loop: test_code_only works")


# =============================================================================
# Convenience Functions Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_loop_for_project(self):
        """Test creating a loop for a project."""
        loop = create_loop_for_project(
            project_path="/home/user/Digi-TS",
            max_iterations=5
        )

        assert isinstance(loop, BuildTestLoop)
        assert loop.max_iterations == 5
        print("✅ Convenience: create_loop_for_project works")

    def test_quick_test_loop(self):
        """Test quick test loop function."""
        result = quick_test_loop(
            code="x = 1 + 2",
            project_path="/home/user/Digi-TS"
        )

        assert isinstance(result, LoopResult)
        print("✅ Convenience: quick_test_loop works")


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for build-test loop."""

    def test_loop_with_multiple_tiers(self):
        """Test loop with multiple test tiers."""
        facility = TestingFacility(
            project_path="/home/user/Digi-TS",
            enabled_tiers=[1, 2]  # Syntax and static
        )
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=2
        )

        code = """
import os

def get_cwd():
    return os.getcwd()

result = get_cwd()
"""
        result = loop.run_loop(initial_code=code)

        # Should run multiple tiers
        assert result.history[0].test_result is not None
        print("✅ Integration: Multiple tiers work")

    def test_stop_on_first_failure(self):
        """Test stop_on_first_failure option."""
        facility = TestingFacility(enabled_tiers=[1, 2, 3, 4, 5])
        loop = BuildTestLoop(
            testing_facility=facility,
            max_iterations=2,
            stop_on_first_failure=True
        )

        # Code with syntax error should stop early
        result = loop.run_loop(initial_code="def broken(")

        assert not result.success
        # Should have stopped after first failure
        if result.history and result.history[0].test_result:
            assert result.history[0].test_result.total_tests <= 2
        print("✅ Integration: Stop on first failure works")


# =============================================================================
# Run Tests
# =============================================================================

def run_all_build_test_loop_tests():
    """Run all build-test loop tests and report results."""
    print("\n" + "=" * 60)
    print("PHASE 3: BUILD-TEST LOOP TESTS")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0
    errors = []

    # BuildTestLoop Tests
    print("\n--- BuildTestLoop ---")
    tests = [
        ("loop_with_passing_code", TestBuildTestLoop().test_loop_with_passing_code),
        ("loop_with_failing_code_no_builder", TestBuildTestLoop().test_loop_with_failing_code_no_builder),
        ("loop_with_builder_function", TestBuildTestLoop().test_loop_with_builder_function),
        ("loop_max_iterations", TestBuildTestLoop().test_loop_max_iterations),
        ("loop_history_tracking", TestBuildTestLoop().test_loop_history_tracking),
        ("loop_result_to_dict", TestBuildTestLoop().test_loop_result_to_dict),
        ("test_code_only", TestBuildTestLoop().test_test_code_only),
    ]

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append(f"{name}: {e}")

    # Convenience Functions
    print("\n--- Convenience Functions ---")
    try:
        TestConvenienceFunctions().test_create_loop_for_project()
        passed += 1
    except Exception as e:
        failed += 1
        errors.append(f"create_loop_for_project: {e}")

    try:
        TestConvenienceFunctions().test_quick_test_loop()
        passed += 1
    except Exception as e:
        failed += 1
        errors.append(f"quick_test_loop: {e}")

    # Integration Tests
    print("\n--- Integration ---")
    try:
        TestIntegration().test_loop_with_multiple_tiers()
        passed += 1
    except Exception as e:
        failed += 1
        errors.append(f"multiple_tiers: {e}")

    try:
        TestIntegration().test_stop_on_first_failure()
        passed += 1
    except Exception as e:
        failed += 1
        errors.append(f"stop_on_first_failure: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  ❌ {err}")

    if failed == 0:
        print("\n✅ ALL PHASE 3 BUILD-TEST LOOP TESTS PASSED!")
    else:
        print(f"\n⚠️ {failed} tests failed")

    return passed, failed


if __name__ == "__main__":
    run_all_build_test_loop_tests()
