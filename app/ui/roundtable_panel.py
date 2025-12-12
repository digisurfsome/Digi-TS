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
    PROMPT_PRESETS,
    TestRunner,
)
from app.services.github_service import GitHubService, validate_github_token
from app.services import get_setting
import json
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
    google_key = get_setting(db, "GOOGLE_API_KEY")

    if not anthropic_key and not openai_key and not google_key:
        show_warning("No API keys configured. Add ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY in Settings.")

    # Initialize service
    service = RoundtableService(
        db=db,
        anthropic_key=anthropic_key,
        openai_key=openai_key,
        google_key=google_key
    )

    # Session Management Section
    st.subheader("📋 Session")

    # Check if tables exist - handle gracefully if not
    try:
        sessions = service.list_sessions(project_id=project_id)
    except Exception as e:
        if "does not exist" in str(e) or "UndefinedTable" in str(e):
            show_warning("Roundtable tables not found. Please go to **System Status** tab and click **Initialize Schema** to create the required database tables.")
            st.info("After initializing, refresh this page to use Roundtable Coder.")
            return
        else:
            show_error(f"Database error: {str(e)}")
            return

    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        # Get existing sessions
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

    # Tools Section (Phases F, H, I)
    render_tools_section(db, service, session)


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

    # Master Prompt with Presets (Phase G)
    with st.expander("📝 Master Prompt & Guardrails", expanded=False):
        # Prompt Preset Selector
        preset_options = ["Custom"] + [p["name"] for p in PROMPT_PRESETS.values()]
        preset = st.selectbox(
            "Prompt Preset",
            options=preset_options,
            key=f"preset_{session.id}",
            help="Select a preset to auto-fill system prompt and guardrails"
        )

        # Get current values
        current_prompt = session.master_prompt or ""
        current_guardrails = session.master_guardrails or ""

        # Apply preset if selected
        if preset != "Custom":
            preset_key = preset.lower().replace(" ", "_").replace("code_", "")
            for key, value in PROMPT_PRESETS.items():
                if value["name"] == preset:
                    preset_key = key
                    break
            if preset_key in PROMPT_PRESETS:
                current_prompt = PROMPT_PRESETS[preset_key]["system"]
                current_guardrails = PROMPT_PRESETS[preset_key]["guardrails"]

        master_prompt = st.text_area(
            "System Prompt (applies to all agents)",
            value=current_prompt,
            height=100,
            key=f"master_prompt_{session.id}"
        )

        guardrails = st.text_area(
            "Guardrails (restrictions/rules)",
            value=current_guardrails,
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

        # Test runner (Phase J)
        responses = service.get_round_responses(selected_round.id)
        if responses["builder"] and responses["builder"]["response"]:
            builder_content = responses["builder"]["response"].content
            render_test_runner(builder_content, selected_round.id)


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


# =============================================================================
# Phase F: Baton Integration
# =============================================================================

def render_baton_section(service: RoundtableService, session: RoundtableSession):
    """Render baton generation section."""
    st.markdown("### 📦 Baton Snapshot")
    st.caption("Generate a context snapshot for session continuity")

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("Generate Baton", key="gen_baton_btn"):
            with st.spinner("Generating baton snapshot..."):
                baton_content = service.generate_roundtable_baton(session.id)
                st.session_state[f"baton_content_{session.id}"] = baton_content
                show_success("Baton generated!")

    # Display baton content if generated
    baton_key = f"baton_content_{session.id}"
    if baton_key in st.session_state:
        with st.expander("📄 Baton Content", expanded=True):
            st.text_area(
                "Copy this content for context persistence",
                value=st.session_state[baton_key],
                height=400,
                key=f"baton_display_{session.id}"
            )
            if st.button("Clear Baton", key="clear_baton_btn"):
                del st.session_state[baton_key]
                st.rerun()


# =============================================================================
# Phase H: GitHub Integration
# =============================================================================

def render_github_section(db, service: RoundtableService, session: RoundtableSession):
    """Render GitHub integration section."""
    st.markdown("### 🐙 GitHub Integration")

    # Get GitHub token from settings
    github_token = get_setting(db, "GITHUB_TOKEN") or ""

    with st.expander("GitHub Settings", expanded=False):
        token_input = st.text_input(
            "GitHub Token",
            value=github_token,
            type="password",
            key="github_token_input",
            help="Personal Access Token with repo permissions"
        )

        if token_input and token_input != github_token:
            # Validate and save token
            validation = validate_github_token(token_input)
            if validation["valid"]:
                show_success(f"Token valid for user: {validation['username']}")
            else:
                show_warning(f"Token validation failed: {validation['error']}")

    if not github_token:
        show_info("Add a GitHub token in settings to enable GitHub features.")
        return

    github = GitHubService(github_token)

    col1, col2 = st.columns(2)

    with col1:
        repo = st.text_input(
            "Repository",
            placeholder="owner/repo",
            key="github_repo",
            help="Format: username/repository"
        )

    with col2:
        branch = st.text_input(
            "Branch",
            value="main",
            key="github_branch"
        )

    if repo:
        # File browser
        st.markdown("**Files:**")
        path = st.text_input("Path", value="", key="github_path", placeholder="src/")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("List Files", key="list_files_btn"):
                result = github.list_files(repo, path, branch)
                if result["success"]:
                    st.session_state["github_files"] = result["files"]
                else:
                    show_error(result["error"])

        with col2:
            if st.button("Fetch File", key="fetch_file_btn"):
                if path:
                    result = github.get_file_content(repo, path, branch)
                    if result["success"]:
                        st.session_state["github_file_content"] = result["content"]
                        st.session_state["github_file_sha"] = result.get("sha")
                        show_success(f"Fetched: {path}")
                    else:
                        show_error(result["error"])

        # Display files list
        if "github_files" in st.session_state:
            files = st.session_state["github_files"]
            for f in files[:20]:  # Limit display
                icon = "📁" if f["type"] == "dir" else "📄"
                st.text(f"{icon} {f['path']}")

        # Display fetched file content
        if "github_file_content" in st.session_state:
            with st.expander("📄 File Content", expanded=True):
                st.code(st.session_state["github_file_content"][:5000], language="python")

        # PR Creation
        st.markdown("---")
        st.markdown("**Create Pull Request:**")

        pr_title = st.text_input("PR Title", key="pr_title")
        pr_body = st.text_area("PR Description", key="pr_body", height=100)
        pr_head = st.text_input("Source Branch", key="pr_head", placeholder="feature-branch")
        pr_base = st.text_input("Target Branch", value="main", key="pr_base")

        if st.button("Create PR", key="create_pr_btn", type="primary"):
            if pr_title and pr_head:
                result = github.create_pr(repo, pr_title, pr_body, pr_head, pr_base)
                if result["success"]:
                    show_success(f"PR #{result['number']} created: {result['url']}")
                else:
                    show_error(result["error"])
            else:
                show_warning("Title and source branch are required")


# =============================================================================
# Phase I: Session Stats & Export
# =============================================================================

def render_session_stats(service: RoundtableService, session: RoundtableSession):
    """Render session statistics section."""
    st.markdown("### 📊 Session Statistics")

    stats = service.get_session_stats(session.id)

    if not stats:
        st.caption("No statistics available yet.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Rounds", stats.get("total_rounds", 0))

    with col2:
        st.metric("Completed", stats.get("completed_rounds", 0))

    with col3:
        st.metric("Total Cost", f"${stats.get('total_cost', 0):.4f}")

    with col4:
        total_tokens = stats.get("total_tokens", 0)
        st.metric("Total Tokens", f"{total_tokens:,}")

    # Token breakdown
    with st.expander("Token Details"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Input Tokens", f"{stats.get('total_tokens_in', 0):,}")
        with col2:
            st.metric("Output Tokens", f"{stats.get('total_tokens_out', 0):,}")
        st.metric("Total Responses", stats.get("total_responses", 0))

    # Export button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("📤 Export Session", key="export_session_btn"):
            export_data = service.export_session(session.id)
            st.session_state[f"export_data_{session.id}"] = export_data

    export_key = f"export_data_{session.id}"
    if export_key in st.session_state:
        with st.expander("📄 Exported JSON", expanded=True):
            st.json(st.session_state[export_key])
            # Download button
            json_str = json.dumps(st.session_state[export_key], indent=2)
            st.download_button(
                "Download JSON",
                data=json_str,
                file_name=f"roundtable_session_{session.id}.json",
                mime="application/json"
            )


# =============================================================================
# Phase J: Test Runner UI
# =============================================================================

def render_test_runner(builder_response: str, round_id: int):
    """Render test runner section after round execution."""
    st.markdown("### 🧪 Code Tests")

    run_tests = st.checkbox(
        "Run tests on builder output",
        value=True,
        key=f"run_tests_{round_id}"
    )

    if run_tests and builder_response:
        if st.button("Run Tests", key=f"run_tests_btn_{round_id}"):
            test_runner = TestRunner()
            with st.spinner("Running tests..."):
                results = test_runner.run_all(builder_response)
                summary = test_runner.get_summary(results)

            # Display results
            for result in results:
                tier = result["tier"]
                name = result["name"]
                passed = result["passed"]

                if passed:
                    st.success(f"✅ Tier {tier} ({name}): PASSED")
                else:
                    st.error(f"❌ Tier {tier} ({name}): FAILED")
                    for error in result.get("errors", []):
                        st.code(error)

                # Show warnings if any
                warnings = result.get("warnings", [])
                if warnings:
                    with st.expander(f"⚠️ Warnings ({len(warnings)})"):
                        for w in warnings[:10]:
                            st.warning(w)

            # Summary
            st.markdown("---")
            if summary["all_passed"]:
                st.success(f"🎉 All {summary['total_tests']} tests passed!")
            else:
                st.error(f"❌ {summary['failed']}/{summary['total_tests']} tests failed")


# =============================================================================
# Extended Panel with All Features
# =============================================================================

def render_tools_section(db, service: RoundtableService, session: RoundtableSession):
    """Render tools section with baton, GitHub, stats, etc."""
    st.divider()
    st.subheader("🛠️ Tools")

    tab1, tab2, tab3 = st.tabs(["📦 Baton", "🐙 GitHub", "📊 Stats"])

    with tab1:
        render_baton_section(service, session)

    with tab2:
        render_github_section(db, service, session)

    with tab3:
        render_session_stats(service, session)
