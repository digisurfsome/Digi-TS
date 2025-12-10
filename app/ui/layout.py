"""
UI layout components and helpers for Streamlit.

This module provides reusable UI components and layout functions.
"""

import streamlit as st
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session

from app.core.models import UserProfile, Project, DescriptionMode
from app.services import (
    list_all_users,
    list_user_projects,
    create_project,
    get_all_settings,
    set_multiple_settings,
    get_project_context,
    update_project_context,
    get_or_create_chat_session,
    get_chat_history,
    send_chat_message,
    clear_chat_history,
    get_token_usage,
    get_setting_as_int,
    generate_baton,
    check_auto_baton_trigger,
    get_warmed_sessions,
    switch_to_session,
    generate_auto_project_description,
    get_combined_description,
    update_description_mode,
    export_truth_doc,
    get_truth_doc_filename,
    get_truth_doc_preview,
    detect_nodes_from_exchange,
    get_node_type_icon,
    create_node,
)
from app.core.models import NodeType, NodeStatus


def render_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Render application header.

    Args:
        title: Main title
        subtitle: Optional subtitle
    """
    st.title(title)
    if subtitle:
        st.markdown(f"*{subtitle}*")
    st.divider()


def render_sidebar() -> None:
    """Render application sidebar with navigation."""
    with st.sidebar:
        st.header("Navigation")
        st.info("Use the tabs above to navigate between features")


def render_footer() -> None:
    """Render application footer."""
    from app.config.settings import settings as app_settings
    st.divider()
    st.markdown(
        f"""
        <div style='text-align: center; color: gray; padding: 1rem;'>
            <small>{app_settings.APP_NAME} v{app_settings.APP_VERSION}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_success(message: str) -> None:
    """Display success message."""
    st.success(f"✅ {message}")


def show_error(message: str) -> None:
    """Display error message."""
    st.error(f"❌ {message}")


def show_warning(message: str) -> None:
    """Display warning message."""
    st.warning(f"⚠️ {message}")


def show_info(message: str) -> None:
    """Display info message."""
    st.info(f"ℹ️ {message}")


# Project Selection Components

def render_user_selector(db: Session, users: List[UserProfile]) -> Optional[UserProfile]:
    """
    Render user selection dropdown.

    Args:
        db: Database session
        users: List of users

    Returns:
        Selected user or None
    """
    if not users:
        show_warning("No users found. Please create a user first.")
        return None

    user_options = {f"{user.username} ({user.email})": user for user in users}
    user_names = list(user_options.keys())

    # Initialize session state
    if "selected_user_name" not in st.session_state:
        st.session_state.selected_user_name = user_names[0]

    selected_name = st.selectbox(
        "Select User",
        user_names,
        key="user_selector",
        index=user_names.index(st.session_state.selected_user_name) if st.session_state.selected_user_name in user_names else 0
    )

    st.session_state.selected_user_name = selected_name
    return user_options[selected_name]


def render_project_selector(
    db: Session,
    user: UserProfile
) -> Tuple[Optional[Project], bool]:
    """
    Render project selection dropdown with create new option.

    Args:
        db: Database session
        user: Current user

    Returns:
        Tuple of (selected_project, should_create_new)
    """
    projects = list_user_projects(db, user.id)

    if not projects:
        st.info("📁 No projects yet – create your first project below!")
        if st.button("➕ Create First Project", type="primary", use_container_width=True):
            return None, True
        return None, False

    # Build project options
    project_options = {p.name: p for p in projects}
    project_names = list(project_options.keys())

    # Determine current selection
    current_selection = None

    # First priority: use current_project_id if set
    if "current_project_id" in st.session_state:
        for name, proj in project_options.items():
            if proj.id == st.session_state.current_project_id:
                current_selection = name
                break

    # Second priority: use selected_project_name if set and valid
    if not current_selection and "selected_project_name" in st.session_state:
        if st.session_state.selected_project_name in project_names:
            current_selection = st.session_state.selected_project_name

    # Default: select first project
    if not current_selection:
        current_selection = project_names[0]

    # Update session state to match
    st.session_state.selected_project_name = current_selection

    # Render selectbox
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_name = st.selectbox(
            "Select Project",
            project_names,
            index=project_names.index(current_selection),
            key="project_selector",
        )

        # Update session state when selection changes
        if selected_name != st.session_state.selected_project_name:
            st.session_state.selected_project_name = selected_name
            selected_project = project_options[selected_name]
            st.session_state.current_project_id = selected_project.id
            st.session_state.current_project_name = selected_project.name
            st.rerun()

    with col2:
        if st.button("➕ New", help="Create a new project", use_container_width=True):
            return None, True

    # Return the selected project
    selected_project = project_options[selected_name]
    return selected_project, False


def render_create_project_form(db: Session, user: UserProfile) -> Optional[Project]:
    """
    Render form to create a new project.

    Args:
        db: Database session
        user: Current user

    Returns:
        Created project or None
    """
    st.subheader("Create New Project")

    with st.form("create_project_form"):
        name = st.text_input("Project Name *", placeholder="My Design Project")
        description = st.text_area(
            "Description (optional)",
            placeholder="Describe your project...",
            height=100
        )

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Create Project", type="primary")
        with col2:
            cancel = st.form_submit_button("Cancel")

        if submit:
            if not name or not name.strip():
                show_error("Project name is required")
                return None

            try:
                project = create_project(
                    db,
                    name=name.strip(),
                    owner_id=user.id,
                    description=description.strip() if description else None
                )
                show_success(f"Project '{project.name}' created successfully!")
                st.session_state.selected_project_name = project.name
                st.rerun()
            except Exception as e:
                show_error(f"Failed to create project: {str(e)}")
                return None

        if cancel:
            st.rerun()

    return None


# Settings UI Components

def render_settings_ui(db: Session, user_id: Optional[int] = None) -> None:
    """
    Render settings UI with all configuration options.

    Args:
        db: Database session
        user_id: User ID for user-specific settings (None for global)
    """
    st.subheader("⚙️ Settings")
    st.markdown("Configure application and AI model settings.")

    # Load current settings
    current_settings = get_all_settings(db, user_id)

    with st.form("settings_form"):
        st.markdown("### API Configuration")

        openai_key = st.text_input(
            "OpenAI API Key (optional, uses env if blank)",
            value=current_settings.get("OPENAI_API_KEY", ""),
            type="password",
            help="Leave blank to use OPENAI_API_KEY from environment"
        )

        col1, col2 = st.columns(2)
        with col1:
            chat_model = st.text_input(
                "Default Chat Model",
                value=current_settings.get("DEFAULT_CHAT_MODEL", "gpt-4-turbo-preview"),
                help="OpenAI model for chat interactions"
            )

        with col2:
            summary_model = st.text_input(
                "Default Summary Model",
                value=current_settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview"),
                help="OpenAI model for generating summaries"
            )

        st.markdown("### Context & Baton Settings")

        col1, col2 = st.columns(2)
        with col1:
            max_tokens = st.number_input(
                "Max Context Tokens",
                value=int(current_settings.get("max_context_tokens", "8000")),
                min_value=1000,
                max_value=128000,
                step=1000,
                help="Maximum tokens for context"
            )

        with col2:
            baton_threshold = st.number_input(
                "Auto Baton Threshold (%)",
                value=int(current_settings.get("auto_baton_threshold_percent", "80")),
                min_value=0,
                max_value=100,
                step=5,
                help="Trigger baton creation at this percentage of max tokens"
            )

        auto_warmup = st.checkbox(
            "Enable Auto Warmup",
            value=current_settings.get("auto_warmup_enabled", "true").lower() == "true",
            help="Automatically warm up AI with project context"
        )

        st.markdown("### Warmup Prompts")
        st.caption("These prompts are used to warm up the AI with project context.")

        warmup_1 = st.text_area(
            "Warmup Prompt 1",
            value=current_settings.get("warmup_prompt_1", ""),
            height=80
        )

        warmup_2 = st.text_area(
            "Warmup Prompt 2",
            value=current_settings.get("warmup_prompt_2", ""),
            height=80
        )

        warmup_3 = st.text_area(
            "Warmup Prompt 3",
            value=current_settings.get("warmup_prompt_3", ""),
            height=80
        )

        warmup_4 = st.text_area(
            "Warmup Prompt 4",
            value=current_settings.get("warmup_prompt_4", ""),
            height=80
        )

        st.markdown("### Baton Description Prompt")
        st.caption("Template for generating baton descriptions.")

        baton_prompt = st.text_area(
            "Baton Description Prompt",
            value=current_settings.get("baton_description_prompt", ""),
            height=100,
            help="Prompt template for AI to generate baton descriptions"
        )

        st.markdown("### Security")

        pin_code = st.text_input(
            "PIN Code (optional)",
            value=current_settings.get("pin_code", ""),
            type="password",
            help="Optional PIN for additional security"
        )

        st.divider()

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            save_button = st.form_submit_button("💾 Save Settings", type="primary")
        with col2:
            reset_button = st.form_submit_button("🔄 Reset to Defaults")

        if save_button:
            try:
                new_settings = {
                    "OPENAI_API_KEY": openai_key,
                    "DEFAULT_CHAT_MODEL": chat_model,
                    "DEFAULT_SUMMARY_MODEL": summary_model,
                    "max_context_tokens": str(max_tokens),
                    "auto_baton_threshold_percent": str(baton_threshold),
                    "auto_warmup_enabled": "true" if auto_warmup else "false",
                    "warmup_prompt_1": warmup_1,
                    "warmup_prompt_2": warmup_2,
                    "warmup_prompt_3": warmup_3,
                    "warmup_prompt_4": warmup_4,
                    "baton_description_prompt": baton_prompt,
                    "pin_code": pin_code,
                }

                set_multiple_settings(db, new_settings, user_id)
                show_success("Settings saved successfully!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to save settings: {str(e)}")

        if reset_button:
            try:
                from app.services.settings_service import DEFAULT_SETTINGS
                set_multiple_settings(db, DEFAULT_SETTINGS, user_id)
                show_success("Settings reset to defaults!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to reset settings: {str(e)}")


# Project Context UI Components

def render_project_context_ui(db: Session, project: Project) -> None:
    """
    Render project context UI.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("📋 Project Context")
    st.markdown(f"Manage context and guidelines for **{project.name}**")

    # Get current context
    context = get_project_context(db, project.id)

    # Description Mode Selector
    st.markdown("#### Description Mode")
    current_mode = context.description_mode if context else DescriptionMode.MANUAL

    mode_options = {
        "Manual Only": DescriptionMode.MANUAL,
        "Auto-Generated Only": DescriptionMode.AUTO,
        "Merged (Manual + Auto)": DescriptionMode.MERGE
    }

    selected_mode_label = [k for k, v in mode_options.items() if v == current_mode][0]

    new_mode_label = st.selectbox(
        "Choose how to combine manual and auto descriptions",
        options=list(mode_options.keys()),
        index=list(mode_options.keys()).index(selected_mode_label),
        help="Manual: use only manual description | Auto: use only AI-generated | Merge: combine both"
    )

    new_mode = mode_options[new_mode_label]

    # Update mode if changed
    if new_mode != current_mode:
        try:
            update_description_mode(db, project.id, new_mode)
            show_success(f"Description mode updated to: {new_mode_label}")
            st.rerun()
        except Exception as e:
            show_error(f"Failed to update mode: {str(e)}")

    st.divider()

    # Manual description
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Manual Description")
        st.caption("Describe your project, design system, and guidelines.")

    with col2:
        if st.button("💾 Save Manual", help="Save manual description"):
            st.session_state.save_context_clicked = True

    # Manual description editor
    manual_desc = st.text_area(
        "Manual Description",
        value=context.content if context else "",
        height=250,
        label_visibility="collapsed",
        help="Enter project context, design guidelines, constraints, etc."
    )

    # Save context if button was clicked
    if st.session_state.get("save_context_clicked"):
        try:
            update_project_context(db, project.id, manual_desc)
            show_success("Manual description saved successfully!")
            st.session_state.save_context_clicked = False
            st.rerun()
        except Exception as e:
            show_error(f"Failed to save description: {str(e)}")

    st.divider()

    # Auto description
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Auto Description")
        st.caption("AI-generated summary from your project nodes and structure.")

    with col2:
        regenerate_btn = st.button("🔄 Regenerate", help="Generate fresh auto-description from current project state")

    # Regenerate auto description if button clicked
    if regenerate_btn:
        with st.spinner("Generating auto-description from project nodes..."):
            try:
                settings = get_all_settings(db)
                auto_desc = generate_auto_project_description(db, project.id, settings)
                show_success("Auto-description generated successfully!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to generate auto-description: {str(e)}")

    # Display auto-generated content
    auto_desc_value = context.auto_description if context and context.auto_description else "(No auto-description generated yet. Click 'Regenerate' above.)"

    st.text_area(
        "Auto-generated description",
        value=auto_desc_value,
        height=250,
        disabled=True,
        label_visibility="collapsed",
        help="This description is automatically generated from your project structure and nodes"
    )

    st.divider()

    # Preview of combined description based on mode
    with st.expander("👁️ Preview Combined Description", expanded=False):
        st.markdown("**This is how the description will appear in Batons and Truth Doc:**")
        st.divider()
        combined = get_combined_description(db, project.id)
        st.markdown(combined)


def render_truth_doc_export_ui(db: Session, project: Project) -> None:
    """
    Render Truth Doc export UI.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("📄 Truth Doc Export")
    st.markdown(f"Export comprehensive documentation for **{project.name}**")

    st.info(
        "Truth Doc is a complete markdown document containing your project description, "
        "all components with their versions, and full history. Perfect for documentation, "
        "handoffs, or archival."
    )

    # Export options
    include_archived = st.checkbox(
        "Include archived/deleted nodes",
        value=False,
        help="Include components that have been archived or deleted"
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        preview_btn = st.button("👁️ Preview", type="secondary", use_container_width=True)

    with col2:
        export_btn = st.button("📥 Export", type="primary", use_container_width=True)

    # Preview Truth Doc
    if preview_btn:
        with st.spinner("Generating Truth Doc preview..."):
            try:
                truth_doc = export_truth_doc(db, project.id, include_archived)
                preview = get_truth_doc_preview(truth_doc, max_lines=100)

                st.divider()
                st.markdown("### Truth Doc Preview")
                st.caption(f"Showing first 100 lines. Full document has {len(truth_doc.split(chr(10)))} lines.")

                st.code(preview, language="markdown")

                # Store full doc in session for download
                st.session_state.truth_doc_full = truth_doc
                st.session_state.truth_doc_filename = get_truth_doc_filename(project.name)

            except Exception as e:
                show_error(f"Failed to generate preview: {str(e)}")

    # Export Truth Doc
    if export_btn:
        with st.spinner("Generating complete Truth Doc..."):
            try:
                truth_doc = export_truth_doc(db, project.id, include_archived)
                filename = get_truth_doc_filename(project.name)

                # Store in session
                st.session_state.truth_doc_full = truth_doc
                st.session_state.truth_doc_filename = filename

                show_success(f"Truth Doc generated! ({len(truth_doc)} characters, {len(truth_doc.split(chr(10)))} lines)")

                st.divider()

                # Download button
                st.download_button(
                    label="💾 Download Truth Doc",
                    data=truth_doc,
                    file_name=filename,
                    mime="text/markdown",
                    type="primary",
                    use_container_width=True
                )

                # Copy to clipboard option
                st.markdown("**Or copy to clipboard:**")
                st.code(truth_doc, language="markdown", line_numbers=False)

            except Exception as e:
                show_error(f"Failed to generate Truth Doc: {str(e)}")

    # If doc is in session, show download button
    if st.session_state.get("truth_doc_full"):
        st.divider()
        st.markdown("### Download Truth Doc")

        st.download_button(
            label="💾 Download Truth Doc",
            data=st.session_state.truth_doc_full,
            file_name=st.session_state.get("truth_doc_filename", "truth_doc.md"),
            mime="text/markdown",
            use_container_width=True
        )


# Chat Panel Components

def render_token_meter(
    db: Session,
    session_id: int,
    max_tokens: int = 8000
) -> None:
    """
    Render token usage meter with color-coded progress bar.

    Args:
        db: Database session
        session_id: Chat session ID
        max_tokens: Maximum context tokens
    """
    # Get token usage
    token_usage = get_token_usage(db, session_id)
    total_tokens = token_usage["total_tokens_used"]

    # Calculate percentage
    percent_used = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0
    percent_used = min(percent_used, 100)  # Cap at 100%

    # Determine color based on usage
    if percent_used < 50:
        color = "🟢"  # Green
        bar_color = "normal"
    elif percent_used < 70:
        color = "🟡"  # Yellow
        bar_color = "normal"
    elif percent_used < 90:
        color = "🟠"  # Orange
        bar_color = "normal"
    else:
        color = "🔴"  # Red
        bar_color = "normal"

    # Display meter
    st.markdown(f"**{color} Token Usage: {total_tokens:,} / {max_tokens:,}** ({percent_used:.1f}%)")

    # Progress bar
    st.progress(percent_used / 100)

    # Token breakdown in expander
    with st.expander("Token Details"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Prompt Tokens", f"{token_usage['total_prompt_tokens']:,}")
        with col2:
            st.metric("Completion Tokens", f"{token_usage['total_completion_tokens']:,}")
        with col3:
            st.metric("Total Used", f"{total_tokens:,}")


def render_chat_panel(
    db: Session,
    user_id: int,
    project: Project
) -> None:
    """
    Render chat panel with message history and input.

    Args:
        db: Database session
        user_id: Current user ID
        project: Current project
    """
    st.subheader("💬 AI Chat")

    # Check for warmed pending sessions
    warmed_sessions = get_warmed_sessions(db, user_id, project.id)
    if warmed_sessions and "baton_notification_shown" not in st.session_state:
        st.success(f"🎯 New warmed session ready! ({len(warmed_sessions)} available)")
        st.session_state.baton_notification_shown = True

    # Get or create chat session
    # Check if we should use a different session from session state
    if "current_chat_session_id" in st.session_state:
        from app.core.models import ChatSession
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == st.session_state.current_chat_session_id,
            ChatSession.user_id == user_id,
            ChatSession.project_id == project.id
        ).first()
        if not chat_session:
            # Session not found, get default
            chat_session = get_or_create_chat_session(db, user_id, project.id)
            st.session_state.current_chat_session_id = chat_session.id
    else:
        chat_session = get_or_create_chat_session(db, user_id, project.id)
        st.session_state.current_chat_session_id = chat_session.id

    # Display current project and session info (Phase 8)
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.markdown(f"**Project:** {project.name}")
    with col2:
        st.markdown(f"**Session:** {chat_session.title}")
    with col3:
        # New session button
        if st.button("🆕 New", help="Start a new clean session (no baton)", use_container_width=True):
            try:
                from datetime import datetime
                from app.core.models import ChatSession, SessionStatus

                # Create new clean session
                new_session = ChatSession(
                    user_id=user_id,
                    project_id=project.id,
                    title=f"Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    description="Clean session without baton",
                    session_type="general",
                    is_active=True,
                    status=SessionStatus.ACTIVE,
                    total_prompt_tokens=0,
                    total_completion_tokens=0,
                    total_tokens_used=0
                )
                db.add(new_session)

                # Deactivate old session
                chat_session.is_active = False

                db.commit()
                db.refresh(new_session)

                # Update session state
                st.session_state.current_chat_session_id = new_session.id
                show_success("New clean session started!")
                st.rerun()
            except Exception as e:
                show_error(f"Failed to create new session: {str(e)}")

    st.divider()

    # Session switcher
    if warmed_sessions:
        with st.expander("🔄 Switch to Warmed Session", expanded=False):
            for warmed in warmed_sessions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{warmed.title}**")
                    st.caption(f"Created: {warmed.created_at.strftime('%Y-%m-%d %H:%M')}")
                with col2:
                    if st.button("Switch", key=f"switch_{warmed.id}"):
                        switch_to_session(db, chat_session.id, warmed.id)
                        st.session_state.current_chat_session_id = warmed.id
                        st.session_state.baton_notification_shown = False
                        show_success("Switched to warmed session!")
                        st.rerun()

    # Get settings
    settings = get_all_settings(db)
    max_tokens = int(settings.get("max_context_tokens", "8000"))
    chat_model = settings.get("DEFAULT_CHAT_MODEL", "gpt-4-turbo-preview")
    openai_key = settings.get("OPENAI_API_KEY", "")

    # Token meter
    render_token_meter(db, chat_session.id, max_tokens)

    st.divider()

    # Chat history with warm-up toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### Conversation")
    with col2:
        show_warmup = st.checkbox("Show warm-up", value=False, key="show_warmup_toggle")

    messages = get_chat_history(db, chat_session.id)

    # Display messages in a container with scrolling
    chat_container = st.container()

    with chat_container:
        if not messages:
            st.info("Start a conversation by typing a message below.")
        else:
            for msg in messages:
                # Filter warm-up messages based on toggle
                if msg.is_warmup and not show_warmup:
                    continue

                # Skip system messages unless showing warmup
                if msg.role.value == "system":
                    if show_warmup:
                        with st.chat_message("assistant", avatar="📋"):
                            st.markdown(f"*System: {msg.content[:200]}...*" if len(msg.content) > 200 else f"*System: {msg.content}*")
                    continue

                # Add warm-up indicator
                warmup_indicator = " 🔥" if msg.is_warmup else ""

                if msg.role.value == "user":
                    with st.chat_message("user"):
                        st.markdown(msg.content + warmup_indicator)
                elif msg.role.value == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(msg.content + warmup_indicator)

    st.divider()

    # Input area - use text_area for larger input
    user_input = st.text_area(
        "Message",
        key="chat_input",
        placeholder="Type your message...",
        label_visibility="collapsed",
        height=100
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        send_button = st.button("📤 Send", type="primary", use_container_width=True)

    with col2:
        if st.button("🗑️ Clear", help="Clear chat history"):
            clear_chat_history(db, chat_session.id)
            st.rerun()

    with col3:
        baton_button = st.button("🎯 Baton Now", help="Create a new warmed session with project snapshot")

    # Manual baton creation
    if baton_button:
        with st.spinner("Creating baton snapshot and warming new session..."):
            try:
                baton, new_session = generate_baton(
                    db=db,
                    user_id=user_id,
                    project_id=project.id,
                    from_session_id=chat_session.id,
                    settings=settings,
                    run_warmup=True
                )
                show_success(f"Baton created! New warmed session: {new_session.title}")
                st.session_state.baton_notification_shown = False
                st.rerun()
            except Exception as e:
                show_error(f"Failed to create baton: {str(e)}")

    # Send message
    if send_button and user_input and user_input.strip():
        with st.spinner("Thinking..."):
            try:
                user_msg, assistant_msg = send_chat_message(
                    db,
                    project.id,
                    chat_session.id,
                    user_input.strip(),
                    openai_api_key=openai_key if openai_key else None,
                    chat_model=chat_model
                )

                # Auto-detect potential nodes from this exchange
                if openai_key or settings.get("OPENAI_API_KEY"):
                    api_key_for_detection = openai_key or settings.get("OPENAI_API_KEY")
                    detected = detect_nodes_from_exchange(
                        user_message=user_input.strip(),
                        assistant_message=assistant_msg.content,
                        openai_api_key=api_key_for_detection,
                        model=settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")
                    )
                    if detected:
                        # Store detected nodes in session state for UI display
                        st.session_state.detected_nodes = detected
                        st.session_state.detected_nodes_project_id = project.id

                # Check for auto-baton trigger
                if check_auto_baton_trigger(db, chat_session.id, settings):
                    show_info("Token threshold reached! Creating auto-baton...")
                    try:
                        auto_baton, auto_session = generate_baton(
                            db=db,
                            user_id=user_id,
                            project_id=project.id,
                            from_session_id=chat_session.id,
                            settings=settings,
                            run_warmup=True
                        )
                        # Update baton type to auto
                        auto_baton.snapshot_type = "auto"
                        db.commit()

                        st.session_state.baton_notification_shown = False
                        show_success("Auto-baton created! A new warmed session is ready.")
                    except Exception as e:
                        show_warning(f"Auto-baton creation failed: {str(e)}")

                st.rerun()
            except Exception as e:
                show_error(f"Chat error: {str(e)}")
    elif send_button and not user_input.strip():
        show_warning("Please enter a message")

    # Display detected node suggestions
    _render_detected_nodes_ui(db, project.id)


def _render_detected_nodes_ui(db: Session, project_id: int) -> None:
    """
    Render UI for detected node suggestions.

    Shows a popup/expander when potential nodes are detected from chat.
    Allows user to accept, edit, or dismiss detected nodes.

    Args:
        db: Database session
        project_id: Current project ID
    """
    # Check if we have detected nodes for current project
    if "detected_nodes" not in st.session_state:
        return

    if st.session_state.get("detected_nodes_project_id") != project_id:
        return

    detected_nodes = st.session_state.detected_nodes
    if not detected_nodes:
        return

    # Show detected nodes in an expander (auto-expanded)
    with st.expander("🔍 **Potential Nodes Detected!**", expanded=True):
        st.markdown("The AI detected items that might be worth tracking as nodes:")

        for idx, node in enumerate(detected_nodes):
            icon = get_node_type_icon(node.suggested_type)
            confidence_pct = int(node.confidence * 100)

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"**{icon} {node.suggested_name}** ({node.suggested_type.value})")
                st.caption(f"{node.suggested_description}")
                st.caption(f"Confidence: {confidence_pct}% | *{node.reason}*")

            with col2:
                # Create node button
                if st.button("✅ Create", key=f"create_node_{idx}", help="Create this node"):
                    try:
                        new_node = create_node(
                            db=db,
                            project_id=project_id,
                            name=node.suggested_name,
                            node_type=node.suggested_type,
                            description=node.suggested_description,
                            status=NodeStatus.DRAFT
                        )
                        show_success(f"Created node: {node.suggested_name}")
                        # Remove this node from the list
                        st.session_state.detected_nodes = [
                            n for i, n in enumerate(detected_nodes) if i != idx
                        ]
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to create node: {str(e)}")

            with col3:
                # Dismiss button
                if st.button("❌ Skip", key=f"dismiss_node_{idx}", help="Dismiss this suggestion"):
                    # Remove this node from the list
                    st.session_state.detected_nodes = [
                        n for i, n in enumerate(detected_nodes) if i != idx
                    ]
                    st.rerun()

            st.divider()

        # Dismiss all button
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Create All", help="Create all suggested nodes"):
                created_count = 0
                for node in detected_nodes:
                    try:
                        create_node(
                            db=db,
                            project_id=project_id,
                            name=node.suggested_name,
                            node_type=node.suggested_type,
                            description=node.suggested_description,
                            status=NodeStatus.DRAFT
                        )
                        created_count += 1
                    except Exception as e:
                        show_warning(f"Could not create '{node.suggested_name}': {str(e)}")
                if created_count > 0:
                    show_success(f"Created {created_count} nodes!")
                st.session_state.detected_nodes = []
                st.rerun()

        with col2:
            if st.button("❌ Dismiss All", help="Dismiss all suggestions"):
                st.session_state.detected_nodes = []
                st.rerun()
