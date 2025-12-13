"""
Idea Bank Panel UI Components.

Provides UI for Phase 5 Idea Bank functionality including:
- Daily Warmup modal
- Idea Bank tab with filtering/sorting
- Quick add interface
- Rating and categorization controls
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.core.models import Project, Idea, IdeaCategory, IdeaSource, IdeaStatus
from app.ui.layout import show_success, show_error, show_warning, show_info
from app.services.idea_bank_service import (
    create_idea,
    list_ideas,
    update_idea,
    retire_idea,
    archive_idea,
    reactivate_idea,
    delete_idea,
    get_warmup_ideas,
    mark_ideas_shown,
    get_idea_stats,
    quick_add_from_text,
    detect_valuable_ideas,
    get_category_icon,
    get_status_icon,
    render_star_rating,
    format_idea_for_display,
)
from app.services.session_service import (
    needs_warmup,
    complete_warmup,
)


# ============================================================================
# DAILY WARMUP MODAL (Mechanism 11)
# ============================================================================


def render_warmup_modal(
    db: Session,
    project_id: int,
    user_id: int,
) -> bool:
    """
    Render the Daily Warmup modal on login.

    Shows top ideas from the Idea Bank as a daily practice
    to build confidence before starting work.

    Args:
        db: Database session
        project_id: Current project ID
        user_id: Current user ID

    Returns:
        True if user dismissed the warmup (ready to work)
    """
    # Check if warmup needed
    if not needs_warmup(db, user_id, project_id):
        return True

    # Get warmup ideas
    ideas = get_warmup_ideas(db, project_id, user_id, max_ideas=5)

    if not ideas:
        # No ideas yet - skip warmup
        complete_warmup(db, user_id, project_id)
        return True

    # Show warmup modal
    st.markdown("""
    <style>
    .warmup-container {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        border: 2px solid #3b82f6;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .warmup-title {
        font-size: 24px;
        font-weight: bold;
        color: #fbbf24;
        margin-bottom: 8px;
    }
    .warmup-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 24px;
    }
    .idea-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 4px solid #3b82f6;
    }
    .idea-content {
        font-size: 16px;
        color: #f1f5f9;
        font-style: italic;
        margin-bottom: 8px;
    }
    .idea-meta {
        font-size: 12px;
        color: #64748b;
        display: flex;
        gap: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="warmup-container">
        <div class="warmup-title">Daily Warmup</div>
        <div class="warmup-subtitle">Review your best ideas to build confidence before starting work</div>
    </div>
    """, unsafe_allow_html=True)

    # Display ideas
    for idea in ideas:
        category_icon = get_category_icon(idea.category)
        stars = render_star_rating(idea.rating)

        st.markdown(f"""
        <div class="idea-card">
            <div class="idea-content">"{idea.content}"</div>
            <div class="idea-meta">
                <span>{stars}</span>
                <span>{category_icon} {idea.category.value.title()}</span>
                <span>Shown {idea.times_shown}x</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")  # Spacing

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button(
            "Got it - Start Working",
            type="primary",
            key="warmup_dismiss",
            use_container_width=True,
        ):
            # Mark ideas as shown
            idea_ids = [idea.id for idea in ideas]
            mark_ideas_shown(db, idea_ids)

            # Complete warmup
            complete_warmup(db, user_id, project_id)

            return True

    with col2:
        if st.button(
            "Add New Idea",
            key="warmup_add_idea",
            use_container_width=True,
        ):
            st.session_state.show_quick_add = True
            st.rerun()

    with col3:
        if st.button(
            "Skip Today",
            key="warmup_skip",
            use_container_width=True,
        ):
            complete_warmup(db, user_id, project_id)
            return True

    # Quick add form (if triggered)
    if st.session_state.get("show_quick_add", False):
        with st.expander("Add New Idea", expanded=True):
            render_quick_add_form(db, project_id, user_id)

    return False


# ============================================================================
# IDEA BANK TAB
# ============================================================================


def render_idea_bank_panel(
    db: Session,
    project: Project,
    user_id: int,
) -> None:
    """
    Render the complete Idea Bank panel.

    Provides:
    - Stats overview
    - Filter and sort controls
    - Idea list with actions
    - Add new idea form

    Args:
        db: Database session
        project: Current project
        user_id: Current user ID
    """
    st.markdown("## Idea Bank")
    st.caption("Your best ideas, reviewed daily until they're in your DNA.")

    # Get stats
    stats = get_idea_stats(db, project.id, user_id)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Ideas", stats["active"])

    with col2:
        st.metric("Retired (Learned)", stats["retired"])

    with col3:
        st.metric("Avg Rating", f"{stats['avg_rating']}/5")

    with col4:
        st.metric("Times Reviewed", stats["total_times_shown"])

    st.divider()

    # Tab navigation
    tabs = st.tabs([
        "Active",
        "Add New",
        "Retired",
        "Archived",
        "AI Detect",
    ])

    with tabs[0]:
        render_idea_list(
            db, project.id, user_id,
            status_filter=IdeaStatus.ACTIVE,
        )

    with tabs[1]:
        render_add_idea_form(db, project.id, user_id)

    with tabs[2]:
        render_idea_list(
            db, project.id, user_id,
            status_filter=IdeaStatus.RETIRED,
        )

    with tabs[3]:
        render_idea_list(
            db, project.id, user_id,
            status_filter=IdeaStatus.ARCHIVED,
        )

    with tabs[4]:
        render_ai_detect_section(db, project.id, user_id)


# ============================================================================
# IDEA LIST
# ============================================================================


def render_idea_list(
    db: Session,
    project_id: int,
    user_id: int,
    status_filter: Optional[IdeaStatus] = None,
) -> None:
    """
    Render a filterable list of ideas.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        status_filter: Optional status filter
    """
    # Filter controls
    col1, col2, col3 = st.columns(3)

    with col1:
        category_options = ["All"] + [c.value.title() for c in IdeaCategory]
        selected_category = st.selectbox(
            "Category",
            options=category_options,
            key=f"filter_category_{status_filter.value if status_filter else 'all'}",
        )

    with col2:
        min_rating = st.selectbox(
            "Minimum Rating",
            options=["Any", "1+", "2+", "3+", "4+", "5"],
            key=f"filter_rating_{status_filter.value if status_filter else 'all'}",
        )

    with col3:
        sort_by = st.selectbox(
            "Sort By",
            options=["Rating (High to Low)", "Times Shown (Low to High)", "Newest First"],
            key=f"sort_by_{status_filter.value if status_filter else 'all'}",
        )

    # Build query
    category = None
    if selected_category != "All":
        category = IdeaCategory(selected_category.lower())

    rating_value = None
    if min_rating != "Any":
        rating_value = int(min_rating.replace("+", ""))

    # Get ideas
    ideas = list_ideas(
        db, project_id, user_id,
        status=status_filter,
        category=category,
        min_rating=rating_value,
    )

    if not ideas:
        if status_filter == IdeaStatus.ACTIVE:
            st.info("No active ideas yet. Add some ideas to build your daily warmup!")
        elif status_filter == IdeaStatus.RETIRED:
            st.info("No retired ideas yet. Retire ideas once you've internalized them.")
        elif status_filter == IdeaStatus.ARCHIVED:
            st.info("No archived ideas.")
        else:
            st.info("No ideas found with these filters.")
        return

    # Display ideas
    for idea in ideas:
        render_idea_card(db, idea, status_filter)


def render_idea_card(
    db: Session,
    idea: Idea,
    current_status: Optional[IdeaStatus] = None,
) -> None:
    """
    Render a single idea card with actions.

    Args:
        db: Database session
        idea: Idea to display
        current_status: Current status filter context
    """
    category_icon = get_category_icon(idea.category)
    status_icon = get_status_icon(idea.status)

    # Card container
    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            # Rating stars
            stars = render_star_rating(idea.rating)
            st.markdown(f"**{stars}**")

            # Content
            st.markdown(f'*"{idea.content}"*')

            # Meta info
            meta_parts = [
                f"{category_icon} {idea.category.value.title()}",
                f"{status_icon} {idea.status.value.title()}",
                f"Shown {idea.times_shown}x",
            ]
            if idea.source != IdeaSource.MANUAL:
                meta_parts.append(f"Source: {idea.source.value}")

            st.caption(" | ".join(meta_parts))

        with col2:
            # Action buttons based on status
            if idea.status == IdeaStatus.ACTIVE:
                if st.button("Retire", key=f"retire_{idea.id}", help="Mark as learned"):
                    retire_idea(db, idea.id)
                    show_success("Idea retired!")
                    st.rerun()

                if st.button("Archive", key=f"archive_{idea.id}", help="Remove from bank"):
                    archive_idea(db, idea.id)
                    show_info("Idea archived")
                    st.rerun()

            elif idea.status == IdeaStatus.RETIRED:
                if st.button("Reactivate", key=f"reactivate_{idea.id}"):
                    reactivate_idea(db, idea.id)
                    show_success("Idea reactivated!")
                    st.rerun()

            elif idea.status == IdeaStatus.ARCHIVED:
                if st.button("Restore", key=f"restore_{idea.id}"):
                    reactivate_idea(db, idea.id)
                    show_success("Idea restored!")
                    st.rerun()

                if st.button("Delete", key=f"delete_{idea.id}", type="secondary"):
                    delete_idea(db, idea.id)
                    show_info("Idea deleted")
                    st.rerun()

        # Expandable edit section
        with st.expander("Edit", expanded=False):
            render_idea_edit_form(db, idea)

        st.divider()


def render_idea_edit_form(db: Session, idea: Idea) -> None:
    """
    Render inline edit form for an idea.

    Args:
        db: Database session
        idea: Idea to edit
    """
    with st.form(f"edit_idea_{idea.id}"):
        new_content = st.text_area(
            "Content",
            value=idea.content,
            key=f"edit_content_{idea.id}",
        )

        col1, col2 = st.columns(2)

        with col1:
            category_options = [c.value for c in IdeaCategory]
            new_category = st.selectbox(
                "Category",
                options=category_options,
                index=category_options.index(idea.category.value),
                key=f"edit_category_{idea.id}",
            )

        with col2:
            new_rating = st.slider(
                "Rating",
                min_value=1,
                max_value=5,
                value=idea.rating,
                key=f"edit_rating_{idea.id}",
            )

        if st.form_submit_button("Save Changes"):
            update_idea(
                db, idea.id,
                content=new_content,
                category=IdeaCategory(new_category),
                rating=new_rating,
            )
            show_success("Idea updated!")
            st.rerun()


# ============================================================================
# ADD IDEA FORMS
# ============================================================================


def render_add_idea_form(
    db: Session,
    project_id: int,
    user_id: int,
) -> None:
    """
    Render the full add idea form.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
    """
    st.markdown("### Add New Idea")
    st.caption("Capture an idea to review daily until it's internalized.")

    with st.form("add_idea_form"):
        content = st.text_area(
            "Idea Content",
            placeholder="Enter your idea, insight, or pattern...",
            help="Keep it concise and memorable - 1-2 sentences is ideal",
        )

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox(
                "Category",
                options=[c.value.title() for c in IdeaCategory],
                help="""
                **Vision**: High-level project direction
                **Feature**: Specific feature ideas
                **Insight**: Key realizations
                **Pattern**: Recurring approaches
                """,
            )

        with col2:
            rating = st.slider(
                "Importance (1-5 stars)",
                min_value=1,
                max_value=5,
                value=3,
                help="5 = core vision, 1 = minor detail",
            )

        tags = st.text_input(
            "Tags (optional, comma-separated)",
            placeholder="e.g., ui, performance, mvp",
        )

        submitted = st.form_submit_button("Add to Idea Bank", type="primary")

        if submitted:
            if not content or not content.strip():
                show_error("Please enter idea content")
            else:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

                create_idea(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    content=content.strip(),
                    category=IdeaCategory(category.lower()),
                    source=IdeaSource.MANUAL,
                    rating=rating,
                    tags=tag_list,
                )
                show_success("Idea added to your bank!")
                st.rerun()


def render_quick_add_form(
    db: Session,
    project_id: int,
    user_id: int,
    default_text: str = "",
    source_ref: Optional[str] = None,
) -> None:
    """
    Render a compact quick-add form (for use in modals/popovers).

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        default_text: Pre-filled text (e.g., selected rant text)
        source_ref: Reference to source content
    """
    with st.form("quick_add_idea"):
        content = st.text_area(
            "Idea",
            value=default_text,
            height=100,
        )

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox(
                "Category",
                options=[c.value.title() for c in IdeaCategory],
                index=2,  # Default to Insight
            )

        with col2:
            rating = st.select_slider(
                "Rating",
                options=[1, 2, 3, 4, 5],
                value=3,
            )

        if st.form_submit_button("Add to Bank", type="primary"):
            if content and content.strip():
                create_idea(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    content=content.strip(),
                    category=IdeaCategory(category.lower()),
                    source=IdeaSource.RANT if source_ref else IdeaSource.MANUAL,
                    rating=rating,
                    source_ref=source_ref,
                )
                show_success("Idea added!")
                st.session_state.show_quick_add = False
                st.rerun()
            else:
                show_error("Please enter idea content")


# ============================================================================
# AI DETECT SECTION
# ============================================================================


def render_ai_detect_section(
    db: Session,
    project_id: int,
    user_id: int,
) -> None:
    """
    Render AI idea detection section.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
    """
    st.markdown("### AI Idea Detection")
    st.caption("Let AI find valuable ideas in your rant content.")

    st.markdown("""
    Paste or enter text content and AI will extract valuable ideas
    that are worth adding to your daily warmup.
    """)

    content = st.text_area(
        "Content to Analyze",
        height=200,
        placeholder="Paste rant content, notes, or any text to analyze...",
        key="ai_detect_content",
    )

    if st.button("Detect Ideas", type="primary", disabled=not content):
        with st.spinner("Analyzing content..."):
            ideas = detect_valuable_ideas(
                db=db,
                project_id=project_id,
                user_id=user_id,
                rant_content=content,
            )

            if ideas:
                show_success(f"Found and added {len(ideas)} ideas!")

                st.markdown("**Detected Ideas:**")
                for idea in ideas:
                    category_icon = get_category_icon(idea.category)
                    stars = render_star_rating(idea.rating)
                    st.markdown(f"""
                    - {stars} {category_icon} *"{idea.content}"*
                    """)

                st.rerun()
            else:
                show_warning("No valuable ideas detected in this content.")


# ============================================================================
# QUICK ADD BUTTON (For Rant Panels)
# ============================================================================


def render_quick_add_button(
    selected_text: str,
    key_suffix: str = "",
) -> bool:
    """
    Render a quick-add button that appears when text is selected.

    Args:
        selected_text: The selected text to add
        key_suffix: Unique key suffix for multiple instances

    Returns:
        True if button was clicked
    """
    if st.button(
        "Add to Idea Bank",
        key=f"quick_add_btn_{key_suffix}",
        help="Save this to your Idea Bank for daily review",
    ):
        st.session_state.quick_add_text = selected_text
        st.session_state.show_quick_add_modal = True
        return True

    return False


def render_quick_add_modal(
    db: Session,
    project_id: int,
    user_id: int,
) -> None:
    """
    Render the quick-add modal when triggered.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
    """
    if not st.session_state.get("show_quick_add_modal", False):
        return

    selected_text = st.session_state.get("quick_add_text", "")

    with st.expander("Add to Idea Bank", expanded=True):
        render_quick_add_form(
            db=db,
            project_id=project_id,
            user_id=user_id,
            default_text=selected_text,
            source_ref="rant_selection",
        )

        if st.button("Cancel", key="cancel_quick_add"):
            st.session_state.show_quick_add_modal = False
            st.session_state.quick_add_text = ""
            st.rerun()


# ============================================================================
# WARMUP STATUS INDICATOR
# ============================================================================


def render_warmup_status_indicator(
    db: Session,
    project_id: int,
    user_id: int,
) -> None:
    """
    Render a compact warmup status indicator.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
    """
    if needs_warmup(db, user_id, project_id):
        st.markdown("""
        <div style="
            background: #fbbf24;
            color: #1e293b;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        ">
            Warmup Pending
        </div>
        """, unsafe_allow_html=True)
    else:
        stats = get_idea_stats(db, project_id, user_id)
        st.markdown(f"""
        <div style="
            background: #059669;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            display: inline-block;
        ">
            {stats['active']} Active Ideas
        </div>
        """, unsafe_allow_html=True)
