"""
Lab Panel UI Components.

Provides UI for Lab Mode testing functionality including:
- Feature flag toggles
- Configuration management
- Test session controls
- Config Levers settings
"""

import streamlit as st
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.models import Project
from app.ui.layout import show_success, show_error, show_warning, show_info
from app.services.lab_service import (
    LabService,
    FeatureFlag,
    ConfigSettings,
    TestConfiguration,
    TestMetrics,
    DetectionSensitivity,
    FlashLabelTiming,
    PanelLayout,
    ColorTheme,
    AnimationSpeed,
    RequiredSections,
    DEFAULT_FEATURE_FLAGS,
    DEFAULT_CONFIG,
    create_preset_configs,
)


# ============================================================================
# LAB MODE PANEL (Phase 4 - Mechanism 5)
# ============================================================================


def render_lab_panel(
    db: Session,
    project: Project,
    lab_service: Optional[LabService] = None
) -> None:
    """
    Render the complete Lab Mode panel.

    Provides:
    - Lab Mode toggle
    - Feature flag controls
    - Test configuration management
    - Test session controls
    - Metrics display

    Args:
        db: Database session
        project: Current project
        lab_service: Optional LabService instance
    """
    st.markdown("## Lab Mode")
    st.caption("Test different feature combinations to find what works best.")

    # Get or create lab service
    if lab_service is None:
        lab_service = _get_or_create_lab_service()

    # Lab Mode toggle
    st.divider()
    lab_mode_active = render_lab_mode_toggle(lab_service)

    if not lab_mode_active:
        st.info("Enable Lab Mode to access testing controls.")
        return

    # Tab navigation for lab features
    lab_tabs = st.tabs([
        "Feature Toggles",
        "Configurations",
        "Config Levers",
        "Test Session",
        "Metrics"
    ])

    with lab_tabs[0]:
        render_feature_toggles(lab_service)

    with lab_tabs[1]:
        render_configuration_manager(lab_service)

    with lab_tabs[2]:
        render_config_levers(lab_service)

    with lab_tabs[3]:
        render_test_session_controls(lab_service)

    with lab_tabs[4]:
        render_metrics_view(lab_service)


def _get_or_create_lab_service() -> LabService:
    """Get or create a LabService from session state."""
    if "lab_service" not in st.session_state:
        lab_service = LabService()

        # Load saved state if exists
        if "lab_service_state" in st.session_state:
            lab_service.load_from_dict(st.session_state.lab_service_state)
        else:
            # Create preset configurations
            create_preset_configs(lab_service)

        st.session_state.lab_service = lab_service

    return st.session_state.lab_service


def _save_lab_service_state(lab_service: LabService) -> None:
    """Save lab service state to session state."""
    st.session_state.lab_service_state = lab_service.save_to_dict()


# ============================================================================
# LAB MODE TOGGLE
# ============================================================================


def render_lab_mode_toggle(lab_service: LabService) -> bool:
    """
    Render the Lab Mode toggle with status.

    Args:
        lab_service: LabService instance

    Returns:
        True if Lab Mode is active
    """
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        lab_mode = st.toggle(
            "Enable Lab Mode",
            value=lab_service.is_lab_mode_active(),
            key="lab_mode_main_toggle",
            help="Enable testing mode to experiment with different feature combinations"
        )

    with col2:
        if lab_mode:
            st.markdown("""
            <span style="
                background: #059669;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
            ">LAB MODE ACTIVE</span>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <span style="
                background: #6b7280;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
            ">STANDARD MODE</span>
            """, unsafe_allow_html=True)

    with col3:
        if st.button("Reset All", key="reset_lab", help="Reset all settings to defaults"):
            lab_service.reset_feature_flags()
            lab_service.reset_config()
            _save_lab_service_state(lab_service)
            show_success("Settings reset to defaults!")
            st.rerun()

    # Update lab mode state
    if lab_mode != lab_service.is_lab_mode_active():
        if lab_mode:
            lab_service.start_lab_mode()
        else:
            lab_service.stop_lab_mode()
        _save_lab_service_state(lab_service)
        st.session_state.lab_mode_active = lab_mode

    return lab_mode


# ============================================================================
# FEATURE TOGGLES
# ============================================================================


def render_feature_toggles(lab_service: LabService) -> None:
    """
    Render feature flag toggles.

    Args:
        lab_service: LabService instance
    """
    st.markdown("### Feature Toggles")
    st.caption("Enable/disable individual features to test them in isolation.")

    current_flags = lab_service.get_feature_flags()

    # Group features by category
    categories = {
        "Voice Input": [
            (FeatureFlag.REAL_TIME_TAGGING, "Real-Time Tagging", "Continuous recording with inline tag buttons"),
            (FeatureFlag.CLICK_TO_RANT, "Click-to-Rant", "Tap section, then speak to fill"),
        ],
        "Visual Feedback": [
            (FeatureFlag.FLASH_LABELS, "Flash Labels", "Section status indicators"),
            (FeatureFlag.TAG_OVERLAY, "Tag Overlay", "Show tags on raw rant text"),
            (FeatureFlag.MULTI_PANEL_VIEW, "Multi-Panel View", "See all sections at once"),
        ],
        "Analysis": [
            (FeatureFlag.GAP_DETECTION, "Gap Detection", "Identify missing sections"),
            (FeatureFlag.POST_RANT_ANALYSIS, "Post-Rant Analysis", "Analyze after consolidation"),
        ],
        "Layout": [
            (FeatureFlag.COCKPIT_MODE, "Cockpit Mode", "All-panels-visible dashboard"),
            (FeatureFlag.AUTO_CONSOLIDATE, "Auto-Consolidate", "Automatically organize content"),
        ],
    }

    changed = False

    for category, features in categories.items():
        st.markdown(f"**{category}**")

        cols = st.columns(len(features))
        for idx, (flag, name, description) in enumerate(features):
            with cols[idx]:
                current_value = current_flags.get(flag.value, False)
                new_value = st.checkbox(
                    name,
                    value=current_value,
                    key=f"feature_{flag.value}",
                    help=description
                )

                if new_value != current_value:
                    lab_service.set_feature_flag(flag, new_value)
                    changed = True

        st.divider()

    if changed:
        _save_lab_service_state(lab_service)

    # Quick presets
    st.markdown("**Quick Presets:**")
    preset_cols = st.columns(4)

    with preset_cols[0]:
        if st.button("All On", key="preset_all_on", use_container_width=True):
            for flag in FeatureFlag:
                lab_service.set_feature_flag(flag, True)
            _save_lab_service_state(lab_service)
            st.rerun()

    with preset_cols[1]:
        if st.button("All Off", key="preset_all_off", use_container_width=True):
            for flag in FeatureFlag:
                lab_service.set_feature_flag(flag, False)
            _save_lab_service_state(lab_service)
            st.rerun()

    with preset_cols[2]:
        if st.button("Voice Only", key="preset_voice", use_container_width=True):
            for flag in FeatureFlag:
                enabled = flag in [FeatureFlag.REAL_TIME_TAGGING, FeatureFlag.CLICK_TO_RANT, FeatureFlag.FLASH_LABELS]
                lab_service.set_feature_flag(flag, enabled)
            _save_lab_service_state(lab_service)
            st.rerun()

    with preset_cols[3]:
        if st.button("Visual Only", key="preset_visual", use_container_width=True):
            for flag in FeatureFlag:
                enabled = flag in [FeatureFlag.FLASH_LABELS, FeatureFlag.TAG_OVERLAY, FeatureFlag.MULTI_PANEL_VIEW, FeatureFlag.GAP_DETECTION]
                lab_service.set_feature_flag(flag, enabled)
            _save_lab_service_state(lab_service)
            st.rerun()


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================


def render_configuration_manager(lab_service: LabService) -> None:
    """
    Render configuration save/load UI.

    Args:
        lab_service: LabService instance
    """
    st.markdown("### Saved Configurations")
    st.caption("Save and load test configurations for A/B testing.")

    # List existing configurations
    configs = lab_service.list_test_configs()

    if configs:
        st.markdown("**Saved Configurations:**")

        for config in configs:
            with st.expander(f"{config.name}", expanded=False):
                st.caption(config.description or "No description")
                st.caption(f"Created: {config.created_at.strftime('%Y-%m-%d %H:%M')}")

                # Show enabled features
                enabled_features = [k for k, v in config.feature_flags.items() if v]
                st.markdown(f"**Enabled Features:** {', '.join(enabled_features) or 'None'}")

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Load", key=f"load_config_{config.id}"):
                        lab_service.load_test_config(config.id)
                        _save_lab_service_state(lab_service)
                        show_success(f"Loaded configuration: {config.name}")
                        st.rerun()

                with col2:
                    if st.button("Update", key=f"update_config_{config.id}"):
                        lab_service.update_test_config(config.id)
                        _save_lab_service_state(lab_service)
                        show_success(f"Updated configuration: {config.name}")

                with col3:
                    if st.button("Delete", key=f"delete_config_{config.id}"):
                        lab_service.delete_test_config(config.id)
                        _save_lab_service_state(lab_service)
                        show_success(f"Deleted configuration: {config.name}")
                        st.rerun()
    else:
        st.info("No saved configurations yet. Create one below!")

    st.divider()

    # Create new configuration
    st.markdown("**Create New Configuration:**")

    with st.form("create_config_form"):
        config_name = st.text_input(
            "Configuration Name",
            placeholder="e.g., Voice-Only Test"
        )

        config_description = st.text_area(
            "Description (optional)",
            placeholder="Describe what this configuration tests..."
        )

        submitted = st.form_submit_button("Save Current Settings as Configuration")

        if submitted:
            if not config_name or not config_name.strip():
                show_error("Configuration name is required")
            else:
                config = lab_service.create_test_config(
                    name=config_name.strip(),
                    description=config_description.strip() if config_description else ""
                )
                _save_lab_service_state(lab_service)
                show_success(f"Created configuration: {config_name}")
                st.rerun()


# ============================================================================
# CONFIG LEVERS (Settings Panel)
# ============================================================================


def render_config_levers(lab_service: LabService) -> None:
    """
    Render Config Levers - adjustable settings panel.

    Args:
        lab_service: LabService instance
    """
    st.markdown("### Config Levers")
    st.caption("Fine-tune how features behave without code changes.")

    config = lab_service.get_config()
    changed = False

    # General Settings
    st.markdown("#### General")

    col1, col2 = st.columns(2)

    with col1:
        auto_detect = st.checkbox(
            "Auto-detect nodes",
            value=config.auto_detect_nodes,
            key="config_auto_detect",
            help="Automatically detect design nodes from chat"
        )
        if auto_detect != config.auto_detect_nodes:
            config.auto_detect_nodes = auto_detect
            changed = True

    with col2:
        sensitivity_options = {
            "Low": DetectionSensitivity.LOW,
            "Medium": DetectionSensitivity.MEDIUM,
            "High": DetectionSensitivity.HIGH,
        }
        current_sensitivity = [k for k, v in sensitivity_options.items() if v == config.detection_sensitivity][0]

        new_sensitivity = st.selectbox(
            "Detection Sensitivity",
            options=list(sensitivity_options.keys()),
            index=list(sensitivity_options.keys()).index(current_sensitivity),
            key="config_sensitivity",
            help="How aggressively to detect content"
        )
        if sensitivity_options[new_sensitivity] != config.detection_sensitivity:
            config.detection_sensitivity = sensitivity_options[new_sensitivity]
            changed = True

    timing_options = {
        "Immediate": FlashLabelTiming.IMMEDIATE,
        "After 5 seconds": FlashLabelTiming.AFTER_5S,
        "Manual only": FlashLabelTiming.MANUAL,
    }
    current_timing = [k for k, v in timing_options.items() if v == config.flash_label_timing][0]

    new_timing = st.selectbox(
        "Flash Label Timing",
        options=list(timing_options.keys()),
        index=list(timing_options.keys()).index(current_timing),
        key="config_flash_timing",
        help="When to show flash labels"
    )
    if timing_options[new_timing] != config.flash_label_timing:
        config.flash_label_timing = timing_options[new_timing]
        changed = True

    st.divider()

    # Voice Settings
    st.markdown("#### Voice")

    col1, col2 = st.columns(2)

    with col1:
        transcription_model = st.text_input(
            "Transcription Model",
            value=config.transcription_model,
            key="config_transcription_model",
            help="OpenAI Whisper model to use"
        )
        if transcription_model != config.transcription_model:
            config.transcription_model = transcription_model
            changed = True

    with col2:
        timeout_options = {
            "5 seconds": 5,
            "10 seconds": 10,
            "30 seconds": 30,
            "60 seconds": 60,
        }
        current_timeout = [k for k, v in timeout_options.items() if v == config.voice_timeout]
        current_timeout = current_timeout[0] if current_timeout else "30 seconds"

        new_timeout = st.selectbox(
            "Voice Timeout",
            options=list(timeout_options.keys()),
            index=list(timeout_options.keys()).index(current_timeout),
            key="config_voice_timeout",
            help="Maximum recording duration"
        )
        if timeout_options[new_timeout] != config.voice_timeout:
            config.voice_timeout = timeout_options[new_timeout]
            changed = True

    st.divider()

    # Display Settings
    st.markdown("#### Display")

    col1, col2 = st.columns(2)

    with col1:
        layout_options = {
            "Standard": PanelLayout.STANDARD,
            "Cockpit": PanelLayout.COCKPIT,
        }
        current_layout = [k for k, v in layout_options.items() if v == config.panel_layout][0]

        new_layout = st.selectbox(
            "Panel Layout",
            options=list(layout_options.keys()),
            index=list(layout_options.keys()).index(current_layout),
            key="config_panel_layout",
            help="Default panel layout mode"
        )
        if layout_options[new_layout] != config.panel_layout:
            config.panel_layout = layout_options[new_layout]
            changed = True

    with col2:
        theme_options = {
            "Default": ColorTheme.DEFAULT,
            "High Contrast": ColorTheme.HIGH_CONTRAST,
        }
        current_theme = [k for k, v in theme_options.items() if v == config.color_theme][0]

        new_theme = st.selectbox(
            "Color Theme",
            options=list(theme_options.keys()),
            index=list(theme_options.keys()).index(current_theme),
            key="config_color_theme",
            help="UI color scheme"
        )
        if theme_options[new_theme] != config.color_theme:
            config.color_theme = theme_options[new_theme]
            changed = True

    speed_options = {
        "Off": AnimationSpeed.OFF,
        "Fast": AnimationSpeed.FAST,
        "Normal": AnimationSpeed.NORMAL,
    }
    current_speed = [k for k, v in speed_options.items() if v == config.animation_speed][0]

    new_speed = st.selectbox(
        "Animation Speed",
        options=list(speed_options.keys()),
        index=list(speed_options.keys()).index(current_speed),
        key="config_animation_speed",
        help="Speed of UI animations"
    )
    if speed_options[new_speed] != config.animation_speed:
        config.animation_speed = speed_options[new_speed]
        changed = True

    st.divider()

    # Agent OS Settings
    st.markdown("#### Agent OS")

    col1, col2 = st.columns(2)

    with col1:
        sections_options = {
            "Minimal": RequiredSections.MINIMAL,
            "Standard": RequiredSections.STANDARD,
            "Complete": RequiredSections.COMPLETE,
        }
        current_sections = [k for k, v in sections_options.items() if v == config.required_sections][0]

        new_sections = st.selectbox(
            "Required Sections",
            options=list(sections_options.keys()),
            index=list(sections_options.keys()).index(current_sections),
            key="config_required_sections",
            help="How many sections required for 'complete' status"
        )
        if sections_options[new_sections] != config.required_sections:
            config.required_sections = sections_options[new_sections]
            changed = True

    with col2:
        gap_threshold = st.slider(
            "Gap Threshold (%)",
            min_value=50,
            max_value=90,
            value=config.gap_threshold,
            step=10,
            key="config_gap_threshold",
            help="Minimum completion % to consider section done"
        )
        if gap_threshold != config.gap_threshold:
            config.gap_threshold = gap_threshold
            changed = True

    auto_consolidate = st.checkbox(
        "Auto-Consolidate",
        value=config.auto_consolidate,
        key="config_auto_consolidate",
        help="Automatically organize content as you type"
    )
    if auto_consolidate != config.auto_consolidate:
        config.auto_consolidate = auto_consolidate
        changed = True

    # Save changes
    if changed:
        lab_service.set_config(config)
        _save_lab_service_state(lab_service)

    st.divider()

    # Reset button
    if st.button("Reset Config to Defaults", key="reset_config_defaults"):
        lab_service.reset_config()
        _save_lab_service_state(lab_service)
        show_success("Configuration reset to defaults!")
        st.rerun()


# ============================================================================
# TEST SESSION CONTROLS
# ============================================================================


def render_test_session_controls(lab_service: LabService) -> None:
    """
    Render test session start/stop controls.

    Args:
        lab_service: LabService instance
    """
    st.markdown("### Test Session")
    st.caption("Track metrics while testing a specific configuration.")

    current_test = lab_service.get_current_test()

    if current_test:
        # Show active test session
        st.markdown("""
        <div style="
            background: #065f46;
            border: 1px solid #10b981;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        ">
            <h4 style="color: #10b981; margin: 0;">Test Session Active</h4>
        </div>
        """, unsafe_allow_html=True)

        # Show running metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            elapsed = datetime.utcnow() - current_test.session_start
            st.metric("Duration", f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s")

        with col2:
            st.metric("Rants", current_test.total_rants)

        with col3:
            st.metric("Words", current_test.total_words)

        # End session form
        st.markdown("**End Test Session:**")

        notes = st.text_area(
            "Session Notes",
            placeholder="What did you observe? What worked well?",
            key="test_session_notes"
        )

        rating = st.slider(
            "Rate this configuration (1-5)",
            min_value=1,
            max_value=5,
            value=3,
            key="test_session_rating"
        )

        if st.button("End Test Session", type="primary", key="end_test_session"):
            # Get current completion from Agent OS
            doc = st.session_state.get("agent_os_doc")
            final_completion = doc.calculate_completion() if doc else 0

            metrics = lab_service.end_test_session(
                final_completion=final_completion,
                notes=notes,
                rating=rating
            )

            _save_lab_service_state(lab_service)
            show_success("Test session completed and metrics saved!")
            st.rerun()

    else:
        # Show start test session
        st.info("No active test session. Start one to track metrics.")

        st.markdown("**Start New Test Session:**")

        # Select configuration to test
        configs = lab_service.list_test_configs()

        if configs:
            config_options = {c.name: c.id for c in configs}
            selected_config = st.selectbox(
                "Select Configuration",
                options=["Current Settings"] + list(config_options.keys()),
                key="test_config_select"
            )

            if st.button("Start Test Session", type="primary", key="start_test_session"):
                config_id = ""
                if selected_config != "Current Settings":
                    config_id = config_options[selected_config]
                    lab_service.load_test_config(config_id)

                # Get initial completion
                doc = st.session_state.get("agent_os_doc")
                initial_completion = doc.calculate_completion() if doc else 0

                lab_service.start_test_session(
                    config_id=config_id or "current",
                    initial_completion=initial_completion
                )

                _save_lab_service_state(lab_service)
                show_success("Test session started!")
                st.rerun()
        else:
            if st.button("Start Test with Current Settings", type="primary", key="start_test_current"):
                doc = st.session_state.get("agent_os_doc")
                initial_completion = doc.calculate_completion() if doc else 0

                lab_service.start_test_session(
                    config_id="current",
                    initial_completion=initial_completion
                )

                _save_lab_service_state(lab_service)
                show_success("Test session started!")
                st.rerun()


# ============================================================================
# METRICS VIEW
# ============================================================================


def render_metrics_view(lab_service: LabService) -> None:
    """
    Render test metrics history and comparison.

    Args:
        lab_service: LabService instance
    """
    st.markdown("### Test Metrics")
    st.caption("View and compare results from test sessions.")

    metrics_history = lab_service.get_metrics_history()

    if not metrics_history:
        st.info("No test sessions completed yet. Complete a test session to see metrics here.")
        return

    # Summary stats
    st.markdown("**Overall Summary:**")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tests", len(metrics_history))

    with col2:
        avg_rating = sum(m.rating or 0 for m in metrics_history) / len(metrics_history)
        st.metric("Avg Rating", f"{avg_rating:.1f}/5")

    with col3:
        total_words = sum(m.total_words for m in metrics_history)
        st.metric("Total Words", total_words)

    with col4:
        avg_completion_gain = sum(
            (m.completion_end - m.completion_start) for m in metrics_history
        ) / len(metrics_history)
        st.metric("Avg Completion Gain", f"+{avg_completion_gain:.1f}%")

    st.divider()

    # Individual test results
    st.markdown("**Test History:**")

    for idx, metrics in enumerate(reversed(metrics_history)):
        with st.expander(
            f"Test #{len(metrics_history) - idx}: {metrics.session_start.strftime('%Y-%m-%d %H:%M')}",
            expanded=False
        ):
            # Duration
            if metrics.session_end:
                duration = metrics.session_end - metrics.session_start
                st.markdown(f"**Duration:** {duration.seconds // 60}m {duration.seconds % 60}s")

            # Metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Words", metrics.total_words)
                st.metric("Rants", metrics.total_rants)

            with col2:
                st.metric("Start Completion", f"{metrics.completion_start}%")
                st.metric("End Completion", f"{metrics.completion_end}%")

            with col3:
                st.metric(
                    "Completion Gain",
                    f"+{metrics.completion_end - metrics.completion_start}%"
                )
                if metrics.rating:
                    st.metric("Rating", f"{metrics.rating}/5")

            # Features used
            if metrics.features_used:
                st.markdown("**Features Used:**")
                for feature, count in metrics.features_used.items():
                    st.markdown(f"- {feature}: {count} times")

            # Notes
            if metrics.notes:
                st.markdown("**Notes:**")
                st.markdown(f"_{metrics.notes}_")

    st.divider()

    # Clear history
    if st.button("Clear Metrics History", key="clear_metrics"):
        lab_service._metrics_history = []
        _save_lab_service_state(lab_service)
        show_success("Metrics history cleared!")
        st.rerun()


# ============================================================================
# COMPACT LAB MODE INDICATOR
# ============================================================================


def render_lab_mode_indicator() -> None:
    """
    Render a compact Lab Mode indicator for display in other panels.

    Shows active status and quick toggle.
    """
    if st.session_state.get("lab_mode_active", False):
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #065f46, #047857);
            border-radius: 6px;
            padding: 4px 12px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            color: white;
        ">
            <span style="font-weight: 600;">LAB MODE</span>
            <span style="opacity: 0.8;">Testing active</span>
        </div>
        """, unsafe_allow_html=True)


def is_feature_enabled(feature: FeatureFlag) -> bool:
    """
    Check if a feature is enabled (considering Lab Mode).

    Args:
        feature: Feature flag to check

    Returns:
        True if feature is enabled
    """
    lab_service = st.session_state.get("lab_service")

    if lab_service and lab_service.is_lab_mode_active():
        return lab_service.is_feature_enabled(feature)

    # Default: all features enabled in standard mode
    return DEFAULT_FEATURE_FLAGS.get(feature, True)
