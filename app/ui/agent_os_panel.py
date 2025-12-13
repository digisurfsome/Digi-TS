"""
Agent OS Panel UI Components.

Provides UI for viewing, generating, and exporting Agent OS documents.
Includes live tree view of Agent OS structure and consolidation features.
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.core.models import Project, ChatMessage
from app.services import (
    get_setting,
    get_all_settings,
    get_chat_history,
    save_raw_rant,
    get_raw_rants,
)
from app.services.agent_os_service import (
    AgentOSDocument,
    AgentOSSection,
    AgentOSSubsection,
    ClassifiedItem,
    classify_text,
    generate_agent_os_from_rant,
    create_empty_template,
    get_section_icon,
    get_subsection_icon,
    get_classification_summary,
)
from app.ui.layout import show_success, show_error, show_warning, show_info


def render_agent_os_tree(doc: AgentOSDocument) -> None:
    """
    Render the Agent OS document as an interactive tree view.

    Args:
        doc: AgentOSDocument to display
    """
    st.markdown(f"### {get_section_icon(AgentOSSection.STANDARDS)} STANDARDS LAYER")

    # Tech Stack
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.TECH_STACK)} Technology Stack ({len(doc.tech_stack)} items)",
        expanded=bool(doc.tech_stack)
    ):
        if doc.tech_stack:
            for item in doc.tech_stack:
                st.markdown(f"- {item}")
        else:
            st.caption("*(No technology decisions captured yet)*")

    # Architecture
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.ARCHITECTURE)} Architecture ({len(doc.architecture)} items)",
        expanded=bool(doc.architecture)
    ):
        if doc.architecture:
            for item in doc.architecture:
                st.markdown(f"- {item}")
        else:
            st.caption("*(No architectural decisions captured yet)*")

    # Coding Patterns
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.CODING_PATTERNS)} Coding Patterns ({len(doc.coding_patterns)} items)",
        expanded=bool(doc.coding_patterns)
    ):
        if doc.coding_patterns:
            for item in doc.coding_patterns:
                st.markdown(f"- {item}")
        else:
            st.caption("*(No coding patterns captured yet)*")

    st.divider()

    st.markdown(f"### {get_section_icon(AgentOSSection.PRODUCT)} PRODUCT LAYER")

    # Vision
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.VISION)} Vision {'(Defined)' if doc.vision else '(Empty)'}",
        expanded=bool(doc.vision)
    ):
        if doc.vision:
            st.markdown(doc.vision)
        else:
            st.caption("*(No vision statement captured yet)*")

    # Target Users
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.TARGET_USERS)} Target Users ({len(doc.target_users)} defined)",
        expanded=bool(doc.target_users)
    ):
        if doc.target_users:
            for user in doc.target_users:
                st.markdown(f"- {user}")
        else:
            st.caption("*(No target users defined yet)*")

    # Use Cases
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.USE_CASES)} Use Cases ({len(doc.use_cases)} defined)",
        expanded=bool(doc.use_cases)
    ):
        if doc.use_cases:
            for i, uc in enumerate(doc.use_cases, 1):
                st.markdown(f"{i}. {uc}")
        else:
            st.caption("*(No use cases defined yet)*")

    # Roadmap
    roadmap_count = sum(len(v) for v in doc.roadmap.values())
    with st.expander(
        f"{get_subsection_icon(AgentOSSubsection.ROADMAP)} Roadmap ({roadmap_count} items)",
        expanded=roadmap_count > 0
    ):
        if doc.roadmap.get("phase_1"):
            st.markdown("**Phase 1 (Current):**")
            for item in doc.roadmap["phase_1"]:
                st.markdown(f"- {item}")
        if doc.roadmap.get("phase_2"):
            st.markdown("**Phase 2 (Next):**")
            for item in doc.roadmap["phase_2"]:
                st.markdown(f"- {item}")
        if doc.roadmap.get("future"):
            st.markdown("**Future:**")
            for item in doc.roadmap["future"]:
                st.markdown(f"- {item}")
        if roadmap_count == 0:
            st.caption("*(No roadmap items captured yet)*")

    st.divider()

    st.markdown(f"### {get_section_icon(AgentOSSection.SPECS)} SPEC LAYER")

    # Features
    if doc.features:
        for feature in doc.features:
            feature_name = feature.get("name", "Unnamed Feature")
            func_count = len(feature.get("requirements_functional", []))
            tech_count = len(feature.get("requirements_technical", []))

            with st.expander(
                f"**Feature: {feature_name}** ({func_count} functional, {tech_count} technical reqs)",
                expanded=True
            ):
                if feature.get("overview"):
                    st.markdown(f"**Overview:** {feature['overview']}")

                if feature.get("requirements_functional"):
                    st.markdown("**Functional Requirements:**")
                    for req in feature["requirements_functional"]:
                        st.markdown(f"- {req}")

                if feature.get("requirements_technical"):
                    st.markdown("**Technical Requirements:**")
                    for req in feature["requirements_technical"]:
                        st.markdown(f"- {req}")

                if feature.get("user_stories"):
                    st.markdown("**User Stories:**")
                    for story in feature["user_stories"]:
                        st.markdown(f"- {story}")

                if feature.get("acceptance_criteria"):
                    st.markdown("**Acceptance Criteria:**")
                    for criterion in feature["acceptance_criteria"]:
                        st.checkbox(criterion, key=f"ac_{feature_name}_{criterion[:20]}", disabled=True)

                if feature.get("technical_spec"):
                    st.markdown("**Technical Spec:**")
                    tech_spec = feature["technical_spec"]
                    if tech_spec.get("api_endpoints"):
                        st.markdown(f"- API: {tech_spec['api_endpoints']}")
                    if tech_spec.get("data_models"):
                        st.markdown(f"- Data: {tech_spec['data_models']}")
                    if tech_spec.get("dependencies"):
                        st.markdown(f"- Dependencies: {tech_spec['dependencies']}")
                    if tech_spec.get("edge_cases"):
                        st.markdown(f"- Edge Cases: {tech_spec['edge_cases']}")

                if feature.get("success_metrics"):
                    st.markdown(f"**Success Metrics:** {feature['success_metrics']}")
    else:
        st.caption("*(No features defined yet)*")

    st.divider()

    st.markdown(f"### {get_section_icon(AgentOSSection.GAPS)} GAPS / QUESTIONS")

    if doc.questions:
        for q in doc.questions:
            st.checkbox(q, key=f"gap_{q[:20]}", disabled=True)
    else:
        st.caption("*(No gaps or questions identified yet)*")

    # Completion meter
    st.divider()
    st.markdown(f"### Completion: {doc.completion_percentage}%")
    st.progress(doc.completion_percentage / 100)


def render_live_classification(items: List[ClassifiedItem]) -> None:
    """
    Render real-time classification results.

    Args:
        items: List of classified items
    """
    if not items:
        return

    summary = get_classification_summary(items)

    st.markdown("#### Classification Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            f"{get_section_icon(AgentOSSection.STANDARDS)} Standards",
            summary.get("standards", 0)
        )
    with col2:
        st.metric(
            f"{get_section_icon(AgentOSSection.PRODUCT)} Product",
            summary.get("product", 0)
        )
    with col3:
        st.metric(
            f"{get_section_icon(AgentOSSection.SPECS)} Specs",
            summary.get("specs", 0)
        )
    with col4:
        st.metric(
            f"{get_section_icon(AgentOSSection.GAPS)} Gaps",
            summary.get("gaps", 0)
        )

    # Show recent classifications
    with st.expander("Recent Classifications", expanded=False):
        for item in items[-10:]:  # Show last 10
            icon = get_subsection_icon(item.subsection)
            confidence_bar = "●" * int(item.confidence * 5) + "○" * (5 - int(item.confidence * 5))
            st.markdown(
                f"{icon} **{item.subsection.value.replace('_', ' ').title()}** "
                f"({confidence_bar})\n\n"
                f"> {item.text[:100]}..."
            )
            st.caption(f"*{item.reasoning}*")
            st.divider()


def render_consolidate_button(
    db: Session,
    project: Project,
    session_id: Optional[int] = None
) -> Optional[AgentOSDocument]:
    """
    Render the consolidate button and handle Agent OS generation.

    Args:
        db: Database session
        project: Current project
        session_id: Optional chat session ID

    Returns:
        Generated AgentOSDocument or None
    """
    st.subheader("Generate Agent OS Document")

    st.markdown(
        """
        Click **Consolidate** to analyze your conversation and generate
        a structured Agent OS specification document.
        """
    )

    # Get conversation text
    conversation_text = ""
    if session_id:
        messages = get_chat_history(db, session_id)
        if messages:
            for msg in messages:
                if not msg.is_warmup and msg.role.value != "system":
                    role = "User" if msg.role.value == "user" else "AI"
                    conversation_text += f"{role}: {msg.content}\n\n"

    # Show conversation stats
    if conversation_text:
        word_count = len(conversation_text.split())
        st.info(f"Conversation contains ~{word_count} words to analyze")
    else:
        st.warning("No conversation found. Start chatting to generate content!")

    # Manual input option
    with st.expander("Or paste raw text manually"):
        manual_input = st.text_area(
            "Raw rant/brainstorm text",
            placeholder="Paste your raw thoughts, ideas, requirements here...",
            height=200,
            key="manual_rant_input"
        )
        if manual_input:
            conversation_text = manual_input

    # Project name override
    project_name = st.text_input(
        "Agent OS Name",
        value=project.name if project else "My Project",
        key="agent_os_name"
    )

    col1, col2 = st.columns([1, 3])

    with col1:
        consolidate_btn = st.button(
            "Consolidate",
            type="primary",
            disabled=not conversation_text,
            use_container_width=True
        )

    if consolidate_btn and conversation_text:
        settings = get_all_settings(db)
        api_key = settings.get("OPENAI_API_KEY", "")
        model = settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")

        if not api_key:
            show_error("OpenAI API key not configured. Please set it in Settings.")
            return None

        with st.spinner("Analyzing conversation and generating Agent OS document..."):
            try:
                doc = generate_agent_os_from_rant(
                    rant_text=conversation_text,
                    openai_api_key=api_key,
                    project_name=project_name,
                    model=model
                )

                # Save raw rant to database (SACRED - never modified)
                try:
                    save_raw_rant(
                        db=db,
                        project_id=project.id,
                        content=conversation_text,
                        session_id=session_id,
                        source_type="manual" if manual_input else "chat",
                        agent_os_doc=doc.to_dict()
                    )
                except Exception as save_err:
                    # Don't fail the whole operation if save fails
                    show_warning(f"Could not save raw rant: {save_err}")

                # Store in session state
                st.session_state.agent_os_doc = doc
                st.session_state.agent_os_doc_dict = doc.to_dict()

                show_success(f"Agent OS document generated! ({doc.completion_percentage}% complete)")
                return doc

            except Exception as e:
                show_error(f"Failed to generate Agent OS: {str(e)}")
                return None

    return None


def render_export_options(doc: AgentOSDocument) -> None:
    """
    Render export options for Agent OS document.

    Args:
        doc: AgentOSDocument to export
    """
    st.subheader("Export Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download as markdown
        markdown_content = doc.to_markdown()
        filename = f"agent_os_{doc.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"

        st.download_button(
            label="Download Markdown",
            data=markdown_content,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True
        )

    with col2:
        # Copy to clipboard (via code block)
        if st.button("View Full Document", use_container_width=True):
            st.session_state.show_full_doc = True

    with col3:
        # Download as JSON
        import json
        json_content = json.dumps(doc.to_dict(), indent=2)
        json_filename = f"agent_os_{doc.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"

        st.download_button(
            label="Download JSON",
            data=json_content,
            file_name=json_filename,
            mime="application/json",
            use_container_width=True
        )

    # Show full document if requested
    if st.session_state.get("show_full_doc"):
        st.divider()
        st.markdown("### Full Agent OS Document")
        st.markdown("*Copy from below:*")
        st.code(doc.to_markdown(), language="markdown")

        if st.button("Hide Full Document"):
            st.session_state.show_full_doc = False
            st.rerun()


def render_raw_rant_view(
    db: Session,
    project: Project,
    doc: AgentOSDocument
) -> None:
    """
    Render the preserved raw rant view.

    Args:
        db: Database session
        project: Current project
        doc: AgentOSDocument with raw rant
    """
    st.subheader("Raw Rant Preservation")
    st.caption("Original, unmodified rants are preserved here. They are NEVER modified after creation.")

    # Show current document's raw rant
    if doc.raw_rant:
        with st.expander("Current Document's Raw Rant", expanded=True):
            st.text_area(
                "Raw Rant",
                value=doc.raw_rant,
                height=200,
                disabled=True,
                label_visibility="collapsed"
            )

    st.divider()

    # Show saved raw rants from database
    st.markdown("### Saved Raw Rants")

    saved_rants = get_raw_rants(db, project.id, limit=10)

    if saved_rants:
        for rant in saved_rants:
            with st.expander(
                f"{rant.created_at.strftime('%Y-%m-%d %H:%M')} - {rant.word_count} words ({rant.source_type})",
                expanded=False
            ):
                st.text_area(
                    "Content",
                    value=rant.content,
                    height=200,
                    disabled=True,
                    key=f"rant_{rant.id}",
                    label_visibility="collapsed"
                )

                if rant.agent_os_doc:
                    if st.button("Load Agent OS", key=f"load_aos_{rant.id}"):
                        loaded_doc = AgentOSDocument.from_dict(rant.agent_os_doc)
                        st.session_state.agent_os_doc = loaded_doc
                        show_success("Loaded Agent OS document from saved rant!")
                        st.rerun()
    else:
        st.caption("*(No saved raw rants yet. Generate an Agent OS document to save a rant.)*")


def render_agent_os_panel(
    db: Session,
    project: Project,
    session_id: Optional[int] = None
) -> None:
    """
    Main entry point for the Agent OS panel.

    Args:
        db: Database session
        project: Current project
        session_id: Optional current chat session ID
    """
    st.header(f"Agent OS: {project.name}")

    st.markdown(
        """
        Transform your brainstorming sessions into structured Agent OS specifications.
        The AI organizes your raw thoughts into the three-layer Agent OS format:
        **Standards**, **Product**, and **Specs**.
        """
    )

    # Create sub-tabs
    tree_tab, generate_tab, raw_tab = st.tabs([
        "Live Tree View",
        "Generate",
        "Raw Rant"
    ])

    # Check if we have a document in session state
    doc = None
    if "agent_os_doc" in st.session_state:
        doc = st.session_state.agent_os_doc
    else:
        # Create empty document
        doc = create_empty_template(project.name)
        st.session_state.agent_os_doc = doc

    with tree_tab:
        # Show live tree view
        render_agent_os_tree(doc)

        # Show live classifications if any
        if "agent_os_classifications" in st.session_state:
            render_live_classification(st.session_state.agent_os_classifications)

        # Export options if document has content
        if doc.completion_percentage > 0:
            st.divider()
            render_export_options(doc)

    with generate_tab:
        # Consolidate button and generation
        new_doc = render_consolidate_button(db, project, session_id)
        if new_doc:
            doc = new_doc
            st.rerun()

    with raw_tab:
        render_raw_rant_view(db, project, doc)


def classify_and_update_live(
    text: str,
    openai_api_key: str,
    model: str = "gpt-4-turbo-preview"
) -> List[ClassifiedItem]:
    """
    Classify text and update session state for live view.

    This function can be called from the chat panel to update
    the Agent OS tree in real-time as the user chats.

    Args:
        text: Text to classify
        openai_api_key: OpenAI API key
        model: Model to use

    Returns:
        List of classified items
    """
    items, suggested_name = classify_text(text, openai_api_key, model)

    if items:
        # Store in session state for live display
        if "agent_os_classifications" not in st.session_state:
            st.session_state.agent_os_classifications = []

        st.session_state.agent_os_classifications.extend(items)

        # Keep only last 50 classifications
        if len(st.session_state.agent_os_classifications) > 50:
            st.session_state.agent_os_classifications = st.session_state.agent_os_classifications[-50:]

    return items
