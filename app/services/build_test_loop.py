"""
Build-Test-Fix Loop Service.

Orchestrates the build → test → fix cycle until code is perfected.
Takes code from the Round Table, runs comprehensive tests, and sends
failures back for fixes until perfection.

Phase 3 of Bootstrap Sequence.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

# Import testing facility components - handle import errors gracefully
try:
    from app.services.testing_facility import (
        TestingFacility,
        TestSuiteResult,
        TestStatus,
        TestResult,
    )
except ImportError:
    # Allow module to be imported standalone for testing
    TestingFacility = None
    TestSuiteResult = None
    TestStatus = None
    TestResult = None


class LoopStatus(Enum):
    """Status of a build-test loop."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"
    ERROR = "error"


@dataclass
class LoopIteration:
    """Record of a single iteration in the loop."""
    iteration: int
    phase: str  # "build" or "test"
    timestamp: datetime
    success: bool
    code: Optional[str] = None
    test_result: Optional[TestSuiteResult] = None
    error: Optional[str] = None
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "iteration": self.iteration,
            "phase": self.phase,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "code_length": len(self.code) if self.code else 0,
            "test_result": self.test_result.to_dict() if self.test_result else None,
            "error": self.error,
            "duration": self.duration
        }


@dataclass
class LoopResult:
    """Final result of a build-test loop."""
    status: LoopStatus
    success: bool
    final_code: Optional[str]
    iterations: int
    total_duration: float
    history: List[LoopIteration]
    message: str
    remaining_failures: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "success": self.success,
            "final_code_length": len(self.final_code) if self.final_code else 0,
            "iterations": self.iterations,
            "total_duration": self.total_duration,
            "history": [h.to_dict() for h in self.history],
            "message": self.message,
            "remaining_failures": self.remaining_failures
        }


class BuildTestLoop:
    """
    Orchestrates the build → test → fix cycle until code is perfected.

    The loop:
    1. Gets initial code from builder (Round Table)
    2. Runs tests (Testing Facility)
    3. If tests fail, sends failures back for fixes
    4. Repeats until all tests pass or max iterations reached
    """

    def __init__(
        self,
        testing_facility: TestingFacility,
        builder_func: Callable[[str], str] = None,
        max_iterations: int = 5,
        stop_on_first_failure: bool = False
    ):
        """
        Initialize the Build-Test Loop.

        Args:
            testing_facility: The TestingFacility instance for running tests
            builder_func: Optional function that takes a prompt and returns code
                         (typically wraps RoundTable execute_round)
            max_iterations: Maximum fix iterations before giving up
            stop_on_first_failure: Stop testing at first failure per iteration
        """
        self.tester = testing_facility
        self.builder_func = builder_func
        self.max_iterations = max_iterations
        self.stop_on_first_failure = stop_on_first_failure
        self.current_status = LoopStatus.PENDING

    def run_loop(
        self,
        initial_code: str = None,
        task_prompt: str = None,
        builder_func: Callable[[str], str] = None
    ) -> LoopResult:
        """
        Run the build-test-fix loop until success or max iterations.

        Args:
            initial_code: Starting code to test (skip first build if provided)
            task_prompt: Task prompt for initial build (if no initial_code)
            builder_func: Optional builder function override

        Returns:
            LoopResult with final code, test results, and iteration count
        """
        start_time = time.time()
        iteration = 0
        history: List[LoopIteration] = []
        current_code = initial_code
        builder = builder_func or self.builder_func

        self.current_status = LoopStatus.RUNNING

        while iteration < self.max_iterations:
            iteration += 1
            iter_start = time.time()

            # Step 1: Build (or use existing code)
            if current_code is None or iteration > 1:
                if builder is None:
                    # Can't build without a builder
                    if current_code is None:
                        return LoopResult(
                            status=LoopStatus.ERROR,
                            success=False,
                            final_code=None,
                            iterations=iteration,
                            total_duration=time.time() - start_time,
                            history=history,
                            message="No builder function and no initial code provided"
                        )
                else:
                    # Build or fix
                    try:
                        if iteration == 1:
                            # Initial build
                            prompt = task_prompt or "Build the code"
                        else:
                            # Fix based on test failures
                            prompt = self._build_fix_prompt(current_code, test_result)

                        current_code = builder(prompt)

                        history.append(LoopIteration(
                            iteration=iteration,
                            phase="build",
                            timestamp=datetime.utcnow(),
                            success=True,
                            code=current_code,
                            duration=time.time() - iter_start
                        ))

                    except Exception as e:
                        history.append(LoopIteration(
                            iteration=iteration,
                            phase="build",
                            timestamp=datetime.utcnow(),
                            success=False,
                            error=str(e),
                            duration=time.time() - iter_start
                        ))
                        continue  # Try again next iteration

            # Step 2: Test
            test_start = time.time()
            try:
                test_result = self.tester.run_all_tests(
                    code=current_code,
                    stop_on_failure=self.stop_on_first_failure
                )

                history.append(LoopIteration(
                    iteration=iteration,
                    phase="test",
                    timestamp=datetime.utcnow(),
                    success=test_result.all_passed,
                    code=current_code,
                    test_result=test_result,
                    duration=time.time() - test_start
                ))

            except Exception as e:
                history.append(LoopIteration(
                    iteration=iteration,
                    phase="test",
                    timestamp=datetime.utcnow(),
                    success=False,
                    error=str(e),
                    duration=time.time() - test_start
                ))
                continue

            # Step 3: Check if done
            if test_result.all_passed:
                self.current_status = LoopStatus.PASSED
                return LoopResult(
                    status=LoopStatus.PASSED,
                    success=True,
                    final_code=current_code,
                    iterations=iteration,
                    total_duration=time.time() - start_time,
                    history=history,
                    message=f"All tests passed after {iteration} iteration(s)"
                )

            # If we have no builder, we can't fix - return with failures
            if builder is None:
                self.current_status = LoopStatus.FAILED
                return LoopResult(
                    status=LoopStatus.FAILED,
                    success=False,
                    final_code=current_code,
                    iterations=iteration,
                    total_duration=time.time() - start_time,
                    history=history,
                    message=f"{test_result.failed} tests failed, no builder to fix",
                    remaining_failures=self.tester.get_failure_summary(test_result)
                )

        # Max iterations reached
        self.current_status = LoopStatus.MAX_ITERATIONS
        return LoopResult(
            status=LoopStatus.MAX_ITERATIONS,
            success=False,
            final_code=current_code,
            iterations=iteration,
            total_duration=time.time() - start_time,
            history=history,
            message=f"Max iterations ({self.max_iterations}) reached. {test_result.failed} tests still failing.",
            remaining_failures=self.tester.get_failure_summary(test_result)
        )

    def _build_fix_prompt(self, code: str, test_result: TestSuiteResult) -> str:
        """Build prompt for fixing failed tests."""
        failures = self.tester.get_failure_summary(test_result)

        return f"""The previous code has test failures that need to be fixed.

## Previous Code
```python
{code}
```

## Test Failures
{failures}

## Your Task
Fix the code to make all tests pass. Only modify what's necessary.
Return the complete fixed code.
"""

    def test_code_only(self, code: str) -> TestSuiteResult:
        """
        Just test code without the fix loop.

        Args:
            code: Code to test

        Returns:
            TestSuiteResult with test outcomes
        """
        return self.tester.run_all_tests(
            code=code,
            stop_on_failure=self.stop_on_first_failure
        )


class BuildTestLoopWithRoundtable:
    """
    Integration layer between Build-Test Loop and Roundtable Service.

    This class connects the testing facility with the roundtable execution
    to enable automatic testing after builds and fix iterations.
    """

    def __init__(
        self,
        roundtable_service: Any,
        testing_facility: TestingFacility,
        max_iterations: int = 3
    ):
        """
        Initialize with Roundtable service and Testing Facility.

        Args:
            roundtable_service: The RoundtableService instance
            testing_facility: The TestingFacility instance
            max_iterations: Maximum fix iterations
        """
        self.rt = roundtable_service
        self.tester = testing_facility
        self.max_iterations = max_iterations

    def execute_round_with_testing(
        self,
        round_id: int,
        auto_fix: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a round and automatically run tests.
        Optionally auto-fix if tests fail.

        Args:
            round_id: Round ID to execute
            auto_fix: Whether to auto-fix on test failures

        Returns:
            Dictionary with execution results including test results
        """
        # Execute initial build round
        result = self.rt.execute_round(round_id)

        if not result.get("success"):
            return result

        # Run tests if builder produced output
        if result.get("builder_response") and result["builder_response"].content:
            code = result["builder_response"].content
            test_result = self.tester.run_all_tests(code=code)
            result["test_results"] = test_result

            # Auto-fix loop if enabled and tests failed
            if auto_fix and not test_result.all_passed:
                # Create a builder function that uses roundtable
                def roundtable_builder(prompt: str) -> str:
                    # Update the round's task prompt
                    self.rt.update_round(round_id, task_prompt=prompt)
                    # Execute again
                    fix_result = self.rt.execute_round(round_id)
                    if fix_result.get("builder_response"):
                        return fix_result["builder_response"].content
                    return ""

                loop = BuildTestLoop(
                    testing_facility=self.tester,
                    builder_func=roundtable_builder,
                    max_iterations=self.max_iterations
                )

                loop_result = loop.run_loop(
                    initial_code=code,
                    task_prompt=None  # Will use fix prompts
                )

                result["loop_result"] = loop_result.to_dict()
                result["final_code"] = loop_result.final_code
                result["all_tests_passed"] = loop_result.success

        return result

    def run_test_only(
        self,
        round_id: int
    ) -> Dict[str, Any]:
        """
        Get the latest builder response from a round and test it.

        Args:
            round_id: Round ID to get response from

        Returns:
            Dictionary with test results
        """
        responses = self.rt.get_round_responses(round_id)

        if not responses.get("builder") or not responses["builder"]["response"]:
            return {
                "success": False,
                "error": "No builder response found for this round"
            }

        code = responses["builder"]["response"].content
        test_result = self.tester.run_all_tests(code=code)

        return {
            "success": True,
            "test_results": test_result,
            "all_passed": test_result.all_passed,
            "summary": self.tester.get_failure_summary(test_result)
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_loop_for_project(project_path: str, max_iterations: int = 5) -> BuildTestLoop:
    """
    Create a BuildTestLoop for a project.

    Args:
        project_path: Path to the project
        max_iterations: Max fix iterations

    Returns:
        Configured BuildTestLoop instance
    """
    facility = TestingFacility(
        project_path=project_path,
        enabled_tiers=[1, 2, 3, 4, 5]  # All core tiers
    )
    return BuildTestLoop(
        testing_facility=facility,
        max_iterations=max_iterations
    )


def quick_test_loop(
    code: str,
    project_path: str = None,
    builder_func: Callable[[str], str] = None
) -> LoopResult:
    """
    Run a quick test loop on code.

    Args:
        code: Code to test
        project_path: Project path for tests
        builder_func: Optional builder for fixes

    Returns:
        LoopResult
    """
    import os
    facility = TestingFacility(
        project_path=project_path or os.getcwd(),
        enabled_tiers=[1, 2]  # Just syntax and static
    )
    loop = BuildTestLoop(
        testing_facility=facility,
        builder_func=builder_func,
        max_iterations=3
    )
    return loop.run_loop(initial_code=code)
