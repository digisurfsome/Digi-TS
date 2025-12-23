"""
Testing Panel UI Component.

Provides UI for the Testing Facility:
- Test configuration (enable/disable tiers)
- Manual test execution
- Test results display
- Build-Test Loop controls

Phase 3 of Bootstrap Sequence.
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from app.services.testing_facility import (
        TestingFacility,
        TestSuiteResult,
        TestResult,
        TestStatus,
        TestTier,
    )
    from app.services.build_test_loop import (
        BuildTestLoop,
        LoopResult,
        LoopStatus,
    )
    TESTING_AVAILABLE = True
except ImportError:
    TESTING_AVAILABLE = False


# Tier descriptions for display
TIER_INFO = {
    1: {"name": "Syntax", "desc": "Python compile, AST parse", "icon": "📝"},
    2: {"name": "Static Analysis", "desc": "Linting, type checking, imports", "icon": "🔍"},
    3: {"name": "Unit Tests", "desc": "pytest, function-level tests", "icon": "🧪"},
    4: {"name": "Integration", "desc": "Database, API tests", "icon": "🔗"},
    5: {"name": "App Tests", "desc": "Full app startup, smoke tests", "icon": "🚀"},
    6: {"name": "Security", "desc": "Vulnerability scan, secrets check", "icon": "🔒"},
    7: {"name": "AI Review", "desc": "Agent code review", "icon": "🤖"},
}


def render_testing_panel(
    testing_facility: Optional["TestingFacility"] = None,
    project_path: str = None
) -> None:
    """
    Render the main testing panel.

    Args:
        testing_facility: Optional pre-configured TestingFacility
        project_path: Project path if creating new facility
    """
    st.header("🧪 Testing Facility")

    if not TESTING_AVAILABLE:
        st.error("Testing system not available. Check imports.")
        return

    # Initialize testing facility in session state
    if "testing_facility" not in st.session_state:
        if testing_facility:
            st.session_state.testing_facility = testing_facility
        elif project_path:
            st.session_state.testing_facility = TestingFacility(
                project_path=project_path,
                enabled_tiers=[1, 2, 3, 4, 5]
            )
        else:
            st.session_state.testing_facility = TestingFacility(
                enabled_tiers=[1, 2, 3, 4, 5]
            )

    facility = st.session_state.testing_facility

    # Create tabs for different sections
    config_tab, run_tab, results_tab, loop_tab = st.tabs([
        "⚙️ Configuration",
        "▶️ Run Tests",
        "📊 Results",
        "🔄 Build-Test Loop"
    ])

    with config_tab:
        _render_configuration(facility)

    with run_tab:
        _render_run_tests(facility)

    with results_tab:
        _render_results()

    with loop_tab:
        _render_loop_controls(facility)


def _render_configuration(facility: "TestingFacility") -> None:
    """Render test configuration section."""
    st.subheader("Test Tier Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Enable/Disable Test Tiers:**")

        enabled_tiers = []
        for tier_num in range(1, 8):
            tier_info = TIER_INFO.get(tier_num, {})
            label = f"{tier_info.get('icon', '🔷')} Tier {tier_num}: {tier_info.get('name', 'Unknown')}"
            default = tier_num in facility.enabled_tiers
            enabled = st.checkbox(
                label,
                value=default,
                key=f"tier_{tier_num}_enabled",
                help=tier_info.get('desc', '')
            )
            if enabled:
                enabled_tiers.append(tier_num)

        # Update facility if changed
        if enabled_tiers != facility.enabled_tiers:
            facility.enabled_tiers = enabled_tiers
            st.success("Test tiers updated!")

    with col2:
        st.write("**Tier Details:**")
        for tier_num in range(1, 8):
            tier_info = TIER_INFO.get(tier_num, {})
            status = "✅ Enabled" if tier_num in facility.enabled_tiers else "⏸️ Disabled"
            st.write(f"**{tier_info.get('name', 'Tier ' + str(tier_num))}:** {tier_info.get('desc', 'N/A')}")
            st.caption(status)

    st.divider()

    # Other settings
    st.subheader("Other Settings")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Project Path:** `{facility.project_path}`")
        st.write(f"**Timeout:** {facility.timeout}s")

    with col2:
        st.write(f"**AI Reviewer:** {'Configured' if facility.ai_reviewer else 'Not configured'}")
        st.write(f"**Results History:** {len(facility.results_history)} runs")


def _render_run_tests(facility: "TestingFacility") -> None:
    """Render manual test execution section."""
    st.subheader("Run Tests")

    # Option to test code directly or a file
    test_type = st.radio(
        "Test Type",
        ["Test Code Snippet", "Test File", "Test Project"],
        horizontal=True
    )

    if test_type == "Test Code Snippet":
        code = st.text_area(
            "Enter Python code to test:",
            height=200,
            placeholder="# Paste your Python code here...",
            key="test_code_input"
        )

        if st.button("🧪 Run Tests on Code", type="primary"):
            if code.strip():
                with st.spinner("Running tests..."):
                    result = facility.run_all_tests(code=code)
                    st.session_state.latest_test_result = result
                    _display_quick_result(result)
            else:
                st.warning("Please enter some code to test.")

    elif test_type == "Test File":
        file_path = st.text_input(
            "File path to test:",
            placeholder="/path/to/file.py"
        )

        if st.button("🧪 Run Tests on File", type="primary"):
            if file_path.strip():
                with st.spinner("Running tests..."):
                    result = facility.run_all_tests(file_path=file_path)
                    st.session_state.latest_test_result = result
                    _display_quick_result(result)
            else:
                st.warning("Please enter a file path.")

    else:  # Test Project
        st.write(f"Testing project at: `{facility.project_path}`")

        if st.button("🧪 Run Full Project Tests", type="primary"):
            with st.spinner("Running full test suite..."):
                result = facility.run_all_tests()
                st.session_state.latest_test_result = result
                _display_quick_result(result)


def _display_quick_result(result: "TestSuiteResult") -> None:
    """Display quick summary of test results."""
    st.divider()

    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total", result.total_tests)
    col2.metric("Passed", result.passed)
    col3.metric("Failed", result.failed)
    col4.metric("Warnings", result.warnings)
    col5.metric("Duration", f"{result.duration:.2f}s")

    # Overall status
    if result.all_passed:
        st.success("✅ All tests passed!")
    else:
        st.error(f"❌ {result.failed} tests failed")

    # Quick view of failures
    if not result.all_passed:
        with st.expander("View Failures", expanded=True):
            for r in result.results:
                if r.status == TestStatus.FAILED:
                    st.error(f"**{r.name}** (Tier {r.tier.value}): {r.message}")
                    if r.details:
                        for detail in r.details[:3]:
                            st.code(detail)


def _render_results() -> None:
    """Render detailed test results section."""
    st.subheader("Test Results")

    if "latest_test_result" not in st.session_state:
        st.info("No test results yet. Run some tests to see results here.")
        return

    result = st.session_state.latest_test_result

    # Summary bar
    st.write("### Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Tests", result.total_tests)
    col2.metric("✅ Passed", result.passed)
    col3.metric("❌ Failed", result.failed)
    col4.metric("⚠️ Warnings", result.warnings)
    col5.metric("⏱️ Duration", f"{result.duration:.2f}s")

    # Status indicator
    if result.all_passed:
        st.success("✅ All tests passed!")
    else:
        st.error(f"❌ {result.failed} tests failed")

    # Detailed results by tier
    st.write("### Results by Tier")

    for tier_num in range(1, 8):
        tier_info = TIER_INFO.get(tier_num, {})
        tier_results = [r for r in result.results if r.tier.value == tier_num]

        if not tier_results:
            continue

        # Determine tier status
        tier_passed = all(r.status in [TestStatus.PASSED, TestStatus.SKIPPED, TestStatus.WARNING]
                         for r in tier_results)
        tier_icon = "✅" if tier_passed else "❌"

        with st.expander(
            f"{tier_icon} Tier {tier_num}: {tier_info.get('name', 'Unknown')}",
            expanded=not tier_passed
        ):
            for r in tier_results:
                status_icons = {
                    TestStatus.PASSED: "✅",
                    TestStatus.FAILED: "❌",
                    TestStatus.WARNING: "⚠️",
                    TestStatus.SKIPPED: "⏭️",
                    TestStatus.ERROR: "💥"
                }
                icon = status_icons.get(r.status, "❓")

                st.write(f"{icon} **{r.name}** - {r.message} ({r.duration:.2f}s)")

                if r.details:
                    with st.container():
                        for detail in r.details:
                            st.code(detail)

                if r.line_number:
                    st.caption(f"Line: {r.line_number}")

    # Failure summary
    if not result.all_passed:
        st.write("### Failure Summary")
        if hasattr(st.session_state, 'testing_facility'):
            summary = st.session_state.testing_facility.get_failure_summary(result)
            st.markdown(summary)


def _render_loop_controls(facility: "TestingFacility") -> None:
    """Render Build-Test Loop controls."""
    st.subheader("Build-Test Loop")

    st.info("""
    The Build-Test Loop automatically:
    1. Takes code from the builder
    2. Runs tests
    3. If tests fail, sends failures back for fixes
    4. Repeats until all tests pass or max iterations reached
    """)

    col1, col2 = st.columns(2)

    with col1:
        max_iterations = st.slider(
            "Max Fix Iterations",
            min_value=1,
            max_value=10,
            value=5,
            key="loop_max_iterations"
        )

        stop_on_first = st.checkbox(
            "Stop on first failure per iteration",
            value=False,
            key="loop_stop_first"
        )

    with col2:
        st.write("**Loop Settings:**")
        st.write(f"- Max iterations: {max_iterations}")
        st.write(f"- Stop on first: {'Yes' if stop_on_first else 'No'}")
        st.write(f"- Enabled tiers: {facility.enabled_tiers}")

    st.divider()

    # Manual loop test
    st.write("### Test Code with Loop")

    code_input = st.text_area(
        "Enter code to test in loop:",
        height=150,
        key="loop_code_input",
        placeholder="# Enter Python code..."
    )

    if st.button("🔄 Run Test Loop", type="primary"):
        if not code_input.strip():
            st.warning("Please enter code to test.")
        else:
            loop = BuildTestLoop(
                testing_facility=facility,
                max_iterations=max_iterations,
                stop_on_first_failure=stop_on_first
            )

            with st.spinner("Running test loop..."):
                result = loop.run_loop(initial_code=code_input)

            st.session_state.latest_loop_result = result
            _display_loop_result(result)

    # Show previous loop results
    if "latest_loop_result" in st.session_state:
        st.divider()
        st.write("### Previous Loop Result")
        _display_loop_result(st.session_state.latest_loop_result)


def _display_loop_result(result: "LoopResult") -> None:
    """Display loop execution result."""
    # Status
    status_display = {
        LoopStatus.PASSED: ("✅ Passed", "success"),
        LoopStatus.FAILED: ("❌ Failed", "error"),
        LoopStatus.MAX_ITERATIONS: ("⚠️ Max Iterations", "warning"),
        LoopStatus.ERROR: ("💥 Error", "error"),
        LoopStatus.PENDING: ("⏳ Pending", "info"),
        LoopStatus.RUNNING: ("🔄 Running", "info"),
    }

    status_text, status_type = status_display.get(result.status, ("Unknown", "info"))

    if status_type == "success":
        st.success(f"{status_text}: {result.message}")
    elif status_type == "error":
        st.error(f"{status_text}: {result.message}")
    elif status_type == "warning":
        st.warning(f"{status_text}: {result.message}")
    else:
        st.info(f"{status_text}: {result.message}")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Iterations", result.iterations)
    col2.metric("Duration", f"{result.total_duration:.2f}s")
    col3.metric("Success", "Yes" if result.success else "No")

    # History
    if result.history:
        with st.expander("Iteration History"):
            for entry in result.history:
                phase_icon = "🔨" if entry.phase == "build" else "🧪"
                status_icon = "✅" if entry.success else "❌"
                st.write(f"{phase_icon} Iteration {entry.iteration} ({entry.phase}): {status_icon}")

                if hasattr(entry, 'test_result') and entry.test_result:
                    st.caption(f"Tests: {entry.test_result.passed} passed, {entry.test_result.failed} failed")

    # Remaining failures
    if result.remaining_failures:
        with st.expander("Remaining Failures", expanded=True):
            st.markdown(result.remaining_failures)


def render_compact_testing_status(facility: Optional["TestingFacility"] = None) -> None:
    """
    Render a compact testing status indicator.

    Args:
        facility: Optional TestingFacility instance
    """
    if not TESTING_AVAILABLE:
        st.caption("🧪 Testing: Not available")
        return

    if facility is None:
        if "testing_facility" in st.session_state:
            facility = st.session_state.testing_facility
        else:
            st.caption("🧪 Testing: Not configured")
            return

    # Get latest result if any
    if facility.results_history:
        latest = facility.results_history[-1]
        if latest.all_passed:
            st.caption(f"🧪 Last run: ✅ All {latest.passed} tests passed")
        else:
            st.caption(f"🧪 Last run: ❌ {latest.failed}/{latest.total_tests} failed")
    else:
        enabled_count = len(facility.enabled_tiers)
        st.caption(f"🧪 Testing: {enabled_count} tiers enabled")


def render_tier_status_badges(result: Optional["TestSuiteResult"] = None) -> None:
    """
    Render status badges for each test tier.

    Args:
        result: Optional test result to show status from
    """
    if not TESTING_AVAILABLE:
        return

    if result is None:
        # Just show tier names
        cols = st.columns(7)
        for i, col in enumerate(cols, 1):
            tier_info = TIER_INFO.get(i, {})
            col.caption(f"{tier_info.get('icon', '🔷')} T{i}")
        return

    # Show actual status
    tier_status = {}
    for r in result.results:
        tier_num = r.tier.value
        if tier_num not in tier_status:
            tier_status[tier_num] = r.status
        elif r.status == TestStatus.FAILED:
            tier_status[tier_num] = TestStatus.FAILED

    cols = st.columns(7)
    for i, col in enumerate(cols, 1):
        tier_info = TIER_INFO.get(i, {})
        status = tier_status.get(i)
        if status == TestStatus.PASSED:
            col.success(f"T{i} ✅")
        elif status == TestStatus.FAILED:
            col.error(f"T{i} ❌")
        elif status == TestStatus.WARNING:
            col.warning(f"T{i} ⚠️")
        elif status == TestStatus.SKIPPED:
            col.info(f"T{i} ⏭️")
        else:
            col.caption(f"T{i} ◯")
