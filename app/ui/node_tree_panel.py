"""
Design Tree Node Panel UI Components.

Provides UI for managing nodes, versions, drafts, and rant summarization.
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional

from app.core.models import Node, NodeVersion, NodeStatus, NodeType, Project
from app.services import (
    get_nodes_by_domain,
    get_draft_nodes,
    get_node_by_id,
    create_node,
    create_node_version,
    get_node_versions,
    get_node_current_version,
    update_node_status,
    update_node_basic_info,
    delete_node,
    commit_draft_node,
    summarize_rant,
    attach_summary_to_node,
    create_node_from_summary,
    get_setting,
)
from app.ui.layout import show_success, show_error, show_warning, show_info


def get_status_badge(status: NodeStatus) -> str:
    """Get a colored badge for node status."""
    badges = {
        NodeStatus.ACTIVE: "🟢 Active",
        NodeStatus.DRAFT: "🟡 Draft",
        NodeStatus.ARCHIVED: "🔵 Archived",
        NodeStatus.DELETED: "🔴 Deleted",
    }
    return badges.get(status, "⚪ Unknown")


def get_type_icon(node_type: NodeType) -> str:
    """Get an icon for node type."""
    icons = {
        NodeType.ROOT: "🌳",
        NodeType.FOLDER: "📁",
        NodeType.COMPONENT: "🧩",
        NodeType.ASSET: "🎨",
        NodeType.NOTE: "📝",
    }
    return icons.get(node_type, "📄")


def render_node_list(
    db: Session,
    project: Project,
    on_select_callback=None
):
    """
    Render the node list grouped by domain.

    Args:
        db: Database session
        project: Current project
        on_select_callback: Optional callback when node is selected
    """
    st.subheader("📂 Nodes by Domain")

    # Search/filter input (Phase 8)
    search_query = st.text_input(
        "🔍 Search nodes",
        placeholder="Filter by title or domain...",
        key="node_search_filter"
    )

    # Get nodes grouped by domain
    domains = get_nodes_by_domain(db, project.id, include_deleted=False)

    if not domains:
        show_info("No nodes yet. Create your first node below!")
        return

    # Filter domains and nodes based on search query
    if search_query:
        search_lower = search_query.lower()
        filtered_domains = {}
        for domain, nodes in domains.items():
            # Filter nodes that match title or domain
            filtered_nodes = [
                node for node in nodes
                if search_lower in node.title.lower() or search_lower in (node.domain or "").lower()
            ]
            if filtered_nodes:
                filtered_domains[domain] = filtered_nodes
        domains = filtered_domains

        if not domains:
            st.info(f"No nodes found matching '{search_query}'")
            return

    # Render each domain
    for domain, nodes in sorted(domains.items()):
        with st.expander(f"**{domain}** ({len(nodes)} nodes)", expanded=True):
            for node in nodes:
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(
                        f"{get_type_icon(node.node_type)} **{node.title}**"
                    )

                with col2:
                    st.markdown(get_status_badge(node.status))

                with col3:
                    if st.button("Edit", key=f"edit_node_{node.id}"):
                        st.session_state.selected_node_id = node.id
                        if on_select_callback:
                            on_select_callback(node.id)


def render_create_node_form(db: Session, project: Project):
    """
    Render form to create a new node.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("➕ Create New Node")

    with st.form("create_node_form"):
        title = st.text_input("Title", placeholder="e.g., User Authentication Module")
        domain = st.text_input("Domain", placeholder="e.g., Backend, Frontend, Design")

        node_type = st.selectbox(
            "Type",
            options=[nt.value for nt in NodeType],
            format_func=lambda x: f"{get_type_icon(NodeType(x))} {x.title()}"
        )

        initial_content = st.text_area(
            "Initial Content",
            placeholder="Add initial notes, requirements, or design thoughts...",
            height=150
        )

        status = st.selectbox(
            "Initial Status",
            options=[NodeStatus.DRAFT.value, NodeStatus.ACTIVE.value],
            index=0
        )

        submit = st.form_submit_button("Create Node", type="primary")

        if submit:
            if not title or not domain:
                show_error("Title and Domain are required")
            else:
                try:
                    node = create_node(
                        db=db,
                        project_id=project.id,
                        title=title,
                        domain=domain,
                        node_type=NodeType(node_type),
                        status=NodeStatus(status),
                        initial_content=initial_content
                    )
                    show_success(f"Node '{node.title}' created successfully!")
                    st.rerun()
                except Exception as e:
                    show_error(f"Failed to create node: {str(e)}")


def render_node_editor(db: Session, node_id: int):
    """
    Render the node editor with version management.

    Args:
        db: Database session
        node_id: Node ID to edit
    """
    node = get_node_by_id(db, node_id)
    if not node:
        show_error("Node not found")
        return

    st.subheader(f"{get_type_icon(node.node_type)} {node.title}")

    # Node info and actions
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.markdown(f"**Domain:** {node.domain}")
        st.markdown(f"**Status:** {get_status_badge(node.status)}")

    with col2:
        st.markdown(f"**Type:** {node.node_type.value.title()}")
        st.markdown(f"**Current Version:** v{node.current_version_number}")

    with col3:
        # Status change buttons
        if node.status == NodeStatus.DRAFT:
            if st.button("✅ Activate", key=f"activate_{node.id}"):
                try:
                    update_node_status(db, node.id, NodeStatus.ACTIVE)
                    show_success("Node activated!")
                    st.rerun()
                except Exception as e:
                    show_error(f"Failed to activate: {str(e)}")

        if st.button("🗑️ Delete", key=f"delete_{node.id}"):
            try:
                delete_node(db, node.id, hard_delete=False)
                show_success("Node deleted")
                st.session_state.selected_node_id = None
                st.rerun()
            except Exception as e:
                show_error(f"Failed to delete: {str(e)}")

    st.divider()

    # Current version display
    current_version = get_node_current_version(db, node.id)

    if current_version:
        st.markdown("### Current Version")
        st.markdown(f"**Summary:** {current_version.summary}")

        with st.expander("View Details", expanded=True):
            st.markdown(current_version.details or "*No details provided*")

        if current_version.change_note:
            st.caption(f"📝 {current_version.change_note}")

    st.divider()

    # New version form
    with st.expander("➕ Create New Version", expanded=False):
        with st.form(f"new_version_form_{node.id}"):
            st.markdown("Create a new version of this node:")

            # Pre-fill with current version data if exists
            default_summary = current_version.summary if current_version else ""
            default_details = current_version.details if current_version else ""

            new_summary = st.text_input(
                "Summary",
                value=default_summary,
                placeholder="Brief summary of this version"
            )

            new_details = st.text_area(
                "Details",
                value=default_details,
                placeholder="Detailed content...",
                height=200
            )

            change_note = st.text_input(
                "Change Note",
                placeholder="What changed in this version?"
            )

            submit_version = st.form_submit_button("Save New Version", type="primary")

            if submit_version:
                if not new_summary:
                    show_error("Summary is required")
                else:
                    try:
                        version = create_node_version(
                            db=db,
                            node_id=node.id,
                            summary=new_summary,
                            details=new_details,
                            change_note=change_note
                        )
                        show_success(f"Version {version.version_number} created!")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to create version: {str(e)}")

    # Version history
    st.markdown("### Version History")
    versions = get_node_versions(db, node.id)

    if versions:
        for version in versions:
            is_current = version.version_number == node.current_version_number
            badge = "✨ **CURRENT**" if is_current else ""

            with st.expander(
                f"v{version.version_number}: {version.summary} {badge}",
                expanded=is_current
            ):
                st.markdown(version.details or "*No details*")
                if version.change_note:
                    st.caption(f"📝 {version.change_note}")
                st.caption(f"Created: {version.created_at.strftime('%Y-%m-%d %H:%M')}")
    else:
        show_info("No version history")


def render_edit_node_basic_info(db: Session, node_id: int):
    """
    Render form to edit node basic information.

    Args:
        db: Database session
        node_id: Node ID
    """
    node = get_node_by_id(db, node_id)
    if not node:
        return

    with st.expander("✏️ Edit Node Info"):
        with st.form(f"edit_node_info_{node.id}"):
            new_title = st.text_input("Title", value=node.title)
            new_domain = st.text_input("Domain", value=node.domain)

            submit = st.form_submit_button("Update Info")

            if submit:
                try:
                    update_node_basic_info(
                        db=db,
                        node_id=node.id,
                        title=new_title,
                        domain=new_domain
                    )
                    show_success("Node info updated!")
                    st.rerun()
                except Exception as e:
                    show_error(f"Failed to update: {str(e)}")


def render_drafts_tab(db: Session, project: Project):
    """
    Render the drafts management tab.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("📝 Draft Nodes")

    drafts = get_draft_nodes(db, project.id)

    if not drafts:
        show_info("No draft nodes. All nodes are active or archived.")
        return

    st.markdown(f"**{len(drafts)} draft(s) pending review**")

    for draft in drafts:
        with st.expander(
            f"{get_type_icon(draft.node_type)} **{draft.title}** ({draft.domain})"
        ):
            current_version = get_node_current_version(db, draft.id)

            if current_version:
                st.markdown(f"**Summary:** {current_version.summary}")
                st.markdown(f"**Details:**\n{current_version.details or '*No details*'}")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Commit", key=f"commit_draft_{draft.id}"):
                    try:
                        commit_draft_node(db, draft.id)
                        show_success(f"'{draft.title}' committed to active!")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to commit: {str(e)}")

            with col2:
                if st.button("✏️ Edit", key=f"edit_draft_{draft.id}"):
                    st.session_state.selected_node_id = draft.id
                    st.rerun()

            with col3:
                if st.button("🗑️ Discard", key=f"discard_draft_{draft.id}"):
                    try:
                        delete_node(db, draft.id, hard_delete=True)
                        show_success("Draft discarded")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to discard: {str(e)}")


def render_rant_summary_tab(db: Session, project: Project):
    """
    Render the rant-to-summary tab with OpenAI summarization.

    Args:
        db: Database session
        project: Current project
    """
    st.subheader("💭 Rant → Summary")

    st.markdown(
        """
        Dump your raw design thoughts here. AI will organize them into structured documentation
        that you can edit and attach to a node.
        """
    )

    # Rant input
    rant_text = st.text_area(
        "Raw Design Rant",
        placeholder="Just start typing your thoughts, ideas, requirements, or concerns...\n\n"
        "Don't worry about structure or grammar - the AI will organize it for you!",
        height=250,
        key="rant_input"
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        summarize_btn = st.button("✨ Summarize", type="primary", disabled=not rant_text)

    # Summarize button action
    if summarize_btn and rant_text:
        try:
            # Get API key and model from settings
            api_key = get_setting(db, "OPENAI_API_KEY")
            summary_model = get_setting(db, "DEFAULT_SUMMARY_MODEL") or "gpt-4-turbo-preview"

            with st.spinner("AI is organizing your thoughts..."):
                summary, details = summarize_rant(
                    rant_text=rant_text,
                    openai_api_key=api_key,
                    summary_model=summary_model
                )

                # Store in session state
                st.session_state.rant_summary = summary
                st.session_state.rant_details = details

            show_success("Summary generated!")

        except Exception as e:
            show_error(f"Summarization failed: {str(e)}")

    # Display and edit summary
    if "rant_summary" in st.session_state and st.session_state.rant_summary:
        st.divider()
        st.markdown("### Generated Summary")

        # Editable summary
        edited_summary = st.text_input(
            "Summary",
            value=st.session_state.rant_summary,
            key="edited_summary"
        )

        edited_details = st.text_area(
            "Details",
            value=st.session_state.rant_details,
            height=300,
            key="edited_details"
        )

        st.divider()
        st.markdown("### Save to Node")

        # Option 1: Attach to existing node
        with st.expander("📎 Attach to Existing Node"):
            nodes = get_nodes_by_domain(db, project.id, include_deleted=False)
            all_nodes = []
            for domain_nodes in nodes.values():
                all_nodes.extend(domain_nodes)

            if all_nodes:
                node_options = {
                    f"{node.domain} / {node.title}": node.id
                    for node in all_nodes
                }

                selected_node = st.selectbox(
                    "Select Node",
                    options=list(node_options.keys())
                )

                change_note = st.text_input(
                    "Change Note",
                    value="Added from rant summary"
                )

                if st.button("Attach to Node", key="attach_to_node"):
                    try:
                        node_id = node_options[selected_node]
                        version = attach_summary_to_node(
                            db=db,
                            node_id=node_id,
                            summary=edited_summary,
                            details=edited_details,
                            change_note=change_note
                        )
                        show_success(
                            f"Summary attached to '{selected_node}' as version {version.version_number}!"
                        )
                        # Clear session state
                        del st.session_state.rant_summary
                        del st.session_state.rant_details
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to attach: {str(e)}")
            else:
                show_info("No existing nodes. Create a new node below.")

        # Option 2: Create new node
        with st.expander("➕ Create New Node from Summary"):
            with st.form("create_from_rant"):
                new_title = st.text_input(
                    "Node Title",
                    placeholder="e.g., API Rate Limiting Strategy"
                )

                new_domain = st.text_input(
                    "Domain",
                    placeholder="e.g., Backend, Architecture"
                )

                new_type = st.selectbox(
                    "Type",
                    options=[nt.value for nt in NodeType],
                    index=2  # Default to COMPONENT
                )

                new_status = st.selectbox(
                    "Status",
                    options=[NodeStatus.DRAFT.value, NodeStatus.ACTIVE.value],
                    index=0  # Default to DRAFT
                )

                submit_new = st.form_submit_button("Create Node", type="primary")

                if submit_new:
                    if not new_title or not new_domain:
                        show_error("Title and Domain are required")
                    else:
                        try:
                            node = create_node_from_summary(
                                db=db,
                                project_id=project.id,
                                title=new_title,
                                domain=new_domain,
                                summary=edited_summary,
                                details=edited_details,
                                node_type=NodeType(new_type),
                                status=NodeStatus(new_status)
                            )
                            show_success(f"Node '{node.title}' created from summary!")
                            # Clear session state
                            del st.session_state.rant_summary
                            del st.session_state.rant_details
                            st.rerun()
                        except Exception as e:
                            show_error(f"Failed to create node: {str(e)}")


def render_design_tree_panel(db: Session, project: Project):
    """
    Main entry point for the Design Tree panel.

    Args:
        db: Database session
        project: Current project
    """
    # Create sub-tabs for different views
    tree_tab, drafts_tab, rant_tab = st.tabs(
        ["🌳 Node Tree", "📝 Drafts", "💭 Rant → Summary"]
    )

    with tree_tab:
        # Check if editing a specific node
        if "selected_node_id" in st.session_state and st.session_state.selected_node_id:
            node_id = st.session_state.selected_node_id

            # Back button
            if st.button("← Back to Node List"):
                st.session_state.selected_node_id = None
                st.rerun()

            # Render node editor
            render_node_editor(db, node_id)
            render_edit_node_basic_info(db, node_id)

        else:
            # Show node list and create form
            col1, col2 = st.columns([2, 1])

            with col1:
                render_node_list(db, project)

            with col2:
                render_create_node_form(db, project)

    with drafts_tab:
        render_drafts_tab(db, project)

    with rant_tab:
        render_rant_summary_tab(db, project)
