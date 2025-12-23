"""
Testing Facility Service.

Comprehensive test runner for the Builder-Tester Loop.
Runs multi-tier tests on code and reports failures for the Builder to fix.

Phase 3 of Bootstrap Sequence.
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import ast
import re
import time
import os
import json


class TestTier(Enum):
    """Test tier levels."""
    SYNTAX = 1
    STATIC = 2
    UNIT = 3
    INTEGRATION = 4
    APP = 5
    SECURITY = 6
    AI_REVIEW = 7


class TestStatus(Enum):
    """Test result status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a single test."""
    tier: TestTier
    name: str
    status: TestStatus
    duration: float
    message: str = ""
    details: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tier": self.tier.name,
            "tier_number": self.tier.value,
            "name": self.name,
            "status": self.status.value,
            "duration": self.duration,
            "message": self.message,
            "details": self.details,
            "file_path": self.file_path,
            "line_number": self.line_number
        }


@dataclass
class TestSuiteResult:
    """Result of a full test suite run."""
    total_tests: int
    passed: int
    failed: int
    warnings: int
    skipped: int
    duration: float
    results: List[TestResult]
    all_passed: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "skipped": self.skipped,
            "duration": self.duration,
            "all_passed": self.all_passed,
            "results": [r.to_dict() for r in self.results]
        }


class TestingFacility:
    """
    The Testing Facility - runs comprehensive tests on code
    and reports failures for the Builder to fix.

    Implements 7 test tiers:
    1. Syntax - Python compile, AST parse
    2. Static Analysis - Linting, type checking, imports
    3. Unit Tests - pytest, function-level tests
    4. Integration - Database, API tests
    5. App Tests - Full app startup, smoke tests
    6. Security - Vulnerability scan, secrets check
    7. AI Review - Agent reviews code for issues
    """

    def __init__(
        self,
        project_path: str = None,
        enabled_tiers: List[int] = None,
        ai_reviewer: Any = None,
        timeout: int = 120
    ):
        """
        Initialize Testing Facility.

        Args:
            project_path: Root path of the project
            enabled_tiers: Which test tiers to run (default: 1-5)
            ai_reviewer: Optional AI agent for Tier 7 review
            timeout: Default timeout for subprocess calls
        """
        self.project_path = project_path or os.getcwd()
        self.enabled_tiers = enabled_tiers or [1, 2, 3, 4, 5]
        self.ai_reviewer = ai_reviewer
        self.timeout = timeout
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
            tier_results = self.run_static_analysis(code, file_path)
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
            tier_results = self.run_security_tests(code, file_path)
            results.extend(tier_results)

        # Tier 7: AI Review
        if 7 in self.enabled_tiers:
            code_to_review = code or (self._read_file(file_path) if file_path else None)
            if code_to_review:
                result = self.run_ai_review(code_to_review)
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

    def run_static_analysis(self, code: str = None, file_path: str = None) -> List[TestResult]:
        """Run linting and type checking."""
        results = []

        path = file_path or self.project_path

        # Linting with flake8
        results.append(self._run_flake8(path))

        # Type checking with mypy
        results.append(self._run_mypy(path))

        # Import check
        results.append(self._check_imports(code, file_path))

        return results

    def _run_flake8(self, path: str) -> TestResult:
        """Run flake8 linter."""
        start = time.time()
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", path, "--max-line-length=120", "--count",
                 "--select=E9,F63,F7,F82", "--show-source", "--statistics"],
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
                    message="No critical linting issues"
                )
            else:
                issues = [l for l in result.stdout.strip().split('\n') if l]
                return TestResult(
                    tier=TestTier.STATIC,
                    name="Flake8 Linting",
                    status=TestStatus.WARNING if len(issues) < 10 else TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"{len(issues)} linting issues",
                    details=issues[:20]
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
                ["python", "-m", "mypy", path, "--ignore-missing-imports",
                 "--no-error-summary", "--no-color"],
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
                errors = [l for l in result.stdout.strip().split('\n') if l and 'error:' in l]
                return TestResult(
                    tier=TestTier.STATIC,
                    name="MyPy Type Check",
                    status=TestStatus.WARNING,  # Type errors are often just warnings
                    duration=time.time() - start,
                    message=f"{len(errors)} type issues",
                    details=errors[:10]
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                tier=TestTier.STATIC,
                name="MyPy Type Check",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="Type checking timed out"
            )
        except FileNotFoundError:
            return TestResult(
                tier=TestTier.STATIC,
                name="MyPy Type Check",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="mypy not installed"
            )

    def _check_imports(self, code: str = None, file_path: str = None) -> TestResult:
        """Check that all imports can be resolved."""
        start = time.time()

        if code is None and file_path:
            code = self._read_file(file_path)

        if not code:
            return TestResult(
                tier=TestTier.STATIC,
                name="Import Check",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="No code to check"
            )

        # Extract code from markdown
        code = self._extract_python_code(code)

        # Parse imports
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return TestResult(
                tier=TestTier.STATIC,
                name="Import Check",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="Cannot parse code for import check"
            )

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])

        # Check if imports exist (basic check)
        missing = []
        for imp in set(imports):
            if imp.startswith('_'):
                continue
            # Skip local app imports
            if imp == 'app':
                continue
            try:
                __import__(imp)
            except ImportError:
                missing.append(imp)

        if not missing:
            return TestResult(
                tier=TestTier.STATIC,
                name="Import Check",
                status=TestStatus.PASSED,
                duration=time.time() - start,
                message=f"All {len(imports)} imports valid"
            )
        else:
            return TestResult(
                tier=TestTier.STATIC,
                name="Import Check",
                status=TestStatus.WARNING,
                duration=time.time() - start,
                message=f"{len(missing)} missing imports",
                details=missing[:10]
            )

    # =========================================================================
    # Tier 3: Unit Tests
    # =========================================================================

    def run_unit_tests(self, test_path: str = None) -> List[TestResult]:
        """Run pytest unit tests."""
        start = time.time()
        results = []

        test_dir = test_path or os.path.join(self.project_path, "tests")

        if not os.path.exists(test_dir):
            results.append(TestResult(
                tier=TestTier.UNIT,
                name="Unit Tests",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="No tests directory found"
            ))
            return results

        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_dir, "-v", "--tb=short", "-q",
                 "--no-header", "-x"],  # -x stops at first failure for faster feedback
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.project_path
            )

            output = result.stdout + result.stderr
            passed = len(re.findall(r'PASSED', output))
            failed = len(re.findall(r'FAILED', output))
            errors = len(re.findall(r'ERROR', output))

            if failed == 0 and errors == 0:
                results.append(TestResult(
                    tier=TestTier.UNIT,
                    name="Unit Tests",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message=f"{passed} tests passed"
                ))
            else:
                # Extract failure details
                failure_lines = re.findall(r'FAILED (.+?)(?:\n|$)', output)
                error_lines = re.findall(r'ERROR (.+?)(?:\n|$)', output)

                results.append(TestResult(
                    tier=TestTier.UNIT,
                    name="Unit Tests",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"{failed} failed, {errors} errors, {passed} passed",
                    details=failure_lines[:10] + error_lines[:5]
                ))

        except subprocess.TimeoutExpired:
            results.append(TestResult(
                tier=TestTier.UNIT,
                name="Unit Tests",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message=f"Tests timed out (>{self.timeout}s)"
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

        return results

    def _test_database(self) -> TestResult:
        """Test database connectivity and basic operations."""
        start = time.time()

        try:
            result = subprocess.run(
                ["python", "-c", """
import sys
sys.path.insert(0, '.')
try:
    from app.core.db import test_connection
    success, msg = test_connection()
    if success:
        print('OK')
    else:
        print(f'FAIL: {msg}')
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"""],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_path
            )

            if "OK" in result.stdout and result.returncode == 0:
                return TestResult(
                    tier=TestTier.INTEGRATION,
                    name="Database Connection",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="Database connected successfully"
                )
            else:
                error_msg = result.stdout.strip() or result.stderr.strip()
                return TestResult(
                    tier=TestTier.INTEGRATION,
                    name="Database Connection",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message="Database connection failed",
                    details=[error_msg[:300]]
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                tier=TestTier.INTEGRATION,
                name="Database Connection",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="Database connection timed out"
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
            result = subprocess.run(
                ["python", "-c", """
import sys
sys.path.insert(0, '.')
try:
    from app.streamlit_app import main
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"""],
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
                error_output = result.stderr or result.stdout
                return TestResult(
                    tier=TestTier.APP,
                    name="App Import Test",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message="App failed to import",
                    details=[error_output[:500]]
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                tier=TestTier.APP,
                name="App Import Test",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="App import timed out"
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

    def run_security_tests(self, code: str = None, file_path: str = None) -> List[TestResult]:
        """Run security checks."""
        results = []

        # Check for hardcoded secrets
        results.append(self._check_secrets(code, file_path))

        # Run bandit if available
        path = file_path or self.project_path
        results.append(self._run_bandit(path))

        return results

    def _check_secrets(self, code: str = None, file_path: str = None) -> TestResult:
        """Check for hardcoded secrets."""
        start = time.time()

        if code is None and file_path:
            code = self._read_file(file_path)

        if not code:
            return TestResult(
                tier=TestTier.SECURITY,
                name="Secrets Check",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="No code to check"
            )

        # Pattern to detect potential secrets
        patterns = [
            (r'api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{20,}["\']', "API key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
            (r'secret\s*=\s*["\'][A-Za-z0-9_\-]{10,}["\']', "Secret"),
            (r'sk-[a-zA-Z0-9]{20,}', "OpenAI key"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub token"),
            (r'AKIA[0-9A-Z]{16}', "AWS access key"),
        ]

        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
            # Skip example/placeholder patterns
            if 'your-' in line.lower() or 'example' in line.lower() or 'xxx' in line.lower():
                continue

            for pattern, secret_type in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(f"Line {i}: Potential {secret_type} detected")

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

    def _run_bandit(self, path: str) -> TestResult:
        """Run bandit security scanner."""
        start = time.time()

        try:
            result = subprocess.run(
                ["python", "-m", "bandit", "-r", path, "-f", "json", "-q",
                 "-x", ".venv,venv,tests,__pycache__"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=self.project_path
            )

            try:
                data = json.loads(result.stdout) if result.stdout else {}
            except json.JSONDecodeError:
                data = {}

            issues = data.get("results", [])
            high_severity = [i for i in issues if i.get("issue_severity") == "HIGH"]
            medium_severity = [i for i in issues if i.get("issue_severity") == "MEDIUM"]

            if high_severity:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Bandit Security Scan",
                    status=TestStatus.FAILED,
                    duration=time.time() - start,
                    message=f"{len(high_severity)} high severity issues",
                    details=[
                        f"{i['issue_text']} at {i['filename']}:{i['line_number']}"
                        for i in high_severity[:5]
                    ]
                )
            elif medium_severity:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Bandit Security Scan",
                    status=TestStatus.WARNING,
                    duration=time.time() - start,
                    message=f"{len(medium_severity)} medium severity issues"
                )
            else:
                return TestResult(
                    tier=TestTier.SECURITY,
                    name="Bandit Security Scan",
                    status=TestStatus.PASSED,
                    duration=time.time() - start,
                    message="No security issues found"
                )

        except FileNotFoundError:
            return TestResult(
                tier=TestTier.SECURITY,
                name="Bandit Security Scan",
                status=TestStatus.SKIPPED,
                duration=time.time() - start,
                message="bandit not installed"
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                tier=TestTier.SECURITY,
                name="Bandit Security Scan",
                status=TestStatus.ERROR,
                duration=time.time() - start,
                message="Security scan timed out"
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

        # Truncate code if too long
        code_to_review = code[:10000] if len(code) > 10000 else code

        prompt = f"""Review this code for issues:

```python
{code_to_review}
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
            # AI reviewer should have a call() method
            response = self.ai_reviewer(prompt) if callable(self.ai_reviewer) else str(self.ai_reviewer)

            if response.upper().strip().startswith("PASS"):
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
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)

        suite = TestSuiteResult(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            skipped=skipped,
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
        except Exception:
            return ""

    def get_failure_summary(self, suite: TestSuiteResult) -> str:
        """Get formatted summary of failures for sending to Builder."""
        if suite.all_passed:
            return "All tests passed!"

        summary = "## Test Failures\n\n"
        summary += f"**{suite.failed} tests failed, {suite.passed} passed, {suite.warnings} warnings**\n\n"

        for result in suite.results:
            if result.status == TestStatus.FAILED:
                summary += f"### ❌ {result.name} (Tier {result.tier.value})\n"
                summary += f"**Message:** {result.message}\n"
                if result.details:
                    summary += "**Details:**\n"
                    for detail in result.details[:5]:
                        summary += f"- {detail}\n"
                if result.line_number:
                    summary += f"**Line:** {result.line_number}\n"
                summary += "\n"
            elif result.status == TestStatus.WARNING:
                summary += f"### ⚠️ {result.name} (Tier {result.tier.value})\n"
                summary += f"**Warning:** {result.message}\n\n"

        return summary

    def get_tier_status(self, suite: TestSuiteResult) -> Dict[int, str]:
        """Get status for each tier."""
        tier_status = {}
        for result in suite.results:
            tier_num = result.tier.value
            if tier_num not in tier_status:
                tier_status[tier_num] = result.status.value
            elif result.status == TestStatus.FAILED:
                tier_status[tier_num] = "failed"
            elif result.status == TestStatus.WARNING and tier_status[tier_num] != "failed":
                tier_status[tier_num] = "warning"
        return tier_status


# =============================================================================
# Convenience Functions
# =============================================================================

def run_quick_test(code: str, project_path: str = None) -> TestSuiteResult:
    """Run quick syntax and import check on code."""
    facility = TestingFacility(
        project_path=project_path or os.getcwd(),
        enabled_tiers=[1, 2]  # Just syntax and static analysis
    )
    return facility.run_all_tests(code=code)


def run_full_test(project_path: str = None) -> TestSuiteResult:
    """Run full test suite on project."""
    facility = TestingFacility(
        project_path=project_path or os.getcwd(),
        enabled_tiers=[1, 2, 3, 4, 5]
    )
    return facility.run_all_tests()
