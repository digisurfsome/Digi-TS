"""
Roundtable Compact UI - Popover-based controls with history navigation.

This is a condensed version of the Roundtable panel that:
1. Uses st.popover() for all settings (single control bar)
2. Has a history row for exchange navigation (hover preview, pin/unpin)
3. Shows parallel agent chat boxes side-by-side
4. Keeps everything "above the fold" - no scrolling needed
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

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
    MEMORY_SYSTEM_AVAILABLE,
)
from app.services import get_setting
from app.ui.layout import show_success, show_error, show_warning, show_info


# =============================================================================
# Session State Helpers
# =============================================================================

def init_compact_state():
    """Initialize session state for compact UI."""
    if "exchange_history" not in st.session_state:
        st.session_state.exchange_history = []
    if "pinned_exchanges" not in st.session_state:
        st.session_state.pinned_exchanges = []
    if "current_exchange_id" not in st.session_state:
        st.session_state.current_exchange_id = 0


def add_exchange(prompt: str, responses: Dict[str, Dict]):
    """Add a new exchange to history."""
    st.session_state.current_exchange_id += 1
    exchange = {
        "id": st.session_state.current_exchange_id,
        "timestamp": datetime.now().strftime("%H:%M"),
        "prompt": prompt,
        "responses": responses,
    }
    st.session_state.exchange_history.append(exchange)
    return exchange


def get_exchange_by_id(exchange_id: int) -> Optional[Dict]:
    """Get exchange by ID."""
    for ex in st.session_state.exchange_history:
        if ex["id"] == exchange_id:
            return ex
    return None


# =============================================================================
# Badge Helpers
# =============================================================================

def get_status_badge(status: RoundtableSessionStatus) -> str:
    """Get a colored badge for session status."""
    badges = {
        RoundtableSessionStatus.ACTIVE: "🟢 Active",
        RoundtableSessionStatus.PAUSED: "🟡 Paused",
        RoundtableSessionStatus.COMPLETED: "🔵 Done",
    }
    return badges.get(status, "⚪")


def get_role_icon(role: AgentRole) -> str:
    """Get icon for agent role."""
    icons = {
        AgentRole.BUILDER: "🔨",
        AgentRole.VOTER: "🗳️",
        AgentRole.REVIEWER: "📝",
    }
    return icons.get(role, "❓")


# =============================================================================
# Popover Renderers
# =============================================================================

def render_settings_popover(service: RoundtableService, session: RoundtableSession):
    """Render settings inside popover."""
    st.markdown("**⚙️ Execution Settings**")
    st.divider()

    # Mode toggle
    mode = st.radio(
        "Mode",
        options=["single", "multi"],
        index=0 if session.execution_mode == "single" else 1,
        key=f"compact_mode_{session.id}",
        horizontal=True,
    )

    if mode == "single":
        st.caption("Builder only, no voting")
    else:
        st.caption("Builder + Voters with consensus")

    if mode != session.execution_mode:
        service.update_session(session.id, execution_mode=mode)
        st.rerun()

    st.divider()

    # Voting threshold
    threshold = st.slider(
        "Voting Threshold",
        min_value=50,
        max_value=100,
        value=int(session.voting_threshold * 100),
        step=5,
        key=f"compact_threshold_{session.id}",
        disabled=(mode == "single"),
    )

    if threshold / 100 != session.voting_threshold:
        service.update_session(session.id, voting_threshold=threshold / 100)

    st.divider()

    # Token usage display
    chat_session_id = st.session_state.get("current_chat_session_id")
    if chat_session_id:
        from app.services import get_token_usage, get_all_settings
        from app.core.db import get_db
        with get_db() as db:
            settings = get_all_settings(db)
            max_tokens = int(settings.get("max_context_tokens", "128000"))
            token_usage = get_token_usage(db, chat_session_id)
            total_tokens = token_usage["total_tokens_used"]
            percent_used = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0

        if percent_used < 50:
            color = "🟢"
        elif percent_used < 70:
            color = "🟡"
        else:
            color = "🔴"

        st.markdown(f"**Token Usage:**")
        st.progress(min(percent_used / 100, 1.0))
        st.caption(f"{color} {total_tokens:,} / {max_tokens:,} ({percent_used:.1f}%)")

    # Warmup toggle
    show_warmup = st.checkbox(
        "Show warm-up messages",
        value=st.session_state.get("show_warmup_messages", False),
        key="compact_warmup_toggle",
    )
    st.session_state.show_warmup_messages = show_warmup


def render_prompt_popover(service: RoundtableService, session: RoundtableSession):
    """Render master prompt settings inside popover."""
    st.markdown("**📝 Master Prompt & Guardrails**")
    st.divider()

    # Preset selector
    preset_options = ["Custom"] + [p["name"] for p in PROMPT_PRESETS.values()]
    preset = st.selectbox(
        "Preset",
        options=preset_options,
        key=f"compact_preset_{session.id}",
    )

    # Get current values
    current_prompt = session.master_prompt or ""
    current_guardrails = session.master_guardrails or ""

    # Apply preset if selected
    if preset != "Custom":
        for key, value in PROMPT_PRESETS.items():
            if value["name"] == preset:
                current_prompt = value["system"]
                current_guardrails = value["guardrails"]
                break

    master_prompt = st.text_area(
        "System Prompt",
        value=current_prompt,
        height=80,
        key=f"compact_prompt_{session.id}",
        placeholder="Instructions for all agents...",
    )

    guardrails = st.text_area(
        "Guardrails",
        value=current_guardrails,
        height=60,
        key=f"compact_guardrails_{session.id}",
        placeholder="e.g., Never use eval()...",
    )

    if st.button("💾 Save", key="compact_save_prompt"):
        service.update_session(
            session.id,
            master_prompt=master_prompt,
            master_guardrails=guardrails,
        )
        show_success("Saved!")


def render_execute_popover(service: RoundtableService, session: RoundtableSession):
    """Render execution controls inside popover."""
    st.markdown("**▶️ Execution Control**")
    st.divider()

    # Round management
    if not session.rounds:
        st.caption("No rounds yet")
        if st.button("➕ Add Round", key="compact_add_first_round"):
            service.add_round(session.id)
            st.rerun()
        return

    # Round selector
    round_options = {r.name: r.id for r in session.rounds}
    round_names = list(round_options.keys())

    selected_round_name = st.selectbox(
        "Round",
        options=round_names,
        key="compact_round_select",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add", key="compact_add_round"):
            service.add_round(session.id)
            st.rerun()
    with col2:
        if st.button("🗑️ Del", key="compact_del_round"):
            round_id = round_options.get(selected_round_name)
            if round_id:
                service.delete_round(round_id)
                st.rerun()

    st.divider()

    # Task prompt for selected round
    round_id = round_options.get(selected_round_name)
    round_obj = service.get_round(round_id) if round_id else None

    if round_obj:
        task_prompt = st.text_area(
            "Task Prompt",
            value=round_obj.task_prompt or "",
            height=60,
            key=f"compact_task_{round_obj.id}",
            placeholder="What should agents build?",
        )

        if task_prompt != (round_obj.task_prompt or ""):
            service.update_round(round_obj.id, task_prompt=task_prompt)

        st.divider()

        # Agents
        st.caption(f"Agents ({len(round_obj.agents)})")

        for agent in round_obj.agents:
            col1, col2, col3 = st.columns([2, 1.5, 0.5])
            with col1:
                model_options = list(AVAILABLE_MODELS.keys())
                current_model = service.get_model_display_name(agent.model)
                try:
                    idx = model_options.index(current_model)
                except ValueError:
                    idx = 0
                new_model = st.selectbox(
                    "M", options=model_options, index=idx,
                    key=f"compact_agent_model_{agent.id}",
                    label_visibility="collapsed",
                )
                if new_model != current_model:
                    service.update_agent(agent.id, model_name=new_model)
                    st.rerun()

            with col2:
                role_options = list(AGENT_ROLES.keys())
                current_role_idx = role_options.index(agent.role.value) if agent.role.value in role_options else 0
                new_role = st.selectbox(
                    "R", options=role_options, index=current_role_idx,
                    key=f"compact_agent_role_{agent.id}",
                    label_visibility="collapsed",
                )
                if new_role != agent.role.value:
                    service.update_agent(agent.id, role=new_role)
                    st.rerun()

            with col3:
                if st.button("✕", key=f"compact_del_agent_{agent.id}"):
                    service.delete_agent(agent.id)
                    st.rerun()

        if st.button("➕ Agent", key="compact_add_agent"):
            default_model = list(AVAILABLE_MODELS.keys())[0]
            service.add_agent(round_obj.id, default_model, "builder")
            st.rerun()

        st.divider()

        # Execute buttons
        builders = [a for a in round_obj.agents if a.role == AgentRole.BUILDER]
        has_builder = len(builders) > 0

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Run", key="compact_run", type="primary",
                        disabled=(round_obj.status == "running" or not has_builder)):
                with st.spinner("Executing..."):
                    result = service.execute_round(round_obj.id)
                    if result["success"]:
                        show_success("Done!")
                    else:
                        show_error(result.get("error", "Failed"))
                st.rerun()

        with col2:
            if st.button("🔄 Rerun", key="compact_rerun",
                        disabled=(round_obj.status != "completed")):
                with st.spinner("Re-executing..."):
                    result = service.execute_round(round_obj.id)
                st.rerun()

        # Status
        status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅"}.get(round_obj.status, "❓")
        st.caption(f"Status: {status_emoji} {round_obj.status}")


def render_memory_popover(service: RoundtableService, session: RoundtableSession):
    """Render memory system status inside popover."""
    st.markdown("**🧠 Memory System**")
    st.divider()

    memory_status = service.get_memory_status()

    if not memory_status.get("enabled"):
        st.warning("Memory not enabled")
        return

    st.success("✅ Active")

    # RAG stats
    rag_stats = memory_status.get("rag_stats", {})
    if rag_stats and "error" not in rag_stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Decisions", rag_stats.get("decisions", 0))
            st.metric("Code", rag_stats.get("code_changes", 0))
        with col2:
            st.metric("Errors", rag_stats.get("errors", 0))
            st.metric("Total", rag_stats.get("total", 0))

    st.divider()

    # Context health
    context_health = memory_status.get("context_health", {})
    if context_health:
        percentage = context_health.get("percentage", 0)
        status = context_health.get("status", "unknown")
        status_emoji = {"healthy": "🟢", "caution": "🟡", "critical": "🔴"}.get(status, "⚪")

        st.progress(min(percentage / 100, 1.0))
        st.caption(f"{status_emoji} {status.upper()} - {context_health.get('remaining', 0):,} tokens left")

    st.divider()

    # Quick store
    decision = st.text_input("Quick store decision:", key="compact_decision_input",
                             placeholder="We decided to...")
    if st.button("💾 Store", key="compact_store_decision") and decision:
        if service.store_manual_decision(decision=decision, project_id=session.project_id):
            show_success("Stored!")
            st.rerun()

    # Search
    if st.button("🔍 Search Memory", key="compact_search_btn"):
        st.session_state["show_compact_memory_search"] = True


def render_github_popover(db: Session, service: RoundtableService, session: RoundtableSession):
    """Render GitHub controls inside popover."""
    st.markdown("**🐙 GitHub**")
    st.divider()

    github_token = get_setting(db, "GITHUB_TOKEN") or ""

    if not github_token:
        st.warning("No token configured")
        st.caption("Add in Settings tab")
        return

    # Get project repo
    project_repo = session.project.github_repo if session.project else None

    repo = st.text_input(
        "Repository",
        value=project_repo or "",
        placeholder="owner/repo",
        key="compact_github_repo",
    )

    branch = st.text_input(
        "Branch",
        value="main",
        key="compact_github_branch",
    )

    if repo:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Browse", key="compact_browse"):
                st.session_state["show_github_browser"] = True
        with col2:
            if st.button("🔀 PR", key="compact_pr"):
                st.session_state["show_pr_form"] = True


def render_stats_popover(service: RoundtableService, session: RoundtableSession):
    """Render session statistics inside popover."""
    st.markdown("**📊 Session Stats**")
    st.divider()

    stats = service.get_session_stats(session.id)

    if not stats:
        st.caption("No stats yet")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rounds", stats.get("total_rounds", 0))
        st.metric("Completed", stats.get("completed_rounds", 0))
    with col2:
        st.metric("Cost", f"${stats.get('total_cost', 0):.4f}")
        st.metric("Tokens", f"{stats.get('total_tokens', 0):,}")

    st.divider()

    if st.button("📤 Export JSON", key="compact_export"):
        export_data = service.export_session(session.id)
        st.session_state[f"export_data_{session.id}"] = export_data
        st.json(export_data)


# =============================================================================
# History Row
# =============================================================================

def render_history_row():
    """Render the exchange history navigation row."""
    exchanges = st.session_state.exchange_history
    pinned = st.session_state.pinned_exchanges
    current = st.session_state.current_exchange_id

    if not exchanges:
        st.caption("History: No exchanges yet")
        return

    # Calculate columns: label + exchanges + clear button
    num_exchanges = len(exchanges)
    max_visible = 15  # Limit visible indicators

    if num_exchanges > max_visible:
        # Show first few, ellipsis, last few
        visible_exchanges = exchanges[-max_visible:]
    else:
        visible_exchanges = exchanges

    cols = st.columns([0.8] + [0.4] * len(visible_exchanges) + [1])

    with cols[0]:
        st.caption("History:")

    for i, ex in enumerate(visible_exchanges):
        with cols[i + 1]:
            ex_id = ex["id"]

            # Determine indicator style
            if ex_id == current:
                label = f"{ex_id}▣"
            elif ex_id in pinned:
                label = f"{ex_id}●"
            else:
                label = str(ex_id)

            # Popover for preview
            with st.popover(label):
                render_exchange_preview(ex, pinned)

    with cols[-1]:
        if pinned and st.button("Clear Pins", key="clear_all_pins"):
            st.session_state.pinned_exchanges = []
            st.rerun()


def render_exchange_preview(exchange: Dict, pinned: List[int]):
    """Render exchange preview inside popover."""
    ex_id = exchange["id"]

    st.markdown(f"**Exchange #{ex_id}** - {exchange['timestamp']}")
    st.divider()

    # User prompt
    prompt_preview = exchange["prompt"][:150]
    if len(exchange["prompt"]) > 150:
        prompt_preview += "..."
    st.markdown(f"**You:** {prompt_preview}")

    st.divider()

    # Response summaries
    st.caption("Responses:")
    for agent_name, resp in exchange.get("responses", {}).items():
        status = "✅" if resp.get("status") == "done" else "⏳"
        tokens = resp.get("tokens", 0)
        st.caption(f"{agent_name}: {tokens} tok {status}")

    st.divider()

    # Pin/unpin button
    if ex_id in pinned:
        if st.button("📌 Unpin", key=f"unpin_{ex_id}"):
            st.session_state.pinned_exchanges.remove(ex_id)
            st.rerun()
    else:
        if st.button("📌 Pin this", key=f"pin_{ex_id}"):
            st.session_state.pinned_exchanges.append(ex_id)
            st.rerun()


def render_pinned_exchanges():
    """Render pinned exchanges as a compact row."""
    pinned_ids = st.session_state.pinned_exchanges

    if not pinned_ids:
        return

    st.markdown("**📌 Pinned**")

    # Tabs for pinned exchanges
    pinned_tabs = st.tabs([f"#{pid}" for pid in pinned_ids])

    for tab, pid in zip(pinned_tabs, pinned_ids):
        with tab:
            exchange = get_exchange_by_id(pid)
            if exchange:
                render_pinned_exchange_content(exchange)


def render_pinned_exchange_content(exchange: Dict):
    """Render content of a pinned exchange."""
    # Compact view of the exchange
    st.caption(f"Prompt: {exchange['prompt'][:100]}...")

    responses = exchange.get("responses", {})
    if responses:
        cols = st.columns(len(responses))
        for col, (agent_name, resp) in zip(cols, responses.items()):
            with col:
                st.caption(f"**{agent_name}**")
                content = resp.get("content", "")[:200]
                if len(resp.get("content", "")) > 200:
                    content += "..."
                st.text(content)

    # Unpin button
    if st.button(f"✕ Unpin", key=f"unpin_pinned_{exchange['id']}"):
        st.session_state.pinned_exchanges.remove(exchange["id"])
        st.rerun()


# =============================================================================
# Agent Chat Boxes
# =============================================================================

def render_agent_chat_boxes(service: RoundtableService, session: RoundtableSession):
    """Render parallel agent chat boxes."""
    # Get current round's agents
    if not session.rounds:
        st.info("Add a round to configure agents")
        return

    # Use selected round or latest
    round_obj = session.rounds[-1]  # Latest round

    if not round_obj.agents:
        st.info("Add agents to see chat boxes")
        return

    # Create columns for each agent
    agents = round_obj.agents
    cols = st.columns(len(agents))

    for col, agent in zip(cols, agents):
        with col:
            render_single_agent_box(service, agent, round_obj)


def render_single_agent_box(service: RoundtableService, agent: RoundtableAgent, round_obj: RoundtableRound):
    """Render a single agent's chat box."""
    model_name = service.get_model_display_name(agent.model)
    role_icon = get_role_icon(agent.role)

    # Header
    st.markdown(f"**{role_icon} {model_name}**")

    # Response container
    container = st.container(height=300, border=True)

    with container:
        # Show latest response if available
        if agent.responses:
            latest = agent.responses[-1]

            # Metrics row
            tokens = latest.tokens_input + latest.tokens_output
            st.caption(f"{tokens:,} tok | ${latest.cost:.4f} | {latest.duration_seconds:.1f}s")

            # Content
            st.markdown(latest.content)
        else:
            st.caption("Awaiting response...")


# =============================================================================
# Main Compact Panel
# =============================================================================

def render_roundtable_compact(db: Session, project_id: Optional[int] = None):
    """
    Render the compact Roundtable panel with popover controls.

    Layout:
    1. Control bar (popovers for settings, prompt, execute, memory, github, stats)
    2. History row (exchange indicators with hover preview)
    3. Pinned exchanges (if any)
    4. Agent chat boxes (side by side)
    5. Input bar
    """
    import os

    # Initialize state
    init_compact_state()

    # Get API keys
    anthropic_key = get_setting(db, "ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = get_setting(db, "OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    google_key = get_setting(db, "GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")

    # Initialize memory services
    rag_service = None
    context_assembler = None
    if MEMORY_SYSTEM_AVAILABLE:
        try:
            from app.services.rag_service import RAGService
            from app.services.context_assembler import ContextAssembler
            rag_service = RAGService()
            context_assembler = ContextAssembler(db=db, rag_service=rag_service)
        except Exception:
            pass

    # Initialize service
    service = RoundtableService(
        db=db,
        anthropic_key=anthropic_key,
        openai_key=openai_key,
        google_key=google_key,
        rag_service=rag_service,
        context_assembler=context_assembler,
    )

    # Get sessions
    try:
        sessions = service.list_sessions(project_id=project_id)
    except Exception as e:
        if "does not exist" in str(e) or "UndefinedTable" in str(e):
            show_warning("Initialize schema first (System Status tab)")
            return
        show_error(f"Error: {e}")
        return

    session_options = {s.name: s.id for s in sessions}
    session_options["+ New"] = None

    # =========================================================================
    # ROW 1: CONTROL BAR
    # =========================================================================
    cols = st.columns([1.2, 1.5, 0.6, 0.5, 0.6, 0.5, 0.5, 0.5, 0.8])

    with cols[0]:
        st.markdown("### 🔄 Roundtable")

    with cols[1]:
        selected_name = st.selectbox(
            "Session",
            options=list(session_options.keys()),
            key="compact_session_select",
            label_visibility="collapsed",
        )

    # Handle new session
    if selected_name == "+ New":
        with st.form("compact_new_session"):
            name = st.text_input("Name", value="New Session")
            if st.form_submit_button("Create", type="primary"):
                new_session = service.create_session(name=name, project_id=project_id)
                show_success(f"Created: {name}")
                st.rerun()
        return

    # Get selected session
    session_id = session_options.get(selected_name)
    if not session_id:
        show_info("Select or create a session")
        return

    session = service.get_session(session_id)
    if not session:
        show_error("Session not found")
        return

    # Popover: Settings
    with cols[2]:
        threshold_pct = int(session.voting_threshold * 100)
        with st.popover(f"⚙️ {threshold_pct}%"):
            render_settings_popover(service, session)

    # Popover: Prompt
    with cols[3]:
        prompt_indicator = "●" if session.master_prompt else ""
        with st.popover(f"📝{prompt_indicator}"):
            render_prompt_popover(service, session)

    # Popover: Execute
    with cols[4]:
        round_label = f"R{len(session.rounds)}" if session.rounds else "R0"
        with st.popover(f"▶️ {round_label}"):
            render_execute_popover(service, session)

    # Popover: Memory
    with cols[5]:
        memory_status = service.get_memory_status()
        memory_count = memory_status.get("rag_stats", {}).get("total", 0) if memory_status.get("enabled") else 0
        with st.popover(f"🧠 {memory_count}"):
            render_memory_popover(service, session)

    # Popover: GitHub
    with cols[6]:
        repo_indicator = "●" if (session.project and session.project.github_repo) else ""
        with st.popover(f"🐙{repo_indicator}"):
            render_github_popover(db, service, session)

    # Popover: Stats
    with cols[7]:
        stats = service.get_session_stats(session.id)
        cost = stats.get("total_cost", 0) if stats else 0
        with st.popover(f"📊"):
            render_stats_popover(service, session)

    # Status badge
    with cols[8]:
        st.markdown(get_status_badge(session.status))

    # =========================================================================
    # ROW 2: HISTORY NAVIGATION
    # =========================================================================
    render_history_row()

    st.divider()

    # =========================================================================
    # ROW 3: PINNED EXCHANGES (if any)
    # =========================================================================
    render_pinned_exchanges()

    # =========================================================================
    # ROW 4: AGENT CHAT BOXES
    # =========================================================================
    render_agent_chat_boxes(service, session)

    # =========================================================================
    # ROW 5: INPUT BAR
    # =========================================================================
    st.divider()

    input_col, btn_col = st.columns([5, 1])

    with input_col:
        prompt = st.text_input(
            "Enter your prompt...",
            key="compact_prompt_input",
            label_visibility="collapsed",
            placeholder="Enter your prompt... All agents will respond",
        )

    with btn_col:
        run_all = st.button("▶️ Run All", key="compact_run_all", type="primary")

    # Handle run all
    if run_all and prompt:
        if not session.rounds:
            show_warning("Add a round first (click ▶️ R0)")
            return

        round_obj = session.rounds[-1]

        # Update task prompt
        service.update_round(round_obj.id, task_prompt=prompt)

        # Execute
        with st.spinner("Running all agents..."):
            result = service.execute_round(round_obj.id)

        if result["success"]:
            # Add to exchange history
            responses = {}
            for agent in round_obj.agents:
                if agent.responses:
                    latest = agent.responses[-1]
                    model_name = service.get_model_display_name(agent.model)
                    responses[model_name] = {
                        "content": latest.content,
                        "tokens": latest.tokens_input + latest.tokens_output,
                        "status": "done",
                    }

            add_exchange(prompt, responses)
            show_success("Completed!")
        else:
            show_error(result.get("error", "Execution failed"))

        st.rerun()


# =============================================================================
# Entry point for tab integration
# =============================================================================

def render_roundtable_panel_compact(db: Session, project_id: Optional[int] = None):
    """Wrapper for integration with existing tab system."""
    render_roundtable_compact(db, project_id)
