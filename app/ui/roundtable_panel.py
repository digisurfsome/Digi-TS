"""
Roundtable Coder UI Panel.

Provides the user interface for creating sessions, managing rounds and agents,
and executing roundtable coding sessions.

Phase 2: Integrated with Memory System for context injection and auto-storage.
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
    MEMORY_SYSTEM_AVAILABLE,
)
from app.services.github_service import GitHubService, validate_github_token
from app.services import get_setting
import json
from app.ui.layout import show_success, show_error, show_warning, show_info, render_token_meter
from app.ui.qualification_panel import (
    render_qualification_status_badge,
    render_auto_qualify_button,
)
from app.services.agent_qualification_service import AgentQualificationService

# Memory System imports (Phase 2)
try:
    from app.services.rag_service import RAGService
    from app.services.context_assembler import ContextAssembler
except ImportError:
    RAGService = None
    ContextAssembler = None


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
    # Layout mode toggle - Compact vs Full
    layout_col, spacer_col = st.columns([1, 5])
    with layout_col:
        use_compact = st.toggle(
            "Compact UI",
            value=st.session_state.get("roundtable_compact_mode", False),
            key="roundtable_layout_toggle",
            help="Condensed layout with popover controls"
        )
        st.session_state.roundtable_compact_mode = use_compact

    # If compact mode, render compact UI and return
    if use_compact:
        from app.ui.roundtable_compact import render_roundtable_compact
        render_roundtable_compact(db, project_id)
        return

    import os

    # Get API keys from settings OR environment variables
    anthropic_key = get_setting(db, "ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = get_setting(db, "OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    google_key = get_setting(db, "GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

    # Initialize Memory System services (Phase 2)
    rag_service = None
    context_assembler = None
    if MEMORY_SYSTEM_AVAILABLE and RAGService and ContextAssembler:
        try:
            rag_service = RAGService()
            context_assembler = ContextAssembler(db=db, rag_service=rag_service)
        except Exception:
            pass

    # Initialize service with memory integration
    service = RoundtableService(
        db=db,
        anthropic_key=anthropic_key,
        openai_key=openai_key,
        google_key=google_key,
        rag_service=rag_service,
        context_assembler=context_assembler
    )

    # Check if tables exist - handle gracefully if not
    try:
        sessions = service.list_sessions(project_id=project_id)
    except Exception as e:
        if "does not exist" in str(e) or "UndefinedTable" in str(e):
            show_warning("Roundtable tables not found. Please go to **System Status** tab and click **Initialize Schema**.")
            return
        else:
            show_error(f"Database error: {str(e)}")
            return

    # Get existing sessions
    session_options = {s.name: s.id for s in sessions}
    session_options["+ New Session"] = None

    # Check if we need to pre-select a newly created session
    default_index = 0
    option_keys = list(session_options.keys())
    if "roundtable_new_session_name" in st.session_state:
        new_name = st.session_state.roundtable_new_session_name
        if new_name in option_keys:
            default_index = option_keys.index(new_name)
        del st.session_state.roundtable_new_session_name

    # Title row with token info and session selector
    title_col, token_col, warmup_col, session_col, delete_col, status_col = st.columns([1.5, 1.5, 0.8, 1.5, 0.4, 0.6])

    with title_col:
        st.markdown("### 🔄 Roundtable Coder")

    # Token Usage (Item 5) - inline display
    with token_col:
        # Get current chat session for token display
        chat_session_id = st.session_state.get("current_chat_session_id")
        if chat_session_id:
            from app.services import get_token_usage, get_all_settings
            settings = get_all_settings(db)
            max_tokens = int(settings.get("max_context_tokens", "128000"))
            token_usage = get_token_usage(db, chat_session_id)
            total_tokens = token_usage["total_tokens_used"]
            percent_used = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0

            # Color based on usage
            if percent_used < 50:
                color = "🟢"
            elif percent_used < 70:
                color = "🟡"
            elif percent_used < 90:
                color = "🟠"
            else:
                color = "🔴"

            st.markdown(f"**{color} Token Usage:** {total_tokens:,} / {max_tokens:,} ({percent_used:.1f}%)")

            # Token Details expander (Item 6)
            with st.expander("Token Details"):
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Prompt: {token_usage['total_prompt_tokens']:,}")
                with col2:
                    st.caption(f"Completion: {token_usage['total_completion_tokens']:,}")
        else:
            st.caption("No session")

    # Show warm-up checkbox (Item 7)
    with warmup_col:
        show_warmup = st.checkbox(
            "Show warm-up",
            value=st.session_state.get("show_warmup_messages", False),
            key="roundtable_show_warmup_checkbox",
            help="Show/hide warmup messages"
        )
        st.session_state.show_warmup_messages = show_warmup

    with session_col:
        selected_name = st.selectbox(
            "Session",
            options=option_keys,
            index=default_index,
            key="roundtable_session_selector",
            label_visibility="collapsed"
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
                st.session_state.roundtable_new_session_name = new_session.name
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

    with delete_col:
        if st.button("🗑️", key="delete_session_btn", help="Delete session"):
            service.delete_session(session_id)
            show_success("Session deleted")
            st.rerun()

    with status_col:
        st.markdown(get_status_badge(session.status))

    # Two-column layout: Session Settings + Tools side by side
    settings_col, tools_col = st.columns([2, 1])

    with settings_col:
        render_session_settings(service, session)

    with tools_col:
        render_tools_section(db, service, session)

    # Rounds and Execution in compact layout
    render_rounds_section(service, session)
    render_execution_section(service, session)


def render_session_settings(service: RoundtableService, session: RoundtableSession):
    """Render session settings section."""
    st.markdown("**⚙️ Settings**")

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
    """Render rounds management section - COMPACT."""
    # Single row: Rounds label + Add button + Round selector (if multiple)
    if not session.rounds:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**🔄 Rounds**")
        with col2:
            if st.button("➕ Add Round", key="add_round_btn", use_container_width=True):
                service.add_round(session.id)
                st.rerun()
        st.caption("No rounds yet. Click 'Add Round' to create one.")
        return

    # Compact header row with round info inline
    col1, col2, col3 = st.columns([1.5, 2.5, 1])

    with col1:
        st.markdown("**🔄 Rounds**")

    with col2:
        # If multiple rounds, show selector; otherwise just show the round name
        if len(session.rounds) > 1:
            round_names = [f"{r.name} {'✅' if r.status == 'completed' else '⏳'}" for r in session.rounds]
            selected_idx = st.selectbox(
                "Round", options=range(len(round_names)),
                format_func=lambda i: round_names[i],
                key="round_selector", label_visibility="collapsed"
            )
            round_obj = session.rounds[selected_idx]
        else:
            round_obj = session.rounds[0]
            status_emoji = "✅" if round_obj.status == "completed" else "⏳"
            st.markdown(f"**{status_emoji} {round_obj.name}**")

    with col3:
        if st.button("➕ Add", key="add_round_btn", use_container_width=True):
            service.add_round(session.id)
            st.rerun()

    # Render the selected/only round (compact)
    render_round_card_compact(service, session, round_obj)


def render_round_card_compact(
    service: RoundtableService,
    session: RoundtableSession,
    round_obj: RoundtableRound
):
    """Render a single round card - COMPACT version."""
    # Task Prompt with delete button inline
    col1, col2 = st.columns([6, 1])
    with col1:
        st.caption("Task Prompt")
    with col2:
        if st.button("🗑️", key=f"delete_round_{round_obj.id}", help="Delete round"):
            service.delete_round(round_obj.id)
            st.rerun()

    task_prompt = st.text_area(
        "Task Prompt",
        value=round_obj.task_prompt or "",
        height=70,
        key=f"task_prompt_{round_obj.id}",
        placeholder="Describe what the builder should create...",
        label_visibility="collapsed"
    )

    if task_prompt != (round_obj.task_prompt or ""):
        service.update_round(round_obj.id, task_prompt=task_prompt)

    # Agents Section - compact
    render_agents_section_compact(service, round_obj)


def render_agents_section_compact(service: RoundtableService, round_obj: RoundtableRound):
    """Render agents section - COMPACT version."""
    # Header row with Agents label and + button inline
    col1, col2 = st.columns([5, 1])

    with col1:
        st.caption(f"Agents ({len(round_obj.agents)})" if round_obj.agents else "Agents")

    with col2:
        if st.button("➕", key=f"add_agent_{round_obj.id}", help="Add agent"):
            default_model = list(AVAILABLE_MODELS.keys())[0]
            service.add_agent(round_obj.id, default_model, "builder")
            st.rerun()

    if not round_obj.agents:
        st.caption("Add at least one builder agent.")
        return

    # Render agents in a tighter grid
    for idx, agent in enumerate(round_obj.agents):
        render_agent_row_compact(service, agent, idx + 1)


def render_agents_section(service: RoundtableService, round_obj: RoundtableRound):
    """Render agents section within a round card - legacy."""
    render_agents_section_compact(service, round_obj)


def render_agent_row_compact(service: RoundtableService, agent: RoundtableAgent, index: int):
    """Render a single agent configuration row - COMPACT."""
    # Tighter columns: number, model, role, delete
    col1, col2, col3, col4 = st.columns([0.3, 2.5, 1.5, 0.4])

    with col1:
        st.caption(f"{index}.")

    with col2:
        current_model = service.get_model_display_name(agent.model)
        model_options = list(AVAILABLE_MODELS.keys())
        try:
            current_idx = model_options.index(current_model)
        except ValueError:
            current_idx = 0

        selected_model = st.selectbox(
            "Model", options=model_options, index=current_idx,
            key=f"agent_model_{agent.id}", label_visibility="collapsed"
        )
        if selected_model != current_model:
            service.update_agent(agent.id, model_name=selected_model)
            st.rerun()

    with col3:
        role_options = list(AGENT_ROLES.keys())
        current_role_idx = role_options.index(agent.role.value) if agent.role.value in role_options else 0
        selected_role = st.selectbox(
            "Role", options=role_options, index=current_role_idx,
            key=f"agent_role_{agent.id}", label_visibility="collapsed",
            format_func=lambda x: get_role_badge(AgentRole(x))
        )
        if selected_role != agent.role.value:
            service.update_agent(agent.id, role=selected_role)
            st.rerun()

    with col4:
        if st.button("✕", key=f"remove_agent_{agent.id}", help="Remove"):
            service.delete_agent(agent.id)
            st.rerun()


def render_agent_row(service: RoundtableService, agent: RoundtableAgent, index: int):
    """Render a single agent configuration row - legacy."""
    render_agent_row_compact(service, agent, index)


def render_execution_section(service: RoundtableService, session: RoundtableSession):
    """Render execution controls - COMPACT."""
    if not session.rounds:
        st.caption("▶️ Execution: Add a round first")
        return

    # All on one row: Label | Round selector | Run | Re-run | Status
    col1, col2, col3, col4, col5 = st.columns([0.8, 1.5, 0.8, 0.6, 1])

    with col1:
        st.caption("▶️ Execute")

    round_options = {r.name: r.id for r in session.rounds}
    with col2:
        selected_round_name = st.selectbox(
            "Round", options=list(round_options.keys()),
            key="exec_round_selector", label_visibility="collapsed"
        )

    selected_round_id = round_options.get(selected_round_name)
    if not selected_round_id:
        return

    selected_round = service.get_round(selected_round_id)
    if not selected_round:
        return

    # Check for builder
    builders = [a for a in selected_round.agents if a.role == AgentRole.BUILDER]
    has_builder = len(builders) > 0

    with col3:
        run_clicked = st.button(
            "▶️ Run", key="run_round_btn", type="primary",
            disabled=(selected_round.status == "running" or not has_builder)
        )

    with col4:
        rerun_clicked = st.button(
            "🔄", key="rerun_round_btn",
            disabled=(selected_round.status != "completed")
        )

    with col5:
        status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅"}.get(selected_round.status, "❓")
        st.caption(f"{status_emoji} {selected_round.status}")

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
    """Render results for a completed round - COMPACT."""
    st.caption("📊 Results")

    # Get all responses for this round
    for agent in round_obj.agents:
        if not agent.responses:
            continue

        latest = agent.responses[-1] if agent.responses else None
        if not latest:
            continue

        model_name = service.get_model_display_name(agent.model)
        role_badge = get_role_badge(agent.role)

        # Vote badge for voters
        vote_badge = ""
        if agent.role == AgentRole.VOTER and latest.vote:
            vote_badges = {"approve": "👍", "reject": "👎", "abstain": "🤷"}
            vote_badge = vote_badges.get(latest.vote.value, "")

        # Compact header with inline metrics
        tokens = latest.tokens_input + latest.tokens_output
        header = f"**{model_name}** {role_badge} {vote_badge} | {tokens:,} tok | ${latest.cost:.4f} | {latest.duration_seconds:.1f}s"

        with st.expander(header, expanded=True):
            st.code(latest.content, language="markdown")
            if st.button("📋 Copy", key=f"copy_{latest.id}"):
                st.toast("Copied!")

    # Consensus display (multi-agent mode only) - COMPACT
    if execution_mode == "multi":
        consensus = service.calculate_consensus(round_obj.id)
        if consensus and consensus.get("total_voters", 0) > 0:
            approval_pct = consensus["percentage"] * 100
            threshold_pct = consensus["threshold"] * 100
            passed = consensus["passed"]

            # Single line consensus display
            status = "✅ PASSED" if passed else "❌ FAILED"
            st.caption(f"🗳️ Consensus: {consensus['approvals']}/{consensus['total_voters']} ({approval_pct:.0f}%/{threshold_pct:.0f}%) {status}")

            if consensus.get("feedback") and not passed:
                with st.expander("📝 Feedback"):
                    for fb in consensus["feedback"]:
                        st.caption(f"• {fb[:200]}...")


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

    # Get project's github_repo for auto-fill
    project_repo = None
    if session.project:
        project_repo = session.project.github_repo

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
        show_info("Add a GitHub token in Settings tab to enable GitHub features.")
        return

    github = GitHubService(github_token)

    # Show project repo status
    if project_repo:
        st.success(f"📁 Project repo: **{project_repo}**")
    else:
        st.info("💡 Set a GitHub repo in Project Settings (sidebar) to auto-fill here.")

    col1, col2 = st.columns(2)

    with col1:
        repo = st.text_input(
            "Repository",
            value=project_repo or "",
            placeholder="owner/repo",
            key="github_repo",
            help="Format: username/repository (auto-filled from project settings)"
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
# Phase 2: Memory System Status UI
# =============================================================================

def render_memory_status(service: RoundtableService, session: RoundtableSession):
    """
    Render Memory System status section.
    Shows RAG statistics, context health, and memory controls.
    """
    st.markdown("### 🧠 Memory System Status")

    # Get memory status from service
    memory_status = service.get_memory_status()

    if not memory_status["enabled"]:
        show_warning("Memory System is not enabled. Install chromadb to enable: `pip install chromadb`")
        return

    # Show enabled status
    st.success("✅ Memory System Active")

    # RAG Statistics
    st.markdown("#### 📊 RAG Database")

    rag_stats = memory_status.get("rag_stats", {})
    if rag_stats and "error" not in rag_stats:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Decisions", rag_stats.get("decisions", 0))

        with col2:
            st.metric("Code Changes", rag_stats.get("code_changes", 0))

        with col3:
            st.metric("Errors", rag_stats.get("errors", 0))

        with col4:
            st.metric("Total Memories", rag_stats.get("total", 0))

        # Additional stats in expander
        with st.expander("All Categories"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Conversations", rag_stats.get("conversations", 0))
            with col2:
                st.metric("Specs", rag_stats.get("specs", 0))
    else:
        st.caption("RAG statistics unavailable")

    # Context Health
    st.markdown("#### 💚 Context Health")

    context_health = memory_status.get("context_health", {})
    if context_health and "error" not in context_health:
        percentage = context_health.get("percentage", 0)
        status = context_health.get("status", "unknown")

        # Progress bar with color based on status
        st.progress(min(percentage / 100, 1.0))

        col1, col2 = st.columns(2)
        with col1:
            status_emoji = {"healthy": "🟢", "caution": "🟡", "critical": "🔴"}.get(status, "⚪")
            st.markdown(f"**Status:** {status_emoji} {status.upper()}")

        with col2:
            remaining = context_health.get("remaining", 0)
            st.markdown(f"**Remaining:** {remaining:,} tokens")

        # Recommendation
        recommendation = context_health.get("recommendation", "")
        if recommendation:
            if context_health.get("should_baton"):
                st.warning(f"⚠️ {recommendation}")
            else:
                st.info(f"💡 {recommendation}")
    else:
        st.caption("Context health unavailable")

    # Manual Decision Storage
    st.markdown("#### 📝 Store Manual Decision")

    with st.form("manual_decision_form"):
        decision_text = st.text_area(
            "Decision",
            placeholder="e.g., We decided to use PostgreSQL for the database",
            height=80
        )
        decision_context = st.text_input(
            "Context (optional)",
            placeholder="Additional context for this decision"
        )

        submitted = st.form_submit_button("Store Decision", type="primary")

        if submitted and decision_text:
            if service.store_manual_decision(
                decision=decision_text,
                context=decision_context or None,
                project_id=session.project_id
            ):
                show_success("Decision stored in RAG!")
                st.rerun()
            else:
                show_error("Failed to store decision")

    # Quick Actions
    st.markdown("#### ⚡ Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresh Stats", key="refresh_memory_stats"):
            st.rerun()

    with col2:
        if st.button("🔍 Search Memory", key="search_memory_btn"):
            st.session_state["show_memory_search"] = True

    # Memory Search Modal
    if st.session_state.get("show_memory_search"):
        with st.expander("🔍 Search Memory", expanded=True):
            search_query = st.text_input(
                "Search query",
                placeholder="e.g., database decisions",
                key="memory_search_query"
            )

            if search_query and service.rag_service:
                results = service.rag_service.retrieve(
                    query=search_query,
                    n_results=5,
                    project_id=session.project_id
                )

                if results:
                    st.markdown(f"**Found {len(results)} results:**")
                    for i, result in enumerate(results, 1):
                        with st.container():
                            st.markdown(f"**{i}. [{result['category'].upper()}]**")
                            st.text(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
                            st.caption(f"Distance: {result.get('distance', 'N/A'):.4f}")
                            st.divider()
                else:
                    st.info("No results found")

            if st.button("Close Search", key="close_memory_search"):
                st.session_state["show_memory_search"] = False
                st.rerun()


# =============================================================================
# Extended Panel with All Features
# =============================================================================

def render_tools_section(db, service: RoundtableService, session: RoundtableSession):
    """Render tools section with baton, GitHub, stats, memory, qualification."""
    st.markdown("**🛠️ Tools**")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 Baton", "🧠 Memory", "🐙 GitHub", "📊 Stats", "🧪 Qualify"])

    with tab1:
        render_baton_section(service, session)

    with tab2:
        render_memory_status(service, session)

    with tab3:
        render_github_section(db, service, session)

    with tab4:
        render_session_stats(service, session)

    with tab5:
        render_qualification_section(db, service, session)


def render_qualification_section(db, service: RoundtableService, session: RoundtableSession):
    """Render agent qualification section for the roundtable."""
    from app.services.pipeline_settings_service import (
        get_pipeline_setting_with_default,
        get_toggle,
    )

    # Get user_id from session (via project)
    user_id = 1  # Default for now, should come from session context

    st.markdown("**Agent Qualification (LIMB Test)**")

    # Show current qualification status
    if session.project_id:
        render_qualification_status_badge(db, user_id, session.project_id)

    st.divider()

    # Initialize qualification service
    openai_key = get_setting(db, "OPENAI_API_KEY")
    qual_service = AgentQualificationService(db=db, openai_key=openai_key)

    # Session state for qualification test
    qual_key = f"qual_test_{session.id}"
    if qual_key not in st.session_state:
        st.session_state[qual_key] = {
            "test_prompt": None,
            "metadata": None,
            "response": None,
            "result": None,
        }

    qual_state = st.session_state[qual_key]

    # Generate test button
    if st.button("🎲 Generate Test", key=f"gen_qual_{session.id}", use_container_width=True):
        test_prompt, metadata = qual_service.generate_test()
        qual_state["test_prompt"] = test_prompt
        qual_state["metadata"] = metadata
        qual_state["response"] = None
        qual_state["result"] = None
        st.rerun()

    # Show test prompt
    if qual_state["test_prompt"]:
        st.markdown("**Test Prompt:**")
        st.code(qual_state["test_prompt"][:500] + "..." if len(qual_state["test_prompt"]) > 500 else qual_state["test_prompt"])

        # Response input
        response = st.text_area(
            "Paste agent response:",
            height=150,
            key=f"qual_response_{session.id}"
        )

        if st.button("🔍 Evaluate", key=f"eval_qual_{session.id}", disabled=not response):
            result = qual_service.evaluate(response, qual_state["metadata"])
            qual_state["response"] = response
            qual_state["result"] = result

            # Save to database
            if session.project_id:
                from app.ui.qualification_panel import save_qualification_result
                save_qualification_result(
                    db, user_id, session.project_id,
                    qual_state["test_prompt"],
                    qual_state["metadata"],
                    response, result
                )

            st.rerun()

    # Show result
    if qual_state["result"]:
        result = qual_state["result"]
        badge = qual_service.get_result_badge(result)

        st.markdown(f"**Result: {badge}**")
        st.write(f"Score: {result.get('total_score', 0)}/7")

        if result.get("critical_fail"):
            st.error("⚠️ Critical failure - agent should not be trusted")

        # Auto-retry toggle
        auto_retry = get_toggle(db, user_id, "auto_retry_on_fail", session.project_id)
        if auto_retry and not qual_service.is_qualified(result):
            st.warning("Auto-retry enabled - generate new test for fresh agent")

    # Link to full qualification panel
    st.caption("For full settings, see the Qualification tab in Agent OS panel")
