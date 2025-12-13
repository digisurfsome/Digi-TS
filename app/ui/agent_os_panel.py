"""
Agent OS Panel UI Components.

Provides UI for viewing, generating, and exporting Agent OS documents.
Includes live tree view of Agent OS structure and consolidation features.
Phase 2B: Adds Click-to-Rant and Real-Time Tagging voice input features.
Phase 3: Adds Tag Overlay, Multi-Panel Live Fill, and Click-to-Expand features.
Phase 4: Adds Cockpit Mode and Lab Mode integration.
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import time
import re

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
    VOICE_SECTION_MAP,
    add_tagged_content_to_document,
    save_voice_rant,
    get_voice_rants,
    generate_agent_os_from_tagged_rant,
    get_organized_view,
)
from app.services.voice_service import (
    VoiceInputMode,
    RecordingState,
    TagEvent,
    TaggedSegment,
    VoiceRantData,
    transcribe_audio,
    process_click_to_rant,
    process_real_time_rant,
    split_transcript_by_tags,
    get_taggable_sections,
    get_section_key,
    format_duration,
)
from app.ui.layout import show_success, show_error, show_warning, show_info
from app.services.lab_service import (
    LabService,
    FeatureFlag,
    get_section_color,
    get_section_layer,
)


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


# ============================================================================
# TAG OVERLAY TOGGLE (Phase 3 - Mechanism 12)
# ============================================================================


def render_tag_overlay_view(
    doc: AgentOSDocument,
    raw_text: str,
    tagged_segments: Optional[List[Dict]] = None
) -> None:
    """
    Render raw rant with tag overlay toggle.

    Shows tags overlaid on raw rant text. See connections without losing original.

    Args:
        doc: AgentOSDocument for section info
        raw_text: The raw unmodified rant text
        tagged_segments: Optional list of tagged segments with positions
    """
    st.markdown("#### Raw Rant with Tag Overlay")

    # Toggle for showing/hiding tags
    show_tags = st.toggle(
        "Show Tag Overlay",
        value=False,
        key="tag_overlay_toggle",
        help="Toggle to show/hide section tags overlaid on the raw text"
    )

    if not raw_text:
        st.caption("*(No raw text available)*")
        return

    if not show_tags:
        # Default view: Clean raw text
        st.text_area(
            "Raw Rant",
            value=raw_text,
            height=300,
            disabled=True,
            label_visibility="collapsed"
        )
    else:
        # Tagged view: Show tags inline
        if tagged_segments:
            # Build annotated text from tagged segments
            annotated_html = _build_annotated_html(raw_text, tagged_segments)
            st.markdown(annotated_html, unsafe_allow_html=True)

            # Legend
            _render_tag_legend()
        else:
            # Try to infer tags from the document
            inferred_segments = _infer_tags_from_document(raw_text, doc)
            if inferred_segments:
                annotated_html = _build_annotated_html(raw_text, inferred_segments)
                st.markdown(annotated_html, unsafe_allow_html=True)
                _render_tag_legend()
            else:
                st.info("No tagged segments available. Use Real-Time Tagging to create tagged content.")
                st.text_area(
                    "Raw Rant",
                    value=raw_text,
                    height=300,
                    disabled=True,
                    label_visibility="collapsed"
                )


def _build_annotated_html(raw_text: str, segments: List[Dict]) -> str:
    """
    Build HTML with annotated tags from segments.

    Args:
        raw_text: Original text
        segments: List of {section, text, start_time, end_time}

    Returns:
        HTML string with tagged spans
    """
    # Sort segments by position in text (approximate by text matching)
    html_parts = ['<div style="background: #1a1a2e; padding: 16px; border-radius: 8px; font-family: monospace; line-height: 1.8;">']

    remaining_text = raw_text
    for segment in segments:
        section = segment.get("section", "Unknown")
        segment_text = segment.get("text", "")
        section_key = VOICE_SECTION_MAP.get(section, section.lower().replace(" ", "_"))
        color = get_section_color(section_key)
        layer = get_section_layer(section_key)

        if segment_text and segment_text in remaining_text:
            # Find the segment in remaining text
            idx = remaining_text.find(segment_text)
            if idx > 0:
                # Add text before segment
                html_parts.append(f'<span style="color: #e0e0e0;">{remaining_text[:idx]}</span>')

            # Add tagged segment with tooltip
            tooltip = f"{layer} > {section}"
            html_parts.append(f'''
                <span style="
                    background: {color}22;
                    border-bottom: 2px solid {color};
                    padding: 2px 4px;
                    border-radius: 4px;
                    position: relative;
                    cursor: pointer;
                " title="{tooltip}">
                    <span style="color: #ffffff;">{segment_text}</span>
                    <sup style="
                        background: {color};
                        color: white;
                        font-size: 10px;
                        padding: 1px 4px;
                        border-radius: 3px;
                        margin-left: 2px;
                    ">{section}</sup>
                </span>
            ''')

            remaining_text = remaining_text[idx + len(segment_text):]

    # Add any remaining text
    if remaining_text:
        html_parts.append(f'<span style="color: #e0e0e0;">{remaining_text}</span>')

    html_parts.append('</div>')

    return ''.join(html_parts)


def _infer_tags_from_document(raw_text: str, doc: AgentOSDocument) -> List[Dict]:
    """
    Try to infer tag positions by matching document content to raw text.

    Args:
        raw_text: Original text
        doc: AgentOSDocument with classified content

    Returns:
        List of inferred segments
    """
    segments = []

    # Extract content from document and try to find in raw text
    if doc.features:
        feature = doc.features[0]

        # Check each section
        sections_to_check = [
            ("Overview", feature.get("overview", "")),
            ("Requirements (Functional)", feature.get("requirements_functional", [])),
            ("Requirements (Technical)", feature.get("requirements_technical", [])),
            ("User Stories", feature.get("user_stories", [])),
            ("Acceptance Criteria", feature.get("acceptance_criteria", [])),
            ("Success Metrics", feature.get("success_metrics", "")),
        ]

        for section_name, content in sections_to_check:
            if isinstance(content, str) and content:
                # Check if content appears in raw text
                if content[:50] in raw_text or content in raw_text:
                    segments.append({
                        "section": section_name,
                        "text": content[:200] if len(content) > 200 else content,
                    })
            elif isinstance(content, list):
                for item in content[:3]:  # Limit to first 3 items
                    if item and item in raw_text:
                        segments.append({
                            "section": section_name,
                            "text": item,
                        })

    return segments


def _render_tag_legend() -> None:
    """Render the color legend for tag overlay."""
    st.markdown("---")
    st.markdown("**Tag Legend:**")

    legend_cols = st.columns(4)

    legend_items = [
        ("Standards", "#3b82f6"),
        ("Product", "#8b5cf6"),
        ("Specs (Req)", "#10b981"),
        ("Specs (Stories)", "#f97316"),
        ("Specs (Technical)", "#ef4444"),
        ("Gaps", "#eab308"),
    ]

    for idx, (name, color) in enumerate(legend_items):
        col_idx = idx % 4
        with legend_cols[col_idx]:
            st.markdown(f'''
                <span style="
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    background: {color};
                    border-radius: 2px;
                    margin-right: 4px;
                "></span>
                <span style="font-size: 12px;">{name}</span>
            ''', unsafe_allow_html=True)


# ============================================================================
# MULTI-PANEL LIVE FILL VIEW (Phase 3 - Mechanism 13)
# ============================================================================


def render_multi_panel_live_fill(
    doc: AgentOSDocument,
    highlight_section: Optional[str] = None
) -> Optional[str]:
    """
    Render multiple Agent OS sections as a grid of mini panels.

    Watch multiple sections being filled simultaneously.

    Args:
        doc: AgentOSDocument to display
        highlight_section: Optional section to highlight (recently updated)

    Returns:
        Clicked section name if any panel was clicked
    """
    st.markdown("#### Multi-Panel View")
    st.caption("Watch all sections fill in real-time. Click any panel to expand.")

    clicked_section = None

    # Define panel sections
    panels = [
        ("overview", "Overview", "overview"),
        ("requirements_functional", "Requirements (Functional)", "requirements_functional"),
        ("requirements_technical", "Requirements (Technical)", "requirements_technical"),
        ("user_stories", "User Stories", "user_stories"),
        ("acceptance_criteria", "Acceptance Criteria", "acceptance_criteria"),
        ("technical_spec", "Technical Spec", "technical_spec"),
        ("success_metrics", "Success Metrics", "success_metrics"),
        ("questions", "Questions/Gaps", "questions"),
    ]

    # Create 2 rows of 4 panels
    row1_panels = panels[:4]
    row2_panels = panels[4:]

    # Row 1
    cols1 = st.columns(4)
    for idx, (key, label, section_key) in enumerate(row1_panels):
        with cols1[idx]:
            clicked = _render_mini_panel(
                doc, key, label, section_key,
                is_highlighted=(highlight_section == section_key)
            )
            if clicked:
                clicked_section = section_key

    # Row 2
    cols2 = st.columns(4)
    for idx, (key, label, section_key) in enumerate(row2_panels):
        with cols2[idx]:
            clicked = _render_mini_panel(
                doc, key, label, section_key,
                is_highlighted=(highlight_section == section_key)
            )
            if clicked:
                clicked_section = section_key

    return clicked_section


def _render_mini_panel(
    doc: AgentOSDocument,
    key: str,
    label: str,
    section_key: str,
    is_highlighted: bool = False
) -> bool:
    """
    Render a single mini panel for a section.

    Args:
        doc: AgentOSDocument
        key: Internal key
        label: Display label
        section_key: Section key for color
        is_highlighted: Whether to highlight this panel

    Returns:
        True if panel was clicked
    """
    color = get_section_color(section_key)
    content = _get_section_content(doc, key)
    preview = _get_content_preview(content)
    status = _get_section_status_indicator(content)

    # Highlight effect
    border_style = f"3px solid {color}" if is_highlighted else f"1px solid #374151"
    animation = "animation: pulse 0.5s ease-in-out;" if is_highlighted else ""

    # Panel container
    panel_html = f'''
    <div style="
        background: #1f2937;
        border: {border_style};
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        min-height: 120px;
        {animation}
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        ">
            <span style="
                font-size: 11px;
                font-weight: 600;
                color: {color};
                text-transform: uppercase;
            ">{label}</span>
            <span style="font-size: 10px;">{status}</span>
        </div>
        <div style="
            font-size: 12px;
            color: #9ca3af;
            line-height: 1.4;
            overflow: hidden;
            max-height: 60px;
        ">{preview}</div>
    </div>
    '''

    st.markdown(panel_html, unsafe_allow_html=True)

    # Click handler using button
    return st.button(
        f"Expand {label}",
        key=f"expand_panel_{key}",
        use_container_width=True,
        type="secondary"
    )


def _get_section_content(doc: AgentOSDocument, key: str) -> Any:
    """Get content for a specific section."""
    if not doc.features:
        if key == "questions":
            return doc.questions
        return None

    feature = doc.features[0]

    content_map = {
        "overview": feature.get("overview", ""),
        "requirements_functional": feature.get("requirements_functional", []),
        "requirements_technical": feature.get("requirements_technical", []),
        "user_stories": feature.get("user_stories", []),
        "acceptance_criteria": feature.get("acceptance_criteria", []),
        "technical_spec": feature.get("technical_spec", {}),
        "success_metrics": feature.get("success_metrics", ""),
        "questions": doc.questions,
    }

    return content_map.get(key)


def _get_content_preview(content: Any) -> str:
    """Get a preview of section content."""
    if not content:
        return "<em style='color: #6b7280;'>(empty)</em>"

    if isinstance(content, str):
        preview = content[:100]
        if len(content) > 100:
            preview += "..."
        return preview

    if isinstance(content, list):
        if not content:
            return "<em style='color: #6b7280;'>(empty)</em>"
        items_preview = []
        for item in content[:3]:
            if len(str(item)) > 40:
                items_preview.append(f"- {str(item)[:40]}...")
            else:
                items_preview.append(f"- {item}")
        if len(content) > 3:
            items_preview.append(f"<em>+{len(content) - 3} more</em>")
        return "<br>".join(items_preview)

    if isinstance(content, dict):
        filled = sum(1 for v in content.values() if v)
        return f"<em>{filled}/4 fields filled</em>"

    return str(content)[:100]


def _get_section_status_indicator(content: Any) -> str:
    """Get status indicator for section content."""
    if not content:
        return "[ ]"

    if isinstance(content, str):
        return "[x]" if len(content) > 10 else "[~]"

    if isinstance(content, list):
        if len(content) >= 2:
            return "[x]"
        elif len(content) > 0:
            return "[~]"
        return "[ ]"

    if isinstance(content, dict):
        filled = sum(1 for v in content.values() if v)
        if filled >= 3:
            return "[x]"
        elif filled > 0:
            return "[~]"
        return "[ ]"

    return "[?]"


# ============================================================================
# CLICK-TO-EXPAND (Phase 3 - Mechanism 14)
# ============================================================================


def render_expanded_section(
    doc: AgentOSDocument,
    section_key: str,
    db: Session,
    project: "Project"
) -> bool:
    """
    Render an expanded view of a section.

    Allows viewing and editing full section content.

    Args:
        doc: AgentOSDocument
        section_key: Section to expand
        db: Database session
        project: Current project

    Returns:
        True if section was modified
    """
    section_labels = {
        "overview": "Overview",
        "requirements_functional": "Functional Requirements",
        "requirements_technical": "Technical Requirements",
        "user_stories": "User Stories",
        "acceptance_criteria": "Acceptance Criteria",
        "technical_spec": "Technical Specification",
        "success_metrics": "Success Metrics",
        "questions": "Questions / Gaps",
    }

    label = section_labels.get(section_key, section_key)
    color = get_section_color(section_key)

    # Header with close button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"""
        <h3 style="color: {color}; margin: 0;">{label}</h3>
        """, unsafe_allow_html=True)
    with col2:
        close_btn = st.button("Close", key=f"close_expanded_{section_key}")

    if close_btn:
        if "expanded_section" in st.session_state:
            del st.session_state["expanded_section"]
        st.rerun()

    st.divider()

    # Get current content
    content = _get_section_content(doc, section_key)
    modified = False

    # Render editable content based on type
    if section_key in ["overview", "success_metrics"]:
        # Text content
        current_value = content if content else ""
        new_value = st.text_area(
            f"Edit {label}",
            value=current_value,
            height=200,
            key=f"edit_{section_key}"
        )

        if new_value != current_value:
            if st.button("Save Changes", type="primary", key=f"save_{section_key}"):
                _update_section_content(doc, section_key, new_value)
                st.session_state.agent_os_doc = doc
                st.session_state.agent_os_doc_dict = doc.to_dict()
                show_success(f"Updated {label}!")
                modified = True
                st.rerun()

    elif section_key in ["requirements_functional", "requirements_technical", "user_stories", "acceptance_criteria"]:
        # List content
        current_items = content if content else []

        st.markdown("**Current Items:**")
        items_to_remove = []

        for idx, item in enumerate(current_items):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {item}")
            with col2:
                if st.button("X", key=f"remove_{section_key}_{idx}"):
                    items_to_remove.append(idx)

        # Remove items
        if items_to_remove:
            new_items = [item for idx, item in enumerate(current_items) if idx not in items_to_remove]
            _update_section_content(doc, section_key, new_items)
            st.session_state.agent_os_doc = doc
            st.session_state.agent_os_doc_dict = doc.to_dict()
            modified = True
            st.rerun()

        # Add new item
        st.markdown("**Add New Item:**")
        new_item = st.text_input(f"New {label} item", key=f"new_{section_key}")
        if st.button("Add Item", key=f"add_{section_key}"):
            if new_item and new_item.strip():
                new_items = current_items + [new_item.strip()]
                _update_section_content(doc, section_key, new_items)
                st.session_state.agent_os_doc = doc
                st.session_state.agent_os_doc_dict = doc.to_dict()
                show_success(f"Added item to {label}!")
                modified = True
                st.rerun()

    elif section_key == "technical_spec":
        # Dict content
        tech_spec = content if content else {}

        sub_fields = [
            ("api_endpoints", "API Endpoints"),
            ("data_models", "Data Models"),
            ("dependencies", "Dependencies"),
            ("edge_cases", "Edge Cases"),
        ]

        for field_key, field_label in sub_fields:
            current_value = tech_spec.get(field_key, "")
            new_value = st.text_area(
                field_label,
                value=current_value,
                height=80,
                key=f"edit_{section_key}_{field_key}"
            )

            if new_value != current_value:
                tech_spec[field_key] = new_value

        if st.button("Save Technical Spec", type="primary", key=f"save_{section_key}"):
            _update_section_content(doc, section_key, tech_spec)
            st.session_state.agent_os_doc = doc
            st.session_state.agent_os_doc_dict = doc.to_dict()
            show_success("Updated Technical Specification!")
            modified = True
            st.rerun()

    elif section_key == "questions":
        # Questions list (at doc level, not feature level)
        current_items = doc.questions if doc.questions else []

        st.markdown("**Current Questions:**")
        items_to_remove = []

        for idx, item in enumerate(current_items):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {item}")
            with col2:
                if st.button("X", key=f"remove_{section_key}_{idx}"):
                    items_to_remove.append(idx)

        # Remove items
        if items_to_remove:
            doc.questions = [item for idx, item in enumerate(current_items) if idx not in items_to_remove]
            st.session_state.agent_os_doc = doc
            st.session_state.agent_os_doc_dict = doc.to_dict()
            modified = True
            st.rerun()

        # Add new question
        st.markdown("**Add New Question:**")
        new_item = st.text_input("New question", key=f"new_{section_key}")
        if st.button("Add Question", key=f"add_{section_key}"):
            if new_item and new_item.strip():
                doc.questions.append(new_item.strip())
                st.session_state.agent_os_doc = doc
                st.session_state.agent_os_doc_dict = doc.to_dict()
                show_success("Added question!")
                modified = True
                st.rerun()

    return modified


def _update_section_content(doc: AgentOSDocument, section_key: str, value: Any) -> None:
    """Update content for a specific section."""
    if not doc.features:
        doc.features.append({
            "name": "General",
            "overview": "",
            "requirements_functional": [],
            "requirements_technical": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "technical_spec": {},
            "success_metrics": ""
        })

    feature = doc.features[0]

    if section_key == "overview":
        feature["overview"] = value
    elif section_key == "requirements_functional":
        feature["requirements_functional"] = value
    elif section_key == "requirements_technical":
        feature["requirements_technical"] = value
    elif section_key == "user_stories":
        feature["user_stories"] = value
    elif section_key == "acceptance_criteria":
        feature["acceptance_criteria"] = value
    elif section_key == "technical_spec":
        feature["technical_spec"] = value
    elif section_key == "success_metrics":
        feature["success_metrics"] = value
    elif section_key == "questions":
        doc.questions = value

    doc.calculate_completion()


# ============================================================================
# CLICK-TO-RANT: Interactive Flash Labels (Mechanism 2)
# ============================================================================


def render_clickable_flash_labels(
    doc: AgentOSDocument,
    db: Session,
    project: Project,
    feature_name: Optional[str] = None
) -> Optional[str]:
    """
    Render clickable Flash Labels for Click-to-Rant mode.

    Labels are interactive - clicking one activates voice input for that section.

    Args:
        doc: AgentOSDocument to check
        db: Database session
        project: Current project
        feature_name: Optional specific feature to check

    Returns:
        Selected section name if a label was clicked, None otherwise
    """
    # Get section statuses
    statuses = doc.get_section_status(feature_name)

    # Check if we're in recording mode
    is_recording = st.session_state.get("voice_recording_active", False)
    active_section = st.session_state.get("voice_target_section", None)

    st.markdown("#### Click a Section to Speak")
    st.caption("Tap a label below, then speak to fill that section with voice input.")

    # Define colors for each state
    state_styles = {
        "empty": {"bg": "#ff6b6b", "color": "white", "icon": "[ ]"},
        "partial": {"bg": "#ffa502", "color": "white", "icon": "[~]"},
        "complete": {"bg": "#26de81", "color": "white", "icon": "[x]"},
        "active": {"bg": "#0ea5e9", "color": "white", "icon": "[*]"}  # Recording state
    }

    # Create columns for section buttons
    sections = list(statuses.keys())
    cols = st.columns(min(len(sections), 4))

    selected_section = None

    for idx, section_name in enumerate(sections):
        col_idx = idx % len(cols)
        status = statuses[section_name]

        # Override status if this section is being recorded
        if is_recording and active_section == section_name:
            status = "active"

        style = state_styles.get(status, state_styles["empty"])

        with cols[col_idx]:
            # Use button for each section
            button_label = f"{style['icon']} {section_name}"

            if is_recording and active_section == section_name:
                button_label = f"[REC] {section_name}"

            if st.button(
                button_label,
                key=f"flash_label_{section_name}_{project.id}",
                use_container_width=True,
                type="primary" if status == "active" else "secondary"
            ):
                selected_section = section_name

    # Show recording indicator if active
    if is_recording and active_section:
        st.markdown(f"""
        <div style="
            background: #0ea5e9;
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            margin: 12px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        ">
            <span style="animation: pulse 1s infinite; font-size: 20px;">REC</span>
            <span>Recording to: <strong>{active_section}</strong></span>
        </div>
        """, unsafe_allow_html=True)

    return selected_section


def render_click_to_rant_panel(
    doc: AgentOSDocument,
    db: Session,
    project: Project
) -> Optional[AgentOSDocument]:
    """
    Render the Click-to-Rant voice input panel.

    Mechanism 2: Click a label, then speak to fill ONLY that section.

    Args:
        doc: AgentOSDocument to update
        db: Database session
        project: Current project

    Returns:
        Updated AgentOSDocument if changes were made, None otherwise
    """
    st.subheader("Click-to-Rant")
    st.markdown("""
    **How it works:**
    1. Click a section label below
    2. Record your voice (or type if voice unavailable)
    3. Content goes directly to that section
    """)

    # Get settings
    settings = get_all_settings(db)
    api_key = settings.get("OPENAI_API_KEY", "")

    if not api_key:
        st.warning("OpenAI API key required for voice transcription. Set it in Settings.")

    # Render clickable labels
    selected_section = render_clickable_flash_labels(doc, db, project)

    # Handle section selection
    if selected_section:
        st.session_state.voice_target_section = selected_section
        st.session_state.voice_input_mode = "click_to_rant"
        st.rerun()

    # If a section is selected, show input options
    target_section = st.session_state.get("voice_target_section")

    if target_section:
        st.markdown(f"### Recording to: **{target_section}**")

        # Voice input using Streamlit's audio input
        st.markdown("#### Option 1: Voice Input")
        audio_data = st.audio_input(
            "Click to record",
            key=f"audio_input_{target_section}_{project.id}"
        )

        if audio_data:
            with st.spinner(f"Transcribing and adding to {target_section}..."):
                try:
                    # Read audio bytes
                    audio_bytes = audio_data.read()

                    # Transcribe
                    text, target = process_click_to_rant(
                        audio_data=audio_bytes,
                        target_section=target_section,
                        openai_api_key=api_key
                    )

                    if text:
                        # Get section key
                        section_key = get_section_key(target_section)

                        # Add to document
                        updated_doc = add_tagged_content_to_document(
                            doc, section_key, text
                        )

                        # Save voice rant to database
                        try:
                            save_voice_rant(
                                db=db,
                                project_id=project.id,
                                raw_transcript=text,
                                total_duration=0,  # Audio input doesn't provide duration
                                mode="click_to_rant",
                                target_section=target_section,
                                agent_os_doc=updated_doc.to_dict()
                            )
                        except Exception as save_err:
                            show_warning(f"Could not save voice rant: {save_err}")

                        # Update session state
                        st.session_state.agent_os_doc = updated_doc
                        st.session_state.agent_os_doc_dict = updated_doc.to_dict()

                        show_success(f"Added {len(text.split())} words to {target_section}!")

                        # Clear target section
                        del st.session_state["voice_target_section"]
                        st.rerun()

                except Exception as e:
                    show_error(f"Transcription failed: {str(e)}")

        # Fallback: Text input
        st.markdown("#### Option 2: Type Instead")
        manual_text = st.text_area(
            f"Type content for {target_section}",
            placeholder="Type your content here if voice isn't available...",
            height=100,
            key=f"manual_input_{target_section}_{project.id}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Add Content", type="primary", use_container_width=True):
                if manual_text and manual_text.strip():
                    section_key = get_section_key(target_section)
                    updated_doc = add_tagged_content_to_document(
                        doc, section_key, manual_text.strip()
                    )
                    st.session_state.agent_os_doc = updated_doc
                    st.session_state.agent_os_doc_dict = updated_doc.to_dict()
                    show_success(f"Added content to {target_section}!")
                    del st.session_state["voice_target_section"]
                    st.rerun()
                else:
                    show_warning("Please enter some content")

        with col2:
            if st.button("Cancel", use_container_width=True):
                del st.session_state["voice_target_section"]
                st.rerun()

    return None


# ============================================================================
# REAL-TIME TAGGING: Continuous Recording with Tags (Mechanism 3)
# ============================================================================


def render_real_time_tagging_panel(
    doc: AgentOSDocument,
    db: Session,
    project: Project
) -> Optional[AgentOSDocument]:
    """
    Render the Real-Time Tagging panel.

    Mechanism 3: One continuous rant with tag buttons to mark sections as you go.

    Args:
        doc: AgentOSDocument to update
        db: Database session
        project: Current project

    Returns:
        Updated AgentOSDocument if changes were made, None otherwise
    """
    st.subheader("Real-Time Tagging")
    st.markdown("""
    **How it works:**
    1. Click **Start Rant** to begin recording
    2. Tap section buttons as you speak to mark what you're talking about
    3. Click **End Rant** when done
    4. See both raw rant and organized version
    """)

    # Get settings
    settings = get_all_settings(db)
    api_key = settings.get("OPENAI_API_KEY", "")

    if not api_key:
        st.warning("OpenAI API key required for voice transcription. Set it in Settings.")

    # Initialize session state for tagging
    if "realtime_tag_events" not in st.session_state:
        st.session_state.realtime_tag_events = []
    if "realtime_recording_start" not in st.session_state:
        st.session_state.realtime_recording_start = None
    if "realtime_current_tag" not in st.session_state:
        st.session_state.realtime_current_tag = None

    is_recording = st.session_state.get("realtime_recording_active", False)

    # Recording controls
    if not is_recording:
        # Start recording UI
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Start Rant",
                type="primary",
                use_container_width=True,
                key="start_rant_btn"
            ):
                st.session_state.realtime_recording_active = True
                st.session_state.realtime_recording_start = time.time()
                st.session_state.realtime_tag_events = []
                st.session_state.realtime_current_tag = None
                st.rerun()
    else:
        # Recording in progress UI
        elapsed = time.time() - st.session_state.realtime_recording_start
        elapsed_str = format_duration(elapsed)

        # Recording indicator
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            margin: 12px 0;
            text-align: center;
        ">
            <div style="font-size: 24px; font-weight: bold; animation: pulse 1s infinite;">
                REC {elapsed_str}
            </div>
            <div style="font-size: 14px; margin-top: 8px;">
                Tap tags below as you speak to mark sections
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Tag buttons
        st.markdown("#### Tap to Tag Current Section")
        sections = get_taggable_sections()
        cols = st.columns(4)

        current_tag = st.session_state.get("realtime_current_tag")

        for idx, section in enumerate(sections):
            col_idx = idx % 4
            with cols[col_idx]:
                is_active = current_tag == section
                btn_type = "primary" if is_active else "secondary"

                if st.button(
                    f"{'> ' if is_active else ''}{section}",
                    key=f"tag_btn_{section}_{project.id}",
                    use_container_width=True,
                    type=btn_type
                ):
                    # Record tag event
                    tag_time = time.time() - st.session_state.realtime_recording_start
                    st.session_state.realtime_tag_events.append({
                        "section": section,
                        "timestamp": tag_time
                    })
                    st.session_state.realtime_current_tag = section
                    st.rerun()

        # Current tag indicator
        if current_tag:
            tag_count = len(st.session_state.realtime_tag_events)
            st.markdown(f"""
            <div style="
                background: #0ea5e9;
                color: white;
                padding: 10px 16px;
                border-radius: 8px;
                margin: 12px 0;
            ">
                <strong>Currently tagging:</strong> {current_tag} |
                <strong>Tags recorded:</strong> {tag_count}
            </div>
            """, unsafe_allow_html=True)

        # Tag history
        if st.session_state.realtime_tag_events:
            with st.expander("Tag History", expanded=False):
                for i, tag in enumerate(st.session_state.realtime_tag_events):
                    st.caption(f"{format_duration(tag['timestamp'])} - {tag['section']}")

        st.markdown("---")

        # Audio input for the recording
        st.markdown("#### Record Your Rant")
        audio_data = st.audio_input(
            "Record your continuous rant here",
            key=f"realtime_audio_{project.id}"
        )

        # End recording controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("End Rant", type="primary", use_container_width=True):
                if audio_data:
                    with st.spinner("Processing your rant..."):
                        try:
                            # Read audio
                            audio_bytes = audio_data.read()

                            # Create tag events from session state
                            tag_events = [
                                TagEvent(
                                    section=t["section"],
                                    timestamp=t["timestamp"]
                                )
                                for t in st.session_state.realtime_tag_events
                            ]

                            # Process with real-time tagging
                            rant_data = process_real_time_rant(
                                audio_data=audio_bytes,
                                tag_events=tag_events,
                                openai_api_key=api_key
                            )

                            # Store rant data for viewing
                            st.session_state.voice_rant_data = rant_data.to_dict()

                            # Save to database
                            try:
                                save_voice_rant(
                                    db=db,
                                    project_id=project.id,
                                    raw_transcript=rant_data.raw_transcript,
                                    total_duration=rant_data.total_duration,
                                    mode="real_time_tag",
                                    tag_events=[t.to_dict() for t in rant_data.tags],
                                    tagged_segments=[s.to_dict() for s in rant_data.segments],
                                    whisper_segments=rant_data.whisper_segments
                                )
                            except Exception as save_err:
                                show_warning(f"Could not save: {save_err}")

                            # Clean up recording state
                            st.session_state.realtime_recording_active = False
                            st.session_state.realtime_recording_start = None

                            show_success(f"Rant processed! {len(rant_data.raw_transcript.split())} words, {len(rant_data.segments)} segments")
                            st.rerun()

                        except Exception as e:
                            show_error(f"Processing failed: {str(e)}")
                else:
                    show_warning("Please record audio before ending the rant")

        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.realtime_recording_active = False
                st.session_state.realtime_recording_start = None
                st.session_state.realtime_tag_events = []
                st.session_state.realtime_current_tag = None
                st.rerun()

    # Show results if we have processed rant data
    if "voice_rant_data" in st.session_state and not is_recording:
        render_rant_results_view(doc, db, project)

    return None


# ============================================================================
# RAW VS ORGANIZED VIEW (Rant Results)
# ============================================================================


def render_rant_results_view(
    doc: AgentOSDocument,
    db: Session,
    project: Project
) -> None:
    """
    Render the Raw vs Organized toggle view for processed rants.

    Shows both the raw unmodified transcript and the organized version
    split by tagged sections.

    Args:
        doc: AgentOSDocument
        db: Database session
        project: Current project
    """
    rant_data = st.session_state.get("voice_rant_data")
    if not rant_data:
        return

    st.markdown("---")
    st.subheader("Rant Results")

    # Toggle view
    view_mode = st.radio(
        "View Mode",
        ["Raw Rant", "Organized"],
        horizontal=True,
        key=f"rant_view_mode_{project.id}"
    )

    if view_mode == "Raw Rant":
        # Raw rant view
        st.markdown("#### Raw Transcript (Unmodified)")
        st.caption("This is your original rant, preserved exactly as transcribed.")

        raw_text = rant_data.get("raw_transcript", "")
        duration = rant_data.get("total_duration", 0)
        word_count = len(raw_text.split()) if raw_text else 0

        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Words", word_count)
        with col2:
            st.metric("Duration", format_duration(duration))
        with col3:
            st.metric("Segments", len(rant_data.get("segments", [])))

        # Raw text with tag markers overlay (optional)
        show_markers = st.checkbox("Show tag markers", value=True)

        if show_markers and rant_data.get("tags"):
            # Display with tag markers inline
            st.markdown("*Tag markers shown as `[Section @ MM:SS]`*")

            display_text = raw_text
            tags = sorted(rant_data.get("tags", []), key=lambda t: t.get("timestamp", 0), reverse=True)

            # This is approximate since we don't have exact character positions
            st.text_area(
                "Raw transcript",
                value=raw_text,
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )

            # Show tag timeline below
            st.markdown("**Tag Timeline:**")
            for tag in sorted(rant_data.get("tags", []), key=lambda t: t.get("timestamp", 0)):
                ts = format_duration(tag.get("timestamp", 0))
                section = tag.get("section", "Unknown")
                st.caption(f"`{ts}` - {section}")
        else:
            st.text_area(
                "Raw transcript",
                value=raw_text,
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )

    else:
        # Organized view
        st.markdown("#### Organized by Section")
        st.caption("Your rant split into Agent OS sections based on your tags.")

        segments = rant_data.get("segments", [])

        if segments:
            # Group by section
            organized = get_organized_view(segments)

            for section, text in organized.items():
                with st.expander(f"**{section}**", expanded=True):
                    st.markdown(text)

                    # Show time range
                    section_segs = [s for s in segments if s.get("section") == section]
                    if section_segs:
                        start = min(s.get("start_time", 0) for s in section_segs)
                        end = max(s.get("end_time", 0) for s in section_segs)
                        st.caption(f"Time: {format_duration(start)} - {format_duration(end)}")
        else:
            st.info("No tagged segments found. The entire rant will be treated as untagged content.")

    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Add to Agent OS", type="primary", use_container_width=True):
            settings = get_all_settings(db)
            api_key = settings.get("OPENAI_API_KEY", "")

            with st.spinner("Generating Agent OS document from rant..."):
                try:
                    segments = rant_data.get("segments", [])
                    raw_transcript = rant_data.get("raw_transcript", "")

                    if segments:
                        # Generate from tagged segments
                        updated_doc = generate_agent_os_from_tagged_rant(
                            tagged_segments=segments,
                            raw_transcript=raw_transcript,
                            openai_api_key=api_key,
                            project_name=project.name
                        )
                    else:
                        # Generate from raw transcript
                        updated_doc = generate_agent_os_from_rant(
                            rant_text=raw_transcript,
                            openai_api_key=api_key,
                            project_name=project.name
                        )

                    st.session_state.agent_os_doc = updated_doc
                    st.session_state.agent_os_doc_dict = updated_doc.to_dict()
                    show_success(f"Agent OS updated! ({updated_doc.completion_percentage}% complete)")

                    # Clear rant data
                    del st.session_state["voice_rant_data"]
                    st.rerun()

                except Exception as e:
                    show_error(f"Failed to update Agent OS: {str(e)}")

    with col2:
        if st.button("New Rant", use_container_width=True):
            del st.session_state["voice_rant_data"]
            st.rerun()

    with col3:
        if st.button("Discard", use_container_width=True):
            del st.session_state["voice_rant_data"]
            show_info("Rant discarded")
            st.rerun()


def render_voice_rant_history(
    db: Session,
    project: Project,
    doc: AgentOSDocument
) -> None:
    """
    Render history of voice rants for a project.

    Args:
        db: Database session
        project: Current project
        doc: Current AgentOSDocument
    """
    st.subheader("Voice Rant History")
    st.caption("Previously recorded voice rants for this project.")

    voice_rants = get_voice_rants(db, project.id, limit=10)

    if not voice_rants:
        st.info("No voice rants recorded yet. Use Click-to-Rant or Real-Time Tagging to create one.")
        return

    for rant in voice_rants:
        mode_label = "Click-to-Rant" if rant.mode.value == "click_to_rant" else "Real-Time Tag"
        duration_str = format_duration(rant.total_duration) if rant.total_duration else "N/A"

        with st.expander(
            f"{rant.created_at.strftime('%Y-%m-%d %H:%M')} | {mode_label} | {rant.word_count} words | {duration_str}"
        ):
            # Raw transcript
            st.markdown("**Raw Transcript:**")
            st.text_area(
                "transcript",
                value=rant.raw_transcript,
                height=150,
                disabled=True,
                key=f"vrant_raw_{rant.id}",
                label_visibility="collapsed"
            )

            # Tagged segments if available
            if rant.tagged_segments:
                st.markdown("**Tagged Segments:**")
                for seg in rant.tagged_segments:
                    st.markdown(f"- **{seg.get('section')}**: {seg.get('text', '')[:100]}...")

            # Load into Agent OS
            if rant.agent_os_doc:
                if st.button("Load Agent OS", key=f"load_vrant_{rant.id}"):
                    loaded_doc = AgentOSDocument.from_dict(rant.agent_os_doc)
                    st.session_state.agent_os_doc = loaded_doc
                    st.session_state.agent_os_doc_dict = rant.agent_os_doc
                    show_success("Loaded Agent OS from voice rant!")
                    st.rerun()


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

    # Create sub-tabs (including new voice input tabs for Phase 2B)
    tree_tab, voice_tab, generate_tab, gaps_tab, raw_tab = st.tabs([
        "Live Tree View",
        "Voice Input",
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

    with voice_tab:
        # =====================================================================
        # VOICE INPUT METHODS (Phase 2B - Mechanisms 2 & 3)
        # =====================================================================
        st.markdown("### Voice-First Input")
        st.markdown("""
        Fill your Agent OS spec using your voice! Choose a method below:
        - **Click-to-Rant**: Tap a section, speak to fill just that section
        - **Real-Time Tagging**: One continuous rant, tap buttons to mark sections as you go
        """)

        # Voice method selector
        voice_method = st.radio(
            "Select Input Method",
            ["Click-to-Rant (Tap and Talk)", "Real-Time Tagging (Tag While Ranting)"],
            horizontal=True,
            key="voice_method_selector"
        )

        st.divider()

        if "Click-to-Rant" in voice_method:
            render_click_to_rant_panel(doc, db, project)
        else:
            render_real_time_tagging_panel(doc, db, project)

        # Voice rant history at bottom
        st.divider()
        render_voice_rant_history(db, project, doc)

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
