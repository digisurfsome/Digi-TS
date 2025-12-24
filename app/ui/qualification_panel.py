"""
Agent Qualification UI Panel.

Provides interface for:
- Running LIMB qualification tests
- Viewing test results and history
- Editing pipeline settings and prompts
- Managing auto-chain workflow
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.models import (
    Project,
    AgentQualification,
    QualificationStatus,
)
from app.services.agent_qualification_service import (
    AgentQualificationService,
    QualificationResult,
    PhaseStatus,
    SCORE_PASS,
    SCORE_CONCERN,
    SCORE_FAIL,
    FAKE_TECH_VARIANTS,
    CONTRADICTION_VARIANTS,
)
from app.services.pipeline_settings_service import (
    get_pipeline_setting_with_default,
    set_pipeline_setting,
    get_toggle,
    set_toggle,
    DEFAULT_CODEBASE_EXPLORATION_PROMPT,
    DEFAULT_AGENT_OS_BLUEPRINT_PROMPT,
    DEFAULT_PHASE_BREAKDOWN_PROMPT,
    DEFAULT_PHASE_TEST_PROMPT,
    DEFAULT_INTEGRATION_TEST_PROMPT,
)
from app.services import get_setting
from app.ui.layout import show_success, show_error, show_warning, show_info


def get_status_badge(status: QualificationStatus) -> str:
    """Get colored badge for qualification status."""
    badges = {
        QualificationStatus.PENDING: "🟡 Pending",
        QualificationStatus.GO: "✅ GO",
        QualificationStatus.GO_WITH_CHECKS: "✅ GO+CHECKS",
        QualificationStatus.SIMPLE_ONLY: "⚠️ Simple Only",
        QualificationStatus.SKIP: "❌ Skip",
        QualificationStatus.CRITICAL_FAIL: "🚫 Critical Fail",
    }
    return badges.get(status, "❓ Unknown")


def get_phase_badge(status: str) -> str:
    """Get badge for phase status."""
    badges = {
        "PASS": "✅",
        "CONCERN": "⚠️",
        "FAIL": "❌",
    }
    return badges.get(status, "❓")


def render_qualification_panel(
    db: Session,
    user_id: int,
    project_id: Optional[int] = None
):
    """
    Render the agent qualification panel.

    Args:
        db: Database session
        user_id: Current user ID
        project_id: Optional project ID
    """
    st.markdown("### 🧪 Agent Qualification (LIMB Test)")

    # Get API key for potential AI evaluation
    openai_key = get_setting(db, "OPENAI_API_KEY")

    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Run Test", "History", "Settings"])

    with tab1:
        render_run_test_section(db, user_id, project_id, openai_key)

    with tab2:
        render_history_section(db, user_id, project_id)

    with tab3:
        render_settings_section(db, user_id, project_id)


def render_run_test_section(
    db: Session,
    user_id: int,
    project_id: Optional[int],
    openai_key: Optional[str]
):
    """Render the test execution section."""
    st.markdown("#### Generate & Run Qualification Test")

    # Initialize service
    service = AgentQualificationService(
        db=db,
        openai_key=openai_key,
        use_ai_evaluation=False  # Default to local evaluation
    )

    # Session state for test
    if "qual_test_prompt" not in st.session_state:
        st.session_state.qual_test_prompt = None
    if "qual_test_metadata" not in st.session_state:
        st.session_state.qual_test_metadata = None
    if "qual_test_result" not in st.session_state:
        st.session_state.qual_test_result = None

    col1, col2 = st.columns([3, 1])

    with col1:
        # Generate test button
        if st.button("🎲 Generate New Test", type="primary", use_container_width=True):
            test_prompt, metadata = service.generate_test()
            st.session_state.qual_test_prompt = test_prompt
            st.session_state.qual_test_metadata = metadata
            st.session_state.qual_test_result = None
            st.rerun()

    with col2:
        # Show which variant is being used
        if st.session_state.qual_test_metadata:
            fake_tech = st.session_state.qual_test_metadata.get("fake_tech", "")
            st.caption(f"Tech: {fake_tech[:20]}...")

    # Display the test prompt
    if st.session_state.qual_test_prompt:
        with st.expander("📋 Test Prompt", expanded=True):
            st.code(st.session_state.qual_test_prompt, language="markdown")

            # Copy button
            if st.button("📋 Copy to Clipboard"):
                st.toast("Copied! Paste into your AI chat.")

        st.divider()

        # Agent response input
        st.markdown("#### Paste Agent Response")
        agent_response = st.text_area(
            "Agent's Response",
            height=300,
            placeholder="Paste the agent's complete response here...",
            key="agent_response_input"
        )

        # Evaluation options
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            use_ai_eval = st.checkbox(
                "Use AI Evaluation",
                value=False,
                help="Use OpenAI to evaluate (more accurate but requires API key)"
            )

        with col2:
            if st.button("🔍 Evaluate Response", type="primary", disabled=not agent_response):
                if agent_response:
                    service.use_ai_evaluation = use_ai_eval and openai_key

                    result = service.evaluate(
                        agent_response,
                        st.session_state.qual_test_metadata,
                        st.session_state.qual_test_prompt
                    )
                    st.session_state.qual_test_result = result

                    # Save to database
                    if project_id:
                        save_qualification_result(
                            db, user_id, project_id,
                            st.session_state.qual_test_prompt,
                            st.session_state.qual_test_metadata,
                            agent_response,
                            result
                        )

                    st.rerun()

        # Display results
        if st.session_state.qual_test_result:
            render_test_results(st.session_state.qual_test_result, service)


def render_test_results(result: Dict[str, Any], service: AgentQualificationService):
    """Render the test results."""
    st.divider()
    st.markdown("### 📊 Evaluation Results")

    # Overall result
    badge = service.get_result_badge(result)
    color = service.get_result_color(result)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Result", badge)

    with col2:
        st.metric("Score", f"{result.get('total_score', 0)}/7")

    with col3:
        st.metric("Passes", result.get("passes", 0))

    with col4:
        if result.get("critical_fail"):
            st.error("⚠️ CRITICAL")
        else:
            st.metric("Fails", result.get("fails", 0))

    # Task breakdown
    st.markdown("#### Task Breakdown")

    tasks = result.get("task_results", [])
    if tasks:
        for task in tasks:
            task_num = task.get("task")
            status = task.get("status", "UNKNOWN")
            reason = task.get("reason", "")

            badge = get_phase_badge(status)
            critical = " (CRITICAL)" if task.get("critical") else ""

            with st.expander(f"{badge} Task {task_num}: {status}{critical}"):
                st.write(reason)
    else:
        st.info("No detailed task breakdown available")

    # Summary
    if result.get("summary"):
        st.markdown("#### Summary")
        st.info(result["summary"])


def save_qualification_result(
    db: Session,
    user_id: int,
    project_id: int,
    test_prompt: str,
    metadata: Dict[str, Any],
    response: str,
    result: Dict[str, Any]
) -> AgentQualification:
    """Save qualification result to database."""
    from app.core.models import AgentQualification, QualificationStatus

    # Map result to status
    result_type = result.get("result")
    status_map = {
        QualificationResult.GO: QualificationStatus.GO,
        QualificationResult.GO_WITH_CHECKS: QualificationStatus.GO_WITH_CHECKS,
        QualificationResult.SIMPLE_ONLY: QualificationStatus.SIMPLE_ONLY,
        QualificationResult.SKIP: QualificationStatus.SKIP,
        QualificationResult.CRITICAL_FAIL: QualificationStatus.CRITICAL_FAIL,
    }
    status = status_map.get(result_type, QualificationStatus.PENDING)

    qualification = AgentQualification(
        project_id=project_id,
        user_id=user_id,
        agent_type="manual_test",
        test_prompt=test_prompt,
        test_metadata=metadata,
        agent_response=response,
        status=status,
        total_score=result.get("total_score"),
        passes=result.get("passes"),
        concerns=result.get("concerns", 0),
        fails=result.get("fails"),
        critical_fail=result.get("critical_fail", False),
        task_results=result.get("task_results"),
        evaluation_summary=result.get("summary"),
        evaluated_at=datetime.utcnow(),
    )

    db.add(qualification)
    db.commit()
    db.refresh(qualification)

    return qualification


def render_history_section(
    db: Session,
    user_id: int,
    project_id: Optional[int]
):
    """Render qualification history."""
    st.markdown("#### Qualification History")

    # Query history
    query = db.query(AgentQualification).filter(
        AgentQualification.user_id == user_id
    )
    if project_id:
        query = query.filter(AgentQualification.project_id == project_id)

    qualifications = query.order_by(AgentQualification.created_at.desc()).limit(20).all()

    if not qualifications:
        st.info("No qualification tests run yet.")
        return

    # Display as table
    for qual in qualifications:
        status_badge = get_status_badge(qual.status)
        date_str = qual.created_at.strftime("%Y-%m-%d %H:%M")

        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            st.write(f"**{date_str}**")

        with col2:
            st.write(status_badge)

        with col3:
            st.write(f"Score: {qual.total_score or '-'}")

        with col4:
            if st.button("👁️", key=f"view_qual_{qual.id}"):
                st.session_state[f"show_qual_{qual.id}"] = not st.session_state.get(f"show_qual_{qual.id}", False)

        # Expandable details
        if st.session_state.get(f"show_qual_{qual.id}"):
            with st.expander("Details", expanded=True):
                st.write(f"**Agent Type:** {qual.agent_type}")
                st.write(f"**Attempt:** #{qual.attempt_number}")
                if qual.critical_fail:
                    st.error("⚠️ Critical failure detected")
                if qual.evaluation_summary:
                    st.markdown(f"**Summary:** {qual.evaluation_summary}")


def render_settings_section(
    db: Session,
    user_id: int,
    project_id: Optional[int]
):
    """Render pipeline settings editor."""
    st.markdown("#### Pipeline Settings")

    # Toggles section
    st.markdown("##### Workflow Toggles")

    col1, col2, col3 = st.columns(3)

    with col1:
        pause_after_os = st.checkbox(
            "Pause after Agent OS",
            value=get_toggle(db, user_id, "pause_after_agent_os", project_id),
            help="Pause for review after Agent OS blueprint is created"
        )

    with col2:
        pause_after_phases = st.checkbox(
            "Pause after Phases",
            value=get_toggle(db, user_id, "pause_after_phases", project_id),
            help="Pause for review after phase breakdown is created"
        )

    with col3:
        pause_before_build = st.checkbox(
            "Pause before Build",
            value=get_toggle(db, user_id, "pause_before_build", project_id),
            help="Pause for confirmation before starting build"
        )

    col1, col2 = st.columns(2)

    with col1:
        auto_retry = st.checkbox(
            "Auto-retry on Fail",
            value=get_toggle(db, user_id, "auto_retry_on_fail", project_id),
            help="Automatically spawn new agent and retry if qualification fails"
        )

    with col2:
        max_retries = st.number_input(
            "Max Retry Attempts",
            min_value=1,
            max_value=10,
            value=int(get_pipeline_setting_with_default(db, user_id, "max_retry_attempts", project_id) or "3"),
            help="Maximum number of retry attempts"
        )

    # Save toggles
    if st.button("💾 Save Toggles", key="save_toggles"):
        set_toggle(db, user_id, "pause_after_agent_os", pause_after_os, project_id)
        set_toggle(db, user_id, "pause_after_phases", pause_after_phases, project_id)
        set_toggle(db, user_id, "pause_before_build", pause_before_build, project_id)
        set_toggle(db, user_id, "auto_retry_on_fail", auto_retry, project_id)
        set_pipeline_setting(db, user_id, "max_retry_attempts", str(max_retries), project_id)
        show_success("Toggles saved!")

    st.divider()

    # Prompts editor
    st.markdown("##### Editable Prompts")

    prompt_tabs = st.tabs([
        "Codebase Exploration",
        "Agent OS Blueprint",
        "Phase Breakdown",
        "Phase Test",
        "Integration Test"
    ])

    prompts = [
        ("codebase_exploration_prompt", DEFAULT_CODEBASE_EXPLORATION_PROMPT, "Codebase Exploration"),
        ("agent_os_blueprint_prompt", DEFAULT_AGENT_OS_BLUEPRINT_PROMPT, "Agent OS Blueprint"),
        ("phase_breakdown_prompt", DEFAULT_PHASE_BREAKDOWN_PROMPT, "Phase Breakdown"),
        ("phase_test_prompt", DEFAULT_PHASE_TEST_PROMPT, "Phase Test"),
        ("integration_test_prompt", DEFAULT_INTEGRATION_TEST_PROMPT, "Integration Test"),
    ]

    for i, (key, default, label) in enumerate(prompts):
        with prompt_tabs[i]:
            current_value = get_pipeline_setting_with_default(db, user_id, key, project_id)

            new_value = st.text_area(
                f"{label} Prompt",
                value=current_value,
                height=200,
                key=f"prompt_{key}"
            )

            col1, col2 = st.columns([1, 3])

            with col1:
                if st.button("💾 Save", key=f"save_{key}"):
                    set_pipeline_setting(db, user_id, key, new_value, project_id)
                    show_success(f"{label} prompt saved!")

            with col2:
                if st.button("↩️ Reset to Default", key=f"reset_{key}"):
                    set_pipeline_setting(db, user_id, key, default, project_id)
                    show_info(f"{label} prompt reset to default")
                    st.rerun()


def render_qualification_status_badge(
    db: Session,
    user_id: int,
    project_id: int,
    agent_session_id: Optional[str] = None
) -> Optional[AgentQualification]:
    """
    Render a compact qualification status badge.

    Returns the latest qualification if found.
    """
    # Get latest qualification for this project
    query = db.query(AgentQualification).filter(
        AgentQualification.user_id == user_id,
        AgentQualification.project_id == project_id
    )

    if agent_session_id:
        query = query.filter(AgentQualification.agent_session_id == agent_session_id)

    qual = query.order_by(AgentQualification.created_at.desc()).first()

    if qual:
        badge = get_status_badge(qual.status)
        st.markdown(f"**Qualification:** {badge}")
        return qual
    else:
        st.markdown("**Qualification:** ⚪ Not tested")
        return None


def render_auto_qualify_button(
    db: Session,
    user_id: int,
    project_id: int,
    agent_type: str = "roundtable",
    on_qualify_callback: Optional[callable] = None
):
    """
    Render button to trigger auto-qualification workflow.

    This is meant to be embedded in other panels (like Roundtable).
    """
    if st.button("🧪 Run Qualification", help="Run LIMB test on this agent"):
        # Generate test
        service = AgentQualificationService(db=db)
        test_prompt, metadata = service.generate_test()

        # Store in session for later evaluation
        st.session_state.pending_qualification = {
            "test_prompt": test_prompt,
            "metadata": metadata,
            "user_id": user_id,
            "project_id": project_id,
            "agent_type": agent_type,
        }

        # Show the test prompt
        st.info("Send this test to the agent:")
        st.code(test_prompt, language="markdown")

        if on_qualify_callback:
            on_qualify_callback(test_prompt, metadata)

        return test_prompt, metadata

    return None, None
