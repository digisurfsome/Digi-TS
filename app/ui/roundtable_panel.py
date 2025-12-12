"""
Roundtable Coder UI Panel.

Provides the user interface for creating sessions, managing rounds and agents,
and executing roundtable coding sessions.
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional

from app.core.models import (
    RoundtableSession,
    RoundtableRound,
    RoundtableAgent,
    RoundtableSessionStatus,
    AgentRole,
)
from app.services.roundtable_service import (
    RoundtableService,
    AVAILABLE_MODELS,
    AGENT_ROLES,
)
from app.services import get_setting
from app.ui.layout import show_success, show_error, show_warning, show_info


def get_status_badge(status: RoundtableSessionStatus) -> str:
    """Get a colored badge for session status."""
    badges = {
        RoundtableSessionStatus.ACTIVE: "🟢 Active",
        RoundtableSessionStatus.PAUSED: "🟡 Paused",
        RoundtableSessionStatus.COMPLETED: "🔵 Completed",
    }
    return badges.get(status, "⚪ Unknown")


def get_role_badge(role: AgentRole) -> str:
    """Get a badge for agent role."""
    badges = {
        AgentRole.BUILDER: "🔨 Builder",
        AgentRole.VOTER: "🗳️ Voter",
        AgentRole.REVIEWER: "📝 Reviewer",
    }
    return badges.get(role, "❓ Unknown")


def render_roundtable_panel(db: Session, project_id: Optional[int] = None):
    """
    Render the main Roundtable Coder panel.

    Args:
        db: Database session
        project_id: Optional project ID to filter sessions
    """
    st.header("🔄 Roundtable Coder")
    st.caption("Multi-agent coding sessions with consensus-based validation")

    # Get API keys from settings
    anthropic_key = get_setting(db, "ANTHROPIC_API_KEY")
    openai_key = get_setting(db, "OPENAI_API_KEY")

    if not anthropic_key and not openai_key:
        show_warning("No API keys configured. Add ANTHROPIC_API_KEY or OPENAI_API_KEY in Settings.")

    # Initialize service
    service = RoundtableService(
        db=db,
        anthropic_key=anthropic_key,
        openai_key=openai_key
    )

    # Session Management Section
    st.subheader("📋 Session")

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        # Get existing sessions
        sessions = service.list_sessions(project_id=project_id)
        session_options = {s.name: s.id for s in sessions}
        session_options["+ New Session"] = None

        selected_name = st.selectbox(
            "Select Session",
            options=list(session_options.keys()),
            key="roundtable_session_selector"
        )

    # Handle new session creation
    if selected_name == "+ New Session":
        with st.form("new_session_form"):
            new_name = st.text_input("Session Name", value="New Roundtable Session")
            submitted = st.form_submit_button("Create Session", type="primary")

            if submitted and new_name:
                new_session = service.create_session(
                    name=new_name,
                    project_id=project_id
                )
                st.session_state.roundtable_session_selector = new_session.name
                show_success(f"Created session: {new_name}")
                st.rerun()
        return

    # Get selected session
    session_id = session_options.get(selected_name)
    if not session_id:
        show_info("Select a session or create a new one to get started.")
        return

    session = service.get_session(session_id)
    if not session:
        show_error("Session not found")
        return

    with col2:
        if st.button("🗑️ Delete", key="delete_session_btn"):
            service.delete_session(session_id)
            show_success("Session deleted")
            st.rerun()

    with col3:
        st.write(get_status_badge(session.status))

    # Session Settings
    st.divider()
    render_session_settings(service, session)

    # Rounds Section
    st.divider()
    render_rounds_section(service, session)

    # Execution Section
    st.divider()
    render_execution_section(service, session)


def render_session_settings(service: RoundtableService, session: RoundtableSession):
    """Render session settings section."""
    st.subheader("⚙️ Session Settings")

    col1, col2 = st.columns(2)

    with col1:
        # Execution Mode Toggle - IMPORTANT
        st.markdown("**Execution Mode**")
        mode = st.radio(
            "Select mode",
            options=["single", "multi"],
            index=0 if session.execution_mode == "single" else 1,
            key=f"exec_mode_{session.id}",
            horizontal=True,
            help="Single: Builder only. Multi: Builder + Voters with consensus."
        )

        if mode == "single":
            st.caption("🔹 Single Agent: Only the builder runs, no voting")
        else:
            st.caption("🔹 Multi-Agent: Builder runs, then voters review and vote")

        if mode != session.execution_mode:
            service.update_session(session.id, execution_mode=mode)
            st.rerun()

    with col2:
        # Voting Threshold Slider
        threshold = st.slider(
            "Voting Threshold",
            min_value=50,
            max_value=100,
            value=int(session.voting_threshold * 100),
            step=5,
            key=f"threshold_{session.id}",
            help="Percentage of approvals needed for consensus",
            disabled=(session.execution_mode == "single")
        )

        if threshold / 100 != session.voting_threshold:
            service.update_session(session.id, voting_threshold=threshold / 100)

        if session.execution_mode == "multi":
            st.caption(f"Requires {threshold}% approval to pass")

    # Master Prompt (collapsible)
    with st.expander("📝 Master Prompt & Guardrails"):
        master_prompt = st.text_area(
            "System Prompt (applies to all agents)",
            value=session.master_prompt or "",
            height=100,
            key=f"master_prompt_{session.id}"
        )

        guardrails = st.text_area(
            "Guardrails (restrictions/rules)",
            value=session.master_guardrails or "",
            height=80,
            key=f"guardrails_{session.id}",
            placeholder="e.g., Never use eval(), always validate inputs..."
        )

        if st.button("Save Prompts", key="save_prompts_btn"):
            service.update_session(
                session.id,
                master_prompt=master_prompt,
                master_guardrails=guardrails
            )
            show_success("Prompts saved")


def render_rounds_section(service: RoundtableService, session: RoundtableSession):
    """Render rounds management section."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("🔄 Rounds")

    with col2:
        if st.button("➕ Add Round", key="add_round_btn"):
            service.add_round(session.id)
            st.rerun()

    if not session.rounds:
        show_info("No rounds yet. Click 'Add Round' to create one.")
        return

    # Render each round as a card
    for round_obj in session.rounds:
        render_round_card(service, session, round_obj)


def render_round_card(
    service: RoundtableService,
    session: RoundtableSession,
    round_obj: RoundtableRound
):
    """Render a single round card."""
    status_emoji = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅"
    }.get(round_obj.status, "❓")

    with st.container():
        st.markdown(f"### {status_emoji} {round_obj.name}")

        col1, col2 = st.columns([4, 1])

        with col2:
            if st.button("🗑️", key=f"delete_round_{round_obj.id}", help="Delete round"):
                service.delete_round(round_obj.id)
                st.rerun()

        # Task Prompt
        task_prompt = st.text_area(
            "Task Prompt",
            value=round_obj.task_prompt or "",
            height=100,
            key=f"task_prompt_{round_obj.id}",
            placeholder="Describe what the builder should create..."
        )

        if task_prompt != (round_obj.task_prompt or ""):
            service.update_round(round_obj.id, task_prompt=task_prompt)

        # Agents Section
        render_agents_section(service, round_obj)

        st.divider()


def render_agents_section(service: RoundtableService, round_obj: RoundtableRound):
    """Render agents section within a round card."""
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Agents**")

    with col2:
        if st.button("➕ Agent", key=f"add_agent_{round_obj.id}"):
            # Add default builder agent
            default_model = list(AVAILABLE_MODELS.keys())[0]
            service.add_agent(round_obj.id, default_model, "builder")
            st.rerun()

    if not round_obj.agents:
        st.caption("No agents configured. Add at least one builder agent.")
        return

    # Render each agent
    for idx, agent in enumerate(round_obj.agents):
        render_agent_row(service, agent, idx + 1)


def render_agent_row(service: RoundtableService, agent: RoundtableAgent, index: int):
    """Render a single agent configuration row."""
    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])

    with col1:
        st.markdown(f"**{index}.**")

    with col2:
        # Model selector
        current_model = service.get_model_display_name(agent.model)
        model_options = list(AVAILABLE_MODELS.keys())

        try:
            current_idx = model_options.index(current_model)
        except ValueError:
            current_idx = 0

        selected_model = st.selectbox(
            "Model",
            options=model_options,
            index=current_idx,
            key=f"agent_model_{agent.id}",
            label_visibility="collapsed"
        )

        if selected_model != current_model:
            service.update_agent(agent.id, model_name=selected_model)
            st.rerun()

    with col3:
        # Role selector
        role_options = list(AGENT_ROLES.keys())
        current_role_idx = role_options.index(agent.role.value) if agent.role.value in role_options else 0

        selected_role = st.selectbox(
            "Role",
            options=role_options,
            index=current_role_idx,
            key=f"agent_role_{agent.id}",
            label_visibility="collapsed",
            format_func=lambda x: get_role_badge(AgentRole(x))
        )

        if selected_role != agent.role.value:
            service.update_agent(agent.id, role=selected_role)
            st.rerun()

    with col4:
        if st.button("❌", key=f"remove_agent_{agent.id}", help="Remove agent"):
            service.delete_agent(agent.id)
            st.rerun()


def render_execution_section(service: RoundtableService, session: RoundtableSession):
    """Render execution controls and results display."""
    st.subheader("▶️ Execution")

    if not session.rounds:
        show_info("Add at least one round before executing.")
        return

    # Round selector
    round_options = {r.name: r.id for r in session.rounds}
    selected_round_name = st.selectbox(
        "Select Round to Execute",
        options=list(round_options.keys()),
        key="exec_round_selector"
    )

    selected_round_id = round_options.get(selected_round_name)
    if not selected_round_id:
        return

    selected_round = service.get_round(selected_round_id)
    if not selected_round:
        return

    # Check for agents
    if not selected_round.agents:
        show_warning("This round has no agents configured.")
        return

    # Check for builder
    builders = [a for a in selected_round.agents if a.role == AgentRole.BUILDER]
    if not builders:
        show_warning("This round needs at least one Builder agent.")
        return

    # Execution buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        run_clicked = st.button(
            "▶️ Run Round",
            key="run_round_btn",
            type="primary",
            disabled=(selected_round.status == "running")
        )

    with col2:
        rerun_clicked = st.button(
            "🔄 Re-run",
            key="rerun_round_btn",
            disabled=(selected_round.status != "completed")
        )

    with col3:
        # Status display
        status_text = {
            "pending": "⏳ Ready to run",
            "running": "🔄 Running...",
            "completed": "✅ Completed"
        }.get(selected_round.status, "❓ Unknown")
        st.markdown(f"**Status:** {status_text}")

    # Handle execution
    if run_clicked or rerun_clicked:
        with st.spinner("Executing round..."):
            result = service.execute_round(selected_round_id)

            if result["success"]:
                show_success("Round executed successfully!")
            else:
                show_error(f"Execution failed: {result.get('error', 'Unknown error')}")

            st.rerun()

    # Display results if round is completed
    if selected_round.status == "completed":
        render_round_results(service, selected_round, session.execution_mode)


def render_round_results(
    service: RoundtableService,
    round_obj: RoundtableRound,
    execution_mode: str
):
    """Render results for a completed round."""
    st.markdown("### 📊 Results")

    # Get all responses for this round
    for agent in round_obj.agents:
        if not agent.responses:
            continue

        # Get latest response
        latest = agent.responses[-1] if agent.responses else None
        if not latest:
            continue

        model_name = service.get_model_display_name(agent.model)
        role_badge = get_role_badge(agent.role)

        # Vote badge for voters
        vote_badge = ""
        if agent.role == AgentRole.VOTER and latest.vote:
            vote_badges = {
                "approve": "👍 APPROVE",
                "reject": "👎 REJECT",
                "abstain": "🤷 ABSTAIN"
            }
            vote_badge = vote_badges.get(latest.vote.value, "")

        with st.expander(f"**{model_name}** - {role_badge} {vote_badge}", expanded=True):
            # Metrics row
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tokens", f"{latest.tokens_input + latest.tokens_output:,}")
            with col2:
                st.metric("Cost", f"${latest.cost:.4f}")
            with col3:
                st.metric("Time", f"{latest.duration_seconds:.1f}s")

            # Content
            st.markdown("**Response:**")
            st.code(latest.content, language="markdown")

            # Copy button
            if st.button("📋 Copy", key=f"copy_{latest.id}"):
                st.write("Content copied to clipboard!")  # Streamlit doesn't have clipboard API

    # Consensus display (multi-agent mode only)
    if execution_mode == "multi":
        consensus = service.calculate_consensus(round_obj.id)
        if consensus and consensus.get("total_voters", 0) > 0:
            st.markdown("### 🗳️ Consensus")

            col1, col2 = st.columns(2)

            with col1:
                approval_pct = consensus["percentage"] * 100
                threshold_pct = consensus["threshold"] * 100

                # Progress bar for approval percentage
                st.progress(consensus["percentage"])
                st.caption(
                    f"{consensus['approvals']}/{consensus['total_voters']} approved "
                    f"({approval_pct:.0f}% / {threshold_pct:.0f}% needed)"
                )

            with col2:
                if consensus["passed"]:
                    st.success("✅ CONSENSUS REACHED")
                else:
                    st.error("❌ CONSENSUS NOT REACHED")

            # Feedback from rejections
            if consensus.get("feedback"):
                with st.expander("📝 Rejection Feedback"):
                    for fb in consensus["feedback"]:
                        st.markdown(f"- {fb[:500]}...")
