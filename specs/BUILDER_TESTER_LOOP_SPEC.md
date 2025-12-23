# Builder-Tester Loop Specification

**Version:** 1.0
**Priority:** HIGH - Build after Memory + Basic Orchestrator
**Purpose:** Automated build → test → fix cycle until code is perfected

---

## Overview

The Builder-Tester Loop is a separate "facility" that takes code from the Round Table,
runs comprehensive tests, and sends failures back for fixes until perfection.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      BUILDER-TESTER LOOP                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌─────────────┐         ┌─────────────┐                          │
│   │  BUILDERS   │         │   TESTERS   │                          │
│   │ (Round      │ ──────► │  (Testing   │                          │
│   │  Table)     │  Code   │   Facility) │                          │
│   │             │         │             │                          │
│   │             │ ◄────── │             │                          │
│   │             │ Failures│             │                          │
│   └─────────────┘         └─────────────┘                          │
│         │                       │                                   │
│         │                       │                                   │
│         └───────────┬───────────┘                                   │
│                     │                                               │
│                     ▼                                               │
│            ┌─────────────────┐                                      │
│            │   ALL TESTS     │                                      │
│            │     PASS        │                                      │
│            └────────┬────────┘                                      │
│                     │                                               │
│                     ▼                                               │
│             [APPROVED CODE]                                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Testing Facility

### Test Categories

| Tier | Category | Tests | Speed |
|------|----------|-------|-------|
| 1 | Syntax | Python compile, AST parse | < 1s |
| 2 | Static Analysis | Linting, type checking, imports | 5-10s |
| 3 | Unit Tests | pytest, function-level tests | 10-30s |
| 4 | Integration | API tests, database tests | 30-60s |
| 5 | App Tests | Full app startup, smoke tests | 1-2min |
| 6 | Security | Vulnerability scan, secrets check | 30s |
| 7 | AI Review | Agent reviews code for issues | 10-30s |

### Test Runner Service

```python
# app/services/testing_facility.py

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import subprocess
import ast
import re
import time

class TestTier(Enum):
    SYNTAX = 1
    STATIC = 2
    UNIT = 3
    INTEGRATION = 4
    APP = 5
    SECURITY = 6
    AI_REVIEW = 7

class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestResult:
    tier: TestTier
    name: str
    status: TestStatus
    duration: float
    message: str = ""
    details: List[str] = None
    file_path: str = None
    line_number: int = None

@dataclass
class TestSuiteResult:
    total_tests: int
    passed: int
    failed: int
    warnings: int
    duration: float
    results: List[TestResult]
    all_passed: bool

class TestingFacility:
    """
    The Testing Facility - runs comprehensive tests on code
    and reports failures for the Builder to fix.
    """

    def __init__(
        self,
        project_path: str,
        enabled_tiers: List[int] = None,
        ai_reviewer = None  # Optional AI agent for code review
    ):
        """
        Initialize Testing Facility.

        Args:
            project_path: Root path of the project
            enabled_tiers: Which test tiers to run (default: 1-5)
            ai_reviewer: Optional AI agent for Tier 7 review
        """
        self.project_path = project_path
        self.enabled_tiers = enabled_tiers or [1, 2, 3, 4, 5]
        self.ai_reviewer = ai_reviewer
        self.results_history: List[TestSuiteResult] = []

    def run_all_tests(
        self,
        code: str = None,
        file_path: str = None,
        stop_on_failure: bool = False
    ) -> TestSuiteResult:
        """
        Run all enabled test tiers.

        Args:
            code: Raw code string to test
            file_path: Or path to file to test
            stop_on_failure: Stop at first failure

        Returns:
            TestSuiteResult with all test outcomes
        """
        start_time = time.time()
        results = []

        # Tier 1: Syntax
        if 1 in self.enabled_tiers:
            result = self.run_syntax_tests(code, file_path)
            results.append(result)
            if stop_on_failure and result.status == TestStatus.FAILED:
                return self._compile_results(results, start_time)

        # Tier 2: Static Analysis
        if 2 in self.enabled_tiers:
            tier_results = self.run_static_analysis(file_path)
            results.extend(tier_results)
            if stop_on_failure and any(r.status == TestStatus.FAILED for r in tier_results):
                return self._compile_results(results, start_time)

        # Tier 3: Unit Tests
        if 3 in self.enabled_tiers:
            tier_results = self.run_unit_tests()
            results.extend(tier_results)
            if stop_on_failure and any(r.status == TestStatus.FAILED for r in tier_results):
                return self._compile_results(results, start_time)

        # Tier 4: Integration Tests
        if 4 in self.enabled_tiers:
            tier_results = self.run_integration_tests()
            results.extend(tier_results)
            if stop_on_failure and any(r.status == TestStatus.FAILED for r in tier_results):
                return self._compile_results(results, start_time)

        # Tier 5: App Tests
        if 5 in self.enabled_tiers:
            result = self.run_app_tests()
            results.append(result)
            if stop_on_failure and result.status == TestStatus.FAILED:
                return self._compile_results(results, start_time)

        # Tier 6: Security
        if 6 in self.enabled_tiers:
            tier_results = self.run_security_tests(file_path)
            results.extend(tier_results)

        # Tier 7: AI Review
        if 7 in self.enabled_tiers and self.ai_reviewer:
            result = self.run_ai_review(code or self._read_file(file_path))
            results.append(result)

        return self._compile_results(results, start_time)

    # =========================================================================
    # Tier 1: Syntax Tests
    # =========================================================================

    def run_syntax_tests(self, code: str = None, file_path: str = None) -> TestResult:
        """Check Python syntax validity."""
        start = time.time()

        if code is None and file_path:
            code = self._read_file(file_path)

        if not code:
            return TestResult(
                tier=TestTier.SYNTAX,
                name="Syntax Check",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="No code provided"
            )

        # Extract code from markdown if needed
        code = self._extract_python_code(code)

        try:
            ast.parse(code)
            return TestResult(
                tier=TestTier.SYNTAX,
                name="Syntax Check",
                status=TestStatus.PASSED,
                duration=time.time() - start,
                message="Syntax valid"
            )
        except SyntaxError as e:
            return TestResult(
                tier=TestTier.SYNTAX,
                name="Syntax Check",
                status=TestStatus.FAILED,
                duration=time.time() - start,
                message=f"Syntax error: {e.msg}",
                details=[f"Line {e.lineno}: {e.text}" if e.text else f"Line {e.lineno}"],
                line_number=e.lineno
            )

    # =========================================================================
    # Tier 2: Static Analysis
    # =========================================================================

    def run_static_analysis(self, file_path: str = None) -> List[TestResult]:
        """Run linting and type checking."""
        results = []

        # Linting with flake8
        if file_path:
            results.append(self._run_flake8(file_path))
            results.append(self._run_mypy(file_path))
        else:
            results.append(self._run_flake8(self.project_path))
            results.append(self._run_mypy(self.project_path))

        # Import check
        results.append(self._check_imports(file_path))

        return results

    def _run_flake8(self, path: str) -> TestResult:
        """Run flake8 linter."""
        start = time.time()
        try:
            result = subprocess.run(
                ["flake8", path, "--max-line-length=120", "--count"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path
            )

            if result.returncode == 0:
                return TestResult(
                    tier=TestTier.STATIC,
                    name="Flake8 Linting",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="No linting issues"
                )
            else:
                issues = result.stdout.strip().split('\n')
                return TestResult(
                    tier=TestTier.STATIC,
                    name="Flake8 Linting",
                    status=TestStatus.WARNING if len(issues) < 10 else TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"{len(issues)} linting issues",
                    details=issues[:20]  # First 20 issues
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                tier=TestTier.STATIC,
                name="Flake8 Linting",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="Linting timed out"
            )
        except FileNotFoundError:
            return TestResult(
                tier=TestTier.STATIC,
                name="Flake8 Linting",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="flake8 not installed"
            )

    def _run_mypy(self, path: str) -> TestResult:
        """Run mypy type checker."""
        start = time.time()
        try:
            result = subprocess.run(
                ["mypy", path, "--ignore-missing-imports", "--no-error-summary"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_path
            )

            if result.returncode == 0:
                return TestResult(
                    tier=TestTier.STATIC,
                    name="MyPy Type Check",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="No type errors"
                )
            else:
                errors = [l for l in result.stdout.strip().split('\n') if l]
                return TestResult(
                    tier=TestTier.STATIC,
                    name="MyPy Type Check",
                    status=TestStatus.WARNING,  # Type errors often warnings
                    duration=time.time() - start,
                    message=f"{len(errors)} type issues",
                    details=errors[:10]
                )

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return TestResult(
                tier=TestTier.STATIC,
                name="MyPy Type Check",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="mypy not available"
            )

    def _check_imports(self, file_path: str = None) -> TestResult:
        """Check that all imports can be resolved."""
        start = time.time()

        # Use Python to check imports
        try:
            result = subprocess.run(
                ["python", "-c", f"import ast; ast.parse(open('{file_path}').read())"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_path
            )

            return TestResult(
                tier=TestTier.STATIC,
                name="Import Check",
                status=TestStatus.PASSED if result.returncode == 0 else TestStatus.FAILED,
                duration=time.time() - start,
                message="Imports valid" if result.returncode == 0 else result.stderr[:200]
            )
        except Exception as e:
            return TestResult(
                tier=TestTier.STATIC,
                name="Import Check",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=str(e)
            )

    # =========================================================================
    # Tier 3: Unit Tests
    # =========================================================================

    def run_unit_tests(self, test_path: str = "tests/") -> List[TestResult]:
        """Run pytest unit tests."""
        start = time.time()
        results = []

        try:
            result = subprocess.run(
                ["pytest", test_path, "-v", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=self.project_path
            )

            # Parse pytest output
            output = result.stdout + result.stderr
            passed = len(re.findall(r'PASSED', output))
            failed = len(re.findall(r'FAILED', output))

            if failed == 0:
                results.append(TestResult(
                    tier=TestTier.UNIT,
                    name="Unit Tests",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message=f"{passed} tests passed"
                ))
            else:
                # Extract failure details
                failures = re.findall(r'FAILED (.+?) -', output)
                results.append(TestResult(
                    tier=TestTier.UNIT,
                    name="Unit Tests",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"{failed} tests failed, {passed} passed",
                    details=failures[:10]
                ))

        except subprocess.TimeoutExpired:
            results.append(TestResult(
                tier=TestTier.UNIT,
                name="Unit Tests",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="Tests timed out (>2min)"
            ))
        except FileNotFoundError:
            results.append(TestResult(
                tier=TestTier.UNIT,
                name="Unit Tests",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="pytest not installed"
            ))

        return results

    # =========================================================================
    # Tier 4: Integration Tests
    # =========================================================================

    def run_integration_tests(self) -> List[TestResult]:
        """Run integration tests (database, API, etc.)."""
        results = []

        # Database connection test
        results.append(self._test_database())

        # API endpoint tests (if applicable)
        # results.append(self._test_api_endpoints())

        return results

    def _test_database(self) -> TestResult:
        """Test database connectivity and basic operations."""
        start = time.time()

        try:
            # Try to import and connect
            result = subprocess.run(
                ["python", "-c", """
from app.core.db import get_db, engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('OK')
"""],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path
            )

            if "OK" in result.stdout:
                return TestResult(
                    tier=TestTier.INTEGRATION,
                    name="Database Connection",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="Database connected"
                )
            else:
                return TestResult(
                    tier=TestTier.INTEGRATION,
                    name="Database Connection",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message="Database connection failed",
                    details=[result.stderr[:300]]
                )

        except Exception as e:
            return TestResult(
                tier=TestTier.INTEGRATION,
                name="Database Connection",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=str(e)
            )

    # =========================================================================
    # Tier 5: App Tests
    # =========================================================================

    def run_app_tests(self) -> TestResult:
        """Test that the full app can start."""
        start = time.time()

        try:
            # Try to import the main app
            result = subprocess.run(
                ["python", "-c", "from app.streamlit_app import main; print('OK')"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path
            )

            if "OK" in result.stdout and result.returncode == 0:
                return TestResult(
                    tier=TestTier.APP,
                    name="App Import Test",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="App imports successfully"
                )
            else:
                return TestResult(
                    tier=TestTier.APP,
                    name="App Import Test",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message="App failed to import",
                    details=[result.stderr[:500]]
                )

        except Exception as e:
            return TestResult(
                tier=TestTier.APP,
                name="App Import Test",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=str(e)
            )

    # =========================================================================
    # Tier 6: Security Tests
    # =========================================================================

    def run_security_tests(self, file_path: str = None) -> List[TestResult]:
        """Run security checks."""
        results = []

        # Check for hardcoded secrets
        results.append(self._check_secrets(file_path))

        # Run bandit if available
        results.append(self._run_bandit(file_path))

        return results

    def _check_secrets(self, file_path: str = None) -> TestResult:
        """Check for hardcoded secrets."""
        start = time.time()

        patterns = [
            r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']',
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']{10,}["\']',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI key pattern
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub token
        ]

        path = file_path or self.project_path
        issues = []

        try:
            result = subprocess.run(
                ["grep", "-rn", "-E", "|".join(patterns), path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout.strip():
                issues = result.stdout.strip().split('\n')

            if issues:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Secrets Check",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"Potential secrets found: {len(issues)}",
                    details=issues[:5]
                )
            else:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Secrets Check",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="No hardcoded secrets detected"
                )

        except Exception as e:
            return TestResult(
                tier=TestTier.SECURITY,
                name="Secrets Check",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=str(e)
            )

    def _run_bandit(self, file_path: str = None) -> TestResult:
        """Run bandit security scanner."""
        start = time.time()

        try:
            path = file_path or self.project_path
            result = subprocess.run(
                ["bandit", "-r", path, "-f", "json", "-q"],
                capture_output=True,
                text=True,
                timeout=60
            )

            import json
            data = json.loads(result.stdout) if result.stdout else {}
            issues = data.get("results", [])

            high_severity = [i for i in issues if i.get("issue_severity") == "HIGH"]

            if high_severity:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Bandit Security Scan",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"{len(high_severity)} high severity issues",
                    details=[f"{i['issue_text']} at {i['filename']}:{i['line_number']}" for i in high_severity[:5]]
                )
            elif issues:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Bandit Security Scan",
                    status=TestStatus.WARNING,
                    duration=time.time() - start,
                    message=f"{len(issues)} issues found (no high severity)"
                )
            else:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Bandit Security Scan",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="No security issues"
                )

        except FileNotFoundError:
            return TestResult(
                tier=TestTier.SECURITY,
                name="Bandit Security Scan",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="bandit not installed"
            )
        except Exception as e:
            return TestResult(
                tier=TestTier.SECURITY,
                name="Bandit Security Scan",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=str(e)
            )

    # =========================================================================
    # Tier 7: AI Review
    # =========================================================================

    def run_ai_review(self, code: str) -> TestResult:
        """Have an AI agent review the code."""
        start = time.time()

        if not self.ai_reviewer:
            return TestResult(
                tier=TestTier.AI_REVIEW,
                name="AI Code Review",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="AI reviewer not configured"
            )

        prompt = f"""Review this code for issues:

```python
{code[:10000]}  # Limit size
```

Look for:
1. Logic errors
2. Edge cases not handled
3. Performance issues
4. Security vulnerabilities
5. Code that doesn't match its intent

Respond with:
- PASS if code is production-ready
- FAIL: [issues] if there are problems

Be concise."""

        try:
            response = self.ai_reviewer.call(prompt)

            if response.upper().startswith("PASS"):
                return TestResult(
                    tier=TestTier.AI_REVIEW,
                    name="AI Code Review",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="AI approved code"
                )
            else:
                return TestResult(
                    tier=TestTier.AI_REVIEW,
                    name="AI Code Review",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message="AI found issues",
                    details=[response[:500]]
                )

        except Exception as e:
            return TestResult(
                tier=TestTier.AI_REVIEW,
                name="AI Code Review",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=str(e)
            )

    # =========================================================================
    # Helpers
    # =========================================================================

    def _compile_results(self, results: List[TestResult], start_time: float) -> TestSuiteResult:
        """Compile individual results into suite result."""
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        warnings = sum(1 for r in results if r.status == TestStatus.WARNING)

        suite = TestSuiteResult(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            duration=time.time() - start_time,
            results=results,
            all_passed=(failed == 0)
        )

        self.results_history.append(suite)
        return suite

    def _extract_python_code(self, text: str) -> str:
        """Extract Python code from markdown if present."""
        if "```python" in text:
            blocks = re.findall(r'```python\n(.*?)```', text, re.DOTALL)
            return "\n\n".join(blocks)
        elif "```" in text:
            blocks = re.findall(r'```\n?(.*?)```', text, re.DOTALL)
            return "\n\n".join(blocks)
        return text

    def _read_file(self, path: str) -> str:
        """Read file contents."""
        try:
            with open(path, 'r') as f:
                return f.read()
        except:
            return ""

    def get_failure_summary(self, suite: TestSuiteResult) -> str:
        """Get formatted summary of failures for sending to Builder."""
        if suite.all_passed:
            return "All tests passed!"

        summary = "## Test Failures\n\n"
        summary += f"**{suite.failed} tests failed, {suite.passed} passed**\n\n"

        for result in suite.results:
            if result.status == TestStatus.FAILED:
                summary += f"### ❌ {result.name}\n"
                summary += f"**Message:** {result.message}\n"
                if result.details:
                    summary += "**Details:**\n"
                    for detail in result.details[:5]:
                        summary += f"- {detail}\n"
                if result.line_number:
                    summary += f"**Line:** {result.line_number}\n"
                summary += "\n"

        return summary
```

---

## The Build-Test-Fix Loop

### Loop Controller

```python
# app/services/build_test_loop.py

class BuildTestLoop:
    """
    Orchestrates the build → test → fix cycle until code is perfected.
    """

    def __init__(
        self,
        roundtable_service,
        testing_facility: TestingFacility,
        max_iterations: int = 5
    ):
        self.rt = roundtable_service
        self.tester = testing_facility
        self.max_iterations = max_iterations

    def run_loop(
        self,
        task: str,
        session_id: int,
        round_id: int
    ) -> Dict:
        """
        Run the build-test-fix loop until success or max iterations.

        Returns:
            Dict with final code, test results, and iteration count
        """
        iteration = 0
        current_code = None
        history = []

        while iteration < self.max_iterations:
            iteration += 1

            # Step 1: Build (or fix)
            if iteration == 1:
                # First iteration: fresh build
                build_result = self.rt.execute_round(round_id)
            else:
                # Subsequent iterations: fix based on test failures
                fix_prompt = self._build_fix_prompt(current_code, test_result)
                build_result = self.rt.execute_round(round_id, override_prompt=fix_prompt)

            if not build_result.get("success"):
                history.append({
                    "iteration": iteration,
                    "phase": "build",
                    "success": False,
                    "error": build_result.get("error")
                })
                continue

            current_code = build_result["builder_response"].content

            # Step 2: Test
            test_result = self.tester.run_all_tests(code=current_code)

            history.append({
                "iteration": iteration,
                "phase": "test",
                "passed": test_result.all_passed,
                "failed_count": test_result.failed,
                "results": test_result
            })

            # Step 3: Check if done
            if test_result.all_passed:
                return {
                    "success": True,
                    "code": current_code,
                    "iterations": iteration,
                    "history": history,
                    "message": f"All tests passed after {iteration} iteration(s)"
                }

        # Max iterations reached
        return {
            "success": False,
            "code": current_code,
            "iterations": iteration,
            "history": history,
            "message": f"Max iterations ({self.max_iterations}) reached. {test_result.failed} tests still failing.",
            "remaining_failures": self.tester.get_failure_summary(test_result)
        }

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
```

---

## Integration with Round Table

### Automatic Testing After Build

```python
# Add to roundtable_service.py

def execute_round_with_testing(
    self,
    round_id: int,
    testing_facility: TestingFacility = None,
    auto_fix: bool = True,
    max_fix_iterations: int = 3
) -> Dict:
    """
    Execute round and automatically run tests.
    Optionally auto-fix if tests fail.
    """
    # Execute build round
    result = self.execute_round(round_id)

    if not result.get("success"):
        return result

    # Run tests if facility provided
    if testing_facility and result.get("builder_response"):
        code = result["builder_response"].content
        test_result = testing_facility.run_all_tests(code=code)

        result["test_results"] = test_result

        # Auto-fix loop if enabled and tests failed
        if auto_fix and not test_result.all_passed:
            loop = BuildTestLoop(
                roundtable_service=self,
                testing_facility=testing_facility,
                max_iterations=max_fix_iterations
            )
            loop_result = loop.run_loop(
                task=self.get_round(round_id).task_prompt,
                session_id=self.get_round(round_id).session_id,
                round_id=round_id
            )
            result["loop_result"] = loop_result

    return result
```

---

## UI Component

```python
# Add to app/ui/testing_panel.py

def render_testing_panel(testing_facility: TestingFacility, latest_result: TestSuiteResult = None):
    """Render testing facility status and controls."""

    st.header("🧪 Testing Facility")

    # Test configuration
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Enabled Tests")
        tiers = {
            1: st.checkbox("Tier 1: Syntax", value=True),
            2: st.checkbox("Tier 2: Static Analysis", value=True),
            3: st.checkbox("Tier 3: Unit Tests", value=True),
            4: st.checkbox("Tier 4: Integration", value=True),
            5: st.checkbox("Tier 5: App Tests", value=True),
            6: st.checkbox("Tier 6: Security", value=False),
            7: st.checkbox("Tier 7: AI Review", value=False),
        }
        testing_facility.enabled_tiers = [k for k, v in tiers.items() if v]

    with col2:
        st.subheader("Loop Settings")
        max_iterations = st.slider("Max fix iterations", 1, 10, 5)
        auto_fix = st.checkbox("Auto-fix on failure", value=True)

    # Results display
    if latest_result:
        st.subheader("Latest Results")

        # Summary bar
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", latest_result.total_tests)
        col2.metric("Passed", latest_result.passed, delta_color="normal")
        col3.metric("Failed", latest_result.failed, delta_color="inverse")
        col4.metric("Duration", f"{latest_result.duration:.1f}s")

        # Status indicator
        if latest_result.all_passed:
            st.success("✅ All tests passed!")
        else:
            st.error(f"❌ {latest_result.failed} tests failed")

        # Detailed results
        with st.expander("Detailed Results"):
            for result in latest_result.results:
                icon = "✅" if result.status == TestStatus.PASSED else "❌" if result.status == TestStatus.FAILED else "⚠️"
                st.write(f"{icon} **{result.name}** ({result.tier.name}) - {result.message}")
                if result.details:
                    for detail in result.details[:3]:
                        st.code(detail)
```

---

## File Structure

```
app/
├── services/
│   ├── testing_facility.py   # NEW - The testing system
│   ├── build_test_loop.py    # NEW - The loop controller
│   └── roundtable_service.py # MODIFY - Add testing integration
└── ui/
    └── testing_panel.py      # NEW - Testing UI
```

---

## Success Criteria

The Builder-Tester Loop is complete when:

1. **All Tiers Work**: Each test tier runs correctly
2. **Loop Functions**: Build → Test → Fix cycle works
3. **Auto-Fix Works**: Failed tests trigger automatic revision
4. **Integration**: Testing is part of round execution flow
5. **Visibility**: UI shows test progress and results
6. **Termination**: Loop stops at success or max iterations

---

*This is the quality gate. No code ships without passing the Testing Facility.*
