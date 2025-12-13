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
    GapItem,
    GapSeverity,
    classify_text,
    generate_agent_os_from_rant,
    create_empty_template,
    get_section_icon,
    get_subsection_icon,
    get_classification_summary,
    detect_gaps,
    calculate_completion_percentage,
    get_completion_color,
    generate_fill_prompts,
    process_fill_response,
    get_flash_label_sections,
    SECTION_MINIMUMS,
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


def render_flash_labels(doc: AgentOSDocument, feature_name: Optional[str] = None) -> None:
    """
    Render Flash Labels showing which Agent OS sections need filling.

    Labels appear as pill-shaped tags with visual states:
    - Empty (bright/pulsing): Section needs content
    - Partial (dimmed): Section has some content but below minimum
    - Complete (green checkmark): Section is complete

    Args:
        doc: AgentOSDocument to check
        feature_name: Optional specific feature to check
    """
    # Get section statuses
    statuses = doc.get_section_status(feature_name)

    # Define colors for each state
    state_styles = {
        "empty": {
            "bg": "#ff6b6b",
            "color": "white",
            "icon": "[ ]",
            "border": "2px solid #ff4757"
        },
        "partial": {
            "bg": "#ffa502",
            "color": "white",
            "icon": "[~]",
            "border": "2px solid #ff9f43"
        },
        "complete": {
            "bg": "#26de81",
            "color": "white",
            "icon": "[x]",
            "border": "2px solid #20bf6b"
        }
    }

    # Build the flash labels HTML
    labels_html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">'

    for section_name, status in statuses.items():
        style = state_styles.get(status, state_styles["empty"])

        # Add pulsing animation for empty sections
        animation = ""
        if status == "empty":
            animation = "animation: pulse 2s infinite;"

        labels_html += f'''
        <span style="
            background: {style['bg']};
            color: {style['color']};
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
            border: {style['border']};
            display: inline-flex;
            align-items: center;
            gap: 4px;
            {animation}
        ">
            <span style="font-family: monospace;">{style['icon']}</span>
            {section_name}
        </span>
        '''

    labels_html += '</div>'

    # Add CSS for pulse animation
    css = '''
    <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
    </style>
    '''

    st.markdown(css + labels_html, unsafe_allow_html=True)


def render_gap_percentage_display(
    doc: AgentOSDocument,
    db: Session,
    expanded: bool = False
) -> None:
    """
    Render the gap percentage display with expandable details.

    Shows:
    - Circular/bar progress indicator
    - Percentage prominently displayed
    - Color coding (red <50%, yellow 50-80%, green >80%)
    - Expandable details section
    - "Help me complete" button

    Args:
        doc: AgentOSDocument to display
        db: Database session for settings
        expanded: Whether details are expanded by default
    """
    # Calculate completion
    percentage = doc.calculate_completion()
    color = get_completion_color(percentage)

    # Get gap summary
    gap_summary = doc.get_gap_summary()

    # Color mapping for display
    color_map = {
        "red": {"bg": "#fee2e2", "text": "#dc2626", "bar": "#ef4444"},
        "orange": {"bg": "#fef3c7", "text": "#d97706", "bar": "#f59e0b"},
        "green": {"bg": "#d1fae5", "text": "#059669", "bar": "#10b981"}
    }

    colors = color_map.get(color, color_map["red"])

    # Main percentage display
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Large percentage display
        st.markdown(f"""
        <div style="
            text-align: center;
            padding: 20px;
            background: {colors['bg']};
            border-radius: 12px;
            margin: 10px 0;
        ">
            <div style="font-size: 48px; font-weight: bold; color: {colors['text']};">
                {percentage}%
            </div>
            <div style="font-size: 14px; color: #666; margin-top: 8px;">
                Agent OS Complete
            </div>
            <div style="font-size: 12px; color: #888; margin-top: 4px;">
                {gap_summary['total_gaps']} items missing across {len(set(g.section for g in gap_summary['gaps']))} sections
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Progress bar
    st.progress(percentage / 100)

    # Gap count badges
    if gap_summary['total_gaps'] > 0:
        col1, col2 = st.columns(2)
        with col1:
            if gap_summary['critical_count'] > 0:
                st.markdown(f"**{gap_summary['critical_count']}** critical gaps")
        with col2:
            if gap_summary['minor_count'] > 0:
                st.markdown(f"**{gap_summary['minor_count']}** minor gaps")

    # Expandable gap details
    with st.expander("View Gaps", expanded=expanded):
        if gap_summary['gaps']:
            # Group gaps by section
            gaps_by_section: Dict[str, List[GapItem]] = {}
            for gap in gap_summary['gaps']:
                section_key = gap.section
                if section_key not in gaps_by_section:
                    gaps_by_section[section_key] = []
                gaps_by_section[section_key].append(gap)

            for section, gaps in gaps_by_section.items():
                st.markdown(f"**{section.replace('_', ' ').title()}**")
                for gap in gaps:
                    severity_icon = "X" if gap.severity == GapSeverity.CRITICAL else "!"
                    severity_color = "#dc2626" if gap.severity == GapSeverity.CRITICAL else "#d97706"

                    st.markdown(f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        padding: 8px 12px;
                        background: #f9fafb;
                        border-radius: 6px;
                        margin: 4px 0;
                        border-left: 3px solid {severity_color};
                    ">
                        <span style="color: {severity_color}; font-weight: bold;">[{severity_icon}]</span>
                        <span>{gap.display_name}</span>
                        <span style="color: #888; font-size: 12px;">
                            ({gap.current_count}/{gap.minimum_required})
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.caption(f"*Prompt: {gap.prompt}*")

                st.divider()
        else:
            st.success("No gaps detected! Your Agent OS document is complete.")


def render_fill_request_ui(
    doc: AgentOSDocument,
    db: Session,
    project: Project
) -> Optional[AgentOSDocument]:
    """
    Render the Fill Request UI for AI-assisted gap filling.

    When user clicks "Help me complete":
    1. AI generates questions for missing sections
    2. Questions are displayed (not interrupting)
    3. User can answer when ready
    4. Answers auto-populate Agent OS sections

    Args:
        doc: AgentOSDocument to fill
        db: Database session
        project: Current project

    Returns:
        Updated AgentOSDocument if changes were made, None otherwise
    """
    settings = get_all_settings(db)
    api_key = settings.get("OPENAI_API_KEY", "")
    model = settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")

    # Check if we have fill prompts in session state
    fill_prompts_key = f"fill_prompts_{project.id}"
    current_prompt_key = f"current_fill_prompt_{project.id}"
    fill_response_key = f"fill_response_{project.id}"

    # Help me complete button
    col1, col2 = st.columns([1, 3])

    with col1:
        help_btn = st.button(
            "Help Me Complete",
            type="secondary",
            use_container_width=True,
            help="Generate AI questions to help fill gaps"
        )

    # Generate fill prompts if button clicked
    if help_btn:
        with st.spinner("Generating questions to help fill gaps..."):
            prompts = generate_fill_prompts(doc, api_key, model, max_questions=5)
            if prompts:
                st.session_state[fill_prompts_key] = prompts
                st.session_state[current_prompt_key] = 0
                show_success(f"Generated {len(prompts)} questions to help you complete the spec!")
            else:
                show_info("No gaps to fill - your document is looking good!")

    # Display fill prompts if available
    if fill_prompts_key in st.session_state and st.session_state[fill_prompts_key]:
        prompts = st.session_state[fill_prompts_key]
        current_idx = st.session_state.get(current_prompt_key, 0)

        if current_idx < len(prompts):
            prompt = prompts[current_idx]

            st.markdown("---")
            st.markdown("### Fill Gap Question")

            # Question card
            st.markdown(f"""
            <div style="
                background: #f0f9ff;
                border: 1px solid #0ea5e9;
                border-radius: 8px;
                padding: 16px;
                margin: 12px 0;
            ">
                <div style="font-size: 12px; color: #0369a1; margin-bottom: 8px;">
                    Section: {prompt.get('section', 'Unknown')}
                </div>
                <div style="font-size: 16px; font-weight: 500; color: #0c4a6e;">
                    {prompt.get('question', 'No question')}
                </div>
                <div style="font-size: 12px; color: #64748b; margin-top: 8px;">
                    {prompt.get('context', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Progress indicator
            st.caption(f"Question {current_idx + 1} of {len(prompts)}")
            st.progress((current_idx + 1) / len(prompts))

            # Answer input
            answer = st.text_area(
                "Your Answer",
                key=fill_response_key,
                placeholder="Type your answer here... (speak naturally, as if explaining to a colleague)",
                height=100
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                submit_btn = st.button("Submit", type="primary", use_container_width=True)

            with col2:
                skip_btn = st.button("Skip", use_container_width=True)

            with col3:
                dismiss_btn = st.button("Dismiss All", use_container_width=True)

            # Handle submit
            if submit_btn and answer and answer.strip():
                with st.spinner("Processing your answer..."):
                    try:
                        updated_doc = process_fill_response(
                            doc=doc,
                            section=prompt.get('section', ''),
                            response_text=answer,
                            openai_api_key=api_key,
                            model=model
                        )

                        # Move to next prompt
                        st.session_state[current_prompt_key] = current_idx + 1

                        # Update session state doc
                        st.session_state.agent_os_doc = updated_doc
                        st.session_state.agent_os_doc_dict = updated_doc.to_dict()

                        show_success("Answer processed and added to Agent OS!")
                        st.rerun()

                    except Exception as e:
                        show_error(f"Failed to process answer: {str(e)}")

            # Handle skip
            if skip_btn:
                st.session_state[current_prompt_key] = current_idx + 1
                st.rerun()

            # Handle dismiss
            if dismiss_btn:
                del st.session_state[fill_prompts_key]
                del st.session_state[current_prompt_key]
                if fill_response_key in st.session_state:
                    del st.session_state[fill_response_key]
                st.rerun()

        else:
            # All prompts answered
            st.success("All gap questions answered!")
            if st.button("Generate More Questions"):
                del st.session_state[fill_prompts_key]
                del st.session_state[current_prompt_key]
                st.rerun()

    return None


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

    # Check if we have a document in session state
    doc = None
    if "agent_os_doc" in st.session_state:
        doc = st.session_state.agent_os_doc
    else:
        # Create empty document
        doc = create_empty_template(project.name)
        st.session_state.agent_os_doc = doc

    # =========================================================================
    # FLASH LABELS - Always visible at top (Mechanism 1)
    # =========================================================================
    st.markdown("#### Section Status")
    render_flash_labels(doc)

    st.divider()

    # =========================================================================
    # GAP PERCENTAGE DISPLAY (Mechanism 15)
    # =========================================================================
    render_gap_percentage_display(doc, db, expanded=False)

    st.divider()

    # =========================================================================
    # FILL REQUEST UI (Mechanism 15 continued)
    # =========================================================================
    render_fill_request_ui(doc, db, project)

    st.divider()

    # Create sub-tabs
    tree_tab, generate_tab, gaps_tab, raw_tab = st.tabs([
        "Live Tree View",
        "Generate",
        "Gaps Detail",
        "Raw Rant"
    ])

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

    with gaps_tab:
        # Detailed gap analysis view (Mechanism 7)
        render_gap_analysis_view(doc, db, project)

    with raw_tab:
        render_raw_rant_view(db, project, doc)


def render_gap_analysis_view(
    doc: AgentOSDocument,
    db: Session,
    project: Project
) -> None:
    """
    Render detailed gap analysis view (Mechanism 7).

    Shows:
    - All gaps with severity levels
    - Prompts for each gap
    - Priority ordering

    Args:
        doc: AgentOSDocument to analyze
        db: Database session
        project: Current project
    """
    st.subheader("Gap Analysis")
    st.markdown(
        """
        This view shows all sections that need attention.
        Critical gaps should be addressed first - these are required for a complete spec.
        """
    )

    gap_summary = doc.get_gap_summary()

    if not gap_summary['gaps']:
        st.success("Congratulations! Your Agent OS document has no gaps.")
        st.balloons()
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Gaps", gap_summary['total_gaps'])
    with col2:
        st.metric("Critical", gap_summary['critical_count'], delta_color="inverse")
    with col3:
        st.metric("Minor", gap_summary['minor_count'])

    st.divider()

    # Critical gaps first
    if gap_summary['critical_gaps']:
        st.markdown("### Critical Gaps")
        st.caption("These sections are empty and required for a complete spec.")

        for gap in gap_summary['critical_gaps']:
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"""
                    <div style="
                        background: #fef2f2;
                        border-left: 4px solid #dc2626;
                        padding: 12px 16px;
                        border-radius: 0 8px 8px 0;
                        margin: 8px 0;
                    ">
                        <div style="font-weight: 600; color: #991b1b;">
                            [X] {gap.display_name}
                        </div>
                        <div style="font-size: 14px; color: #7f1d1d; margin-top: 4px;">
                            {gap.prompt}
                        </div>
                        <div style="font-size: 12px; color: #b91c1c; margin-top: 4px;">
                            {gap.current_count}/{gap.minimum_required} required
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()

    # Minor gaps
    if gap_summary['minor_gaps']:
        st.markdown("### Minor Gaps")
        st.caption("These sections have some content but could use more detail.")

        for gap in gap_summary['minor_gaps']:
            with st.container():
                st.markdown(f"""
                <div style="
                    background: #fffbeb;
                    border-left: 4px solid #f59e0b;
                    padding: 12px 16px;
                    border-radius: 0 8px 8px 0;
                    margin: 8px 0;
                ">
                    <div style="font-weight: 600; color: #92400e;">
                        [!] {gap.display_name}
                    </div>
                    <div style="font-size: 14px; color: #78350f; margin-top: 4px;">
                        {gap.prompt}
                    </div>
                    <div style="font-size: 12px; color: #b45309; margin-top: 4px;">
                        {gap.current_count}/{gap.minimum_required} items (partial)
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Quick fill section
    st.markdown("### Quick Fill")
    st.markdown("Select a gap to fill directly:")

    gap_options = [f"{g.display_name} ({g.severity.value})" for g in gap_summary['gaps']]
    selected_gap_label = st.selectbox("Select gap to fill", gap_options)

    if selected_gap_label:
        selected_idx = gap_options.index(selected_gap_label)
        selected_gap = gap_summary['gaps'][selected_idx]

        st.markdown(f"**Prompt:** {selected_gap.prompt}")

        quick_fill_input = st.text_area(
            "Your response",
            placeholder="Type your answer here...",
            height=100,
            key=f"quick_fill_{selected_gap.section}_{selected_gap.subsection}"
        )

        if st.button("Add to Agent OS", type="primary"):
            if quick_fill_input and quick_fill_input.strip():
                settings = get_all_settings(db)
                api_key = settings.get("OPENAI_API_KEY", "")
                model = settings.get("DEFAULT_SUMMARY_MODEL", "gpt-4-turbo-preview")

                with st.spinner("Processing..."):
                    try:
                        updated_doc = process_fill_response(
                            doc=doc,
                            section=selected_gap.display_name,
                            response_text=quick_fill_input,
                            openai_api_key=api_key,
                            model=model
                        )
                        st.session_state.agent_os_doc = updated_doc
                        st.session_state.agent_os_doc_dict = updated_doc.to_dict()
                        show_success(f"Added content to {selected_gap.display_name}!")
                        st.rerun()
                    except Exception as e:
                        show_error(f"Failed to add content: {str(e)}")
            else:
                show_warning("Please enter some content to add.")


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
