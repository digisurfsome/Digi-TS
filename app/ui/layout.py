"""
UI layout components and helpers for Streamlit.

This module provides reusable UI components and layout functions.
"""

import streamlit as st
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session

from app.core.models import UserProfile, Project
from app.services import (
    list_all_users,
    list_user_projects,
    create_project,
    get_all_settings,
    set_multiple_settings,
    get_project_context,
    update_project_context,
)


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
        # TODO: Add navigation menu in later phases
        st.info("Navigation menu will be added in later phases")


def render_footer() -> None:
    """Render application footer."""
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; padding: 1rem;'>
            <small>Design Tree Studio v0.1.0</small>
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

    col1, col2 = st.columns([3, 1])

    with col1:
        if not projects:
            st.info("No projects found. Create your first project!")
            return None, True

        project_options = {f"{p.name}": p for p in projects}
        project_options["+ Create New Project"] = None

        project_names = list(project_options.keys())

        # Initialize session state
        if "selected_project_name" not in st.session_state or st.session_state.selected_project_name not in project_names:
            st.session_state.selected_project_name = project_names[0] if project_names else None

        selected_name = st.selectbox(
            "Select Project",
            project_names,
            key="project_selector",
            index=project_names.index(st.session_state.selected_project_name) if st.session_state.selected_project_name in project_names else 0
        )

        st.session_state.selected_project_name = selected_name

        if selected_name == "+ Create New Project":
            return None, True

        return project_options[selected_name], False

    with col2:
        if st.button("➕ New", help="Create a new project"):
            return None, True

    return None, False


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

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Manual Description")
        st.caption("Describe your project, design system, and guidelines.")

    with col2:
        if st.button("💾 Save Context"):
            st.session_state.save_context_clicked = True

    # Manual description editor
    manual_desc = st.text_area(
        "Manual Description",
        value=context.content if context else "",
        height=300,
        label_visibility="collapsed",
        help="Enter project context, design guidelines, constraints, etc."
    )

    # Save context if button was clicked
    if st.session_state.get("save_context_clicked"):
        try:
            update_project_context(db, project.id, manual_desc)
            show_success("Project context saved successfully!")
            st.session_state.save_context_clicked = False
            st.rerun()
        except Exception as e:
            show_error(f"Failed to save context: {str(e)}")

    st.divider()

    # Auto description (placeholder for now)
    st.markdown("#### Auto Description")
    st.caption("AI-generated summary of your project state.")

    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.info("Auto-description will be generated from project nodes and activity.")

        with col2:
            if st.button("🔄 Regenerate", help="Generate fresh auto-description"):
                show_info("Auto-description generation will be implemented in a future phase.")

        # Placeholder for auto-generated content
        st.text_area(
            "Auto-generated description",
            value="(Auto-description not yet implemented)",
            height=150,
            disabled=True,
            label_visibility="collapsed"
        )
