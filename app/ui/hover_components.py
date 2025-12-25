"""
Hover-based UI components for Streamlit.

Provides hover-to-open dropdowns that:
1. Open on hover (no click needed)
2. Stay open on click (pinned)
3. Close when clicking elsewhere

Uses CSS + JavaScript injection for hover behavior.
"""

import streamlit as st
from typing import Callable, Optional, Any, List, Dict
import uuid
import json


def inject_hover_styles_and_scripts():
    """Inject CSS and JavaScript for hover dropdown behavior. Call once per page."""
    st.markdown("""
    <style>
    /* ========================================
       HOVER DROPDOWN SYSTEM
       ======================================== */

    /* Control bar layout */
    .hd-control-bar {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 4px 0;
        margin-bottom: 8px;
    }

    /* Hover dropdown container */
    .hd-container {
        position: relative;
        display: inline-block;
    }

    /* The trigger button */
    .hd-trigger {
        background: linear-gradient(180deg, #2a2a2a 0%, #1e1e1e 100%);
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        padding: 8px 14px;
        color: #e0e0e0;
        cursor: pointer;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.15s ease;
        white-space: nowrap;
        user-select: none;
    }

    .hd-trigger:hover,
    .hd-container:hover .hd-trigger {
        background: linear-gradient(180deg, #3a3a3a 0%, #2a2a2a 100%);
        border-color: #4a9eff;
        color: #fff;
        box-shadow: 0 0 12px rgba(74, 158, 255, 0.5), 0 0 24px rgba(74, 158, 255, 0.25);
    }

    .hd-trigger.active,
    .hd-container.pinned .hd-trigger {
        background: #4a9eff;
        border-color: #4a9eff;
        color: #fff;
        box-shadow: 0 0 16px rgba(74, 158, 255, 0.6), 0 0 32px rgba(74, 158, 255, 0.3);
    }

    /* Dropdown panel - hidden by default */
    .hd-panel {
        display: none;
        position: absolute;
        top: calc(100% + 4px);
        left: 0;
        min-width: 300px;
        max-width: 450px;
        max-height: 500px;
        overflow-y: auto;
        background: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 10px;
        padding: 16px;
        z-index: 9999;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }

    /* Show panel when container is hovered OR pinned */
    .hd-container:hover .hd-panel,
    .hd-container.pinned .hd-panel {
        display: block;
    }

    /* Pinned state indicator */
    .hd-container.pinned .hd-trigger {
        border-color: #4a9eff;
        box-shadow: 0 0 8px rgba(74, 158, 255, 0.3);
    }

    .hd-container.pinned .hd-panel {
        border-color: #4a9eff;
    }

    /* Right-aligned panels */
    .hd-panel.align-right {
        left: auto;
        right: 0;
    }

    /* Panel header */
    .hd-header {
        font-weight: 600;
        font-size: 14px;
        color: #ffffff;
        margin-bottom: 12px;
        padding-bottom: 10px;
        border-bottom: 1px solid #3a3a3a;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Pin toggle */
    .hd-pin {
        background: transparent;
        border: none;
        color: #666;
        cursor: pointer;
        padding: 4px 8px;
        font-size: 14px;
        border-radius: 4px;
        transition: all 0.15s;
    }

    .hd-pin:hover {
        background: #2a2a2a;
        color: #4a9eff;
    }

    .hd-container.pinned .hd-pin {
        color: #4a9eff;
    }

    /* Panel sections */
    .hd-section {
        margin: 12px 0;
    }

    .hd-section-title {
        color: #888;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }

    /* Divider */
    .hd-divider {
        height: 1px;
        background: #3a3a3a;
        margin: 12px 0;
    }

    /* ========================================
       HISTORY INDICATORS
       ======================================== */

    .hist-row {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 0;
        flex-wrap: wrap;
    }

    .hist-label {
        color: #666;
        font-size: 12px;
        margin-right: 8px;
    }

    /* Individual history indicator */
    .hist-item {
        position: relative;
        display: inline-block;
    }

    .hist-btn {
        min-width: 32px;
        height: 28px;
        line-height: 28px;
        text-align: center;
        background: #2a2a2a;
        border: 1px solid #3a3a3a;
        border-radius: 5px;
        font-size: 12px;
        color: #888;
        cursor: pointer;
        transition: all 0.15s;
        padding: 0 6px;
    }

    .hist-btn:hover,
    .hist-item:hover .hist-btn {
        background: #3a3a3a;
        border-color: #4a9eff;
        color: #fff;
        box-shadow: 0 0 10px rgba(74, 158, 255, 0.5), 0 0 20px rgba(74, 158, 255, 0.25);
    }

    .hist-btn.current {
        background: linear-gradient(180deg, #4a9eff 0%, #3a7edf 100%);
        border-color: #4a9eff;
        color: #fff;
        font-weight: 600;
        box-shadow: 0 0 8px rgba(74, 158, 255, 0.4);
    }

    .hist-btn.pinned {
        border-color: #4a9eff;
        color: #4a9eff;
        box-shadow: 0 0 6px rgba(74, 158, 255, 0.3);
    }

    /* History preview panel */
    .hist-preview {
        display: none;
        position: absolute;
        bottom: calc(100% + 6px);
        left: 50%;
        transform: translateX(-50%);
        min-width: 260px;
        max-width: 350px;
        background: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        padding: 12px;
        z-index: 9999;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.4);
    }

    .hist-item:hover .hist-preview {
        display: block;
    }

    /* Summary bullets */
    .hist-summary {
        margin-bottom: 8px;
    }

    .summary-bullet {
        display: block;
        padding: 3px 0;
        font-weight: 500;
        font-size: 13px;
        color: #e0e0e0;
    }

    .hist-meta {
        color: #666;
        font-size: 11px;
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #3a3a3a;
    }

    .hist-actions {
        margin-top: 8px;
        padding-top: 8px;
        border-top: 1px solid #3a3a3a;
        text-align: center;
    }

    .hist-pin-btn {
        background: #2a2a2a;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        color: #aaa;
        padding: 4px 12px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.15s;
    }

    .hist-pin-btn:hover {
        background: #4a9eff;
        border-color: #4a9eff;
        color: #fff;
    }
    </style>

    <script>
    // Handle pin toggle for dropdowns
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('hd-pin')) {
            const container = e.target.closest('.hd-container');
            if (container) {
                container.classList.toggle('pinned');
            }
        }
    });

    // Handle history pin buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('hist-pin-btn')) {
            const itemId = e.target.dataset.id;
            // Trigger Streamlit callback via hidden button
            const btn = document.querySelector(`button[data-pin-id="${itemId}"]`);
            if (btn) btn.click();
        }
    });
    </script>
    """, unsafe_allow_html=True)


def inject_hover_styles():
    """Inject CSS for hover dropdown behavior. Call once per page."""
    st.markdown("""
    <style>
    /* Hover dropdown container */
    .hover-dropdown {
        position: relative;
        display: inline-block;
    }

    /* The trigger button */
    .hover-trigger {
        background: #1e1e1e;
        border: 1px solid #3a3a3a;
        border-radius: 6px;
        padding: 6px 12px;
        color: #e0e0e0;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s;
        white-space: nowrap;
    }

    .hover-trigger:hover {
        background: #2a2a2a;
        border-color: #4a4a4a;
    }

    /* Dropdown content - hidden by default */
    .hover-content {
        visibility: hidden;
        opacity: 0;
        position: absolute;
        top: 100%;
        left: 0;
        min-width: 280px;
        max-width: 400px;
        background: #1a1a1a;
        border: 1px solid #3a3a3a;
        border-radius: 8px;
        padding: 12px;
        z-index: 1000;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        transition: opacity 0.15s, visibility 0.15s;
        margin-top: 4px;
    }

    /* Show on hover */
    .hover-dropdown:hover .hover-content {
        visibility: visible;
        opacity: 1;
    }

    /* Pinned state - always visible */
    .hover-content.pinned {
        visibility: visible !important;
        opacity: 1 !important;
        border-color: #4a9eff;
    }

    /* Right-aligned dropdowns (for items near right edge) */
    .hover-content.align-right {
        left: auto;
        right: 0;
    }

    /* Dropdown header */
    .dropdown-header {
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid #3a3a3a;
    }

    /* Dropdown sections */
    .dropdown-section {
        margin: 8px 0;
        padding: 8px 0;
        border-bottom: 1px solid #2a2a2a;
    }

    .dropdown-section:last-child {
        border-bottom: none;
    }

    /* Labels */
    .dropdown-label {
        color: #888;
        font-size: 12px;
        margin-bottom: 4px;
    }

    /* Values */
    .dropdown-value {
        color: #e0e0e0;
        font-size: 14px;
    }

    /* Metric display */
    .dropdown-metric {
        display: inline-block;
        background: #2a2a2a;
        padding: 4px 8px;
        border-radius: 4px;
        margin: 2px;
        font-size: 13px;
    }

    /* Pin button */
    .pin-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        background: transparent;
        border: none;
        color: #666;
        cursor: pointer;
        padding: 4px;
        font-size: 14px;
    }

    .pin-btn:hover {
        color: #4a9eff;
    }

    .pin-btn.pinned {
        color: #4a9eff;
    }

    /* History indicator buttons */
    .history-indicator {
        display: inline-block;
        min-width: 28px;
        height: 28px;
        line-height: 28px;
        text-align: center;
        background: #2a2a2a;
        border: 1px solid #3a3a3a;
        border-radius: 4px;
        margin: 0 2px;
        font-size: 12px;
        color: #aaa;
        cursor: pointer;
        transition: all 0.15s;
    }

    .history-indicator:hover {
        background: #3a3a3a;
        border-color: #4a4a4a;
        color: #fff;
    }

    .history-indicator.current {
        background: #4a9eff;
        border-color: #4a9eff;
        color: #fff;
    }

    .history-indicator.pinned {
        border-color: #4a9eff;
        color: #4a9eff;
    }

    /* Summary bullets in dropdown */
    .summary-bullet {
        display: block;
        padding: 2px 0;
        font-weight: 500;
        color: #e0e0e0;
    }

    /* Control bar container */
    .control-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 0;
        flex-wrap: wrap;
    }

    /* Divider */
    .dropdown-divider {
        height: 1px;
        background: #3a3a3a;
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)


def hover_dropdown(
    trigger_label: str,
    dropdown_id: str,
    align_right: bool = False,
) -> bool:
    """
    Create a hover dropdown trigger.

    Returns True if this dropdown should show its Streamlit content
    (either hovered or pinned).

    Usage:
        if hover_dropdown("⚙️ 66%", "settings"):
            st.slider("Threshold", 0, 100)
            # ... more controls
    """
    pinned_key = f"pinned_dropdown_{dropdown_id}"
    is_pinned = st.session_state.get(pinned_key, False)

    # Render the HTML trigger
    pinned_class = "pinned" if is_pinned else ""
    align_class = "align-right" if align_right else ""

    # We use a unique container for each dropdown
    container_id = f"dropdown_{dropdown_id}"

    st.markdown(f"""
    <div class="hover-dropdown" id="{container_id}">
        <div class="hover-trigger">{trigger_label}</div>
        <div class="hover-content {pinned_class} {align_class}">
            <div id="content_{dropdown_id}"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Return pinned state - actual content rendered by caller
    return is_pinned


def render_hover_control_bar(controls: list):
    """
    Render a row of hover dropdown controls.

    Args:
        controls: List of dicts with {label, id, content_func, align_right}
    """
    inject_hover_styles()

    # Create the control bar
    html_parts = ['<div class="control-bar">']

    for ctrl in controls:
        label = ctrl["label"]
        ctrl_id = ctrl["id"]
        align = "align-right" if ctrl.get("align_right") else ""
        pinned = st.session_state.get(f"pinned_{ctrl_id}", False)
        pinned_class = "pinned" if pinned else ""

        html_parts.append(f"""
        <div class="hover-dropdown">
            <div class="hover-trigger">{label}</div>
            <div class="hover-content {align} {pinned_class}">
                <div class="dropdown-header">{ctrl.get('title', label)}</div>
                <div id="content_{ctrl_id}">
                    <!-- Streamlit content injected below -->
                </div>
            </div>
        </div>
        """)

    html_parts.append('</div>')

    st.markdown("".join(html_parts), unsafe_allow_html=True)


def history_indicator_row(
    exchanges: list,
    pinned_ids: list,
    current_id: int,
    on_pin: Callable[[int], None],
    on_unpin: Callable[[int], None],
):
    """
    Render a row of history indicators with hover previews.

    Args:
        exchanges: List of exchange dicts
        pinned_ids: List of pinned exchange IDs
        current_id: Current exchange ID
        on_pin: Callback when pinning an exchange
        on_unpin: Callback when unpinning
    """
    if not exchanges:
        st.caption("History: No exchanges yet")
        return

    # Build the HTML for indicators
    html = ['<div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">']
    html.append('<span style="color: #888; font-size: 12px; margin-right: 8px;">History:</span>')

    for ex in exchanges[-20:]:  # Show last 20
        ex_id = ex["id"]

        # Determine class
        classes = ["history-indicator"]
        if ex_id == current_id:
            classes.append("current")
            label = f"{ex_id}▣"
        elif ex_id in pinned_ids:
            classes.append("pinned")
            label = f"{ex_id}●"
        else:
            label = str(ex_id)

        # Get summary for tooltip
        summary = ex.get("summary", [])
        summary_text = " | ".join(summary) if summary else ex.get("prompt", "")[:50]

        html.append(f"""
        <div class="hover-dropdown">
            <div class="{' '.join(classes)}">{label}</div>
            <div class="hover-content">
                <div class="dropdown-header">Exchange #{ex_id}</div>
        """)

        # Summary bullets
        if summary:
            for bullet in summary:
                html.append(f'<span class="summary-bullet">{bullet}</span>')

        html.append(f"""
                <div class="dropdown-divider"></div>
                <div class="dropdown-label">Prompt:</div>
                <div class="dropdown-value">{ex.get('prompt', '')[:100]}...</div>
                <div class="dropdown-divider"></div>
                <div style="font-size: 12px; color: #666;">Click to {'unpin' if ex_id in pinned_ids else 'pin'}</div>
            </div>
        </div>
        """)

    html.append('</div>')

    st.markdown("".join(html), unsafe_allow_html=True)

    # Render actual Streamlit buttons for pin/unpin functionality
    # These are hidden but functional
    cols = st.columns(len(exchanges[-20:]) + 2)
    with cols[0]:
        st.empty()  # Spacer for "History:" label

    for i, ex in enumerate(exchanges[-20:]):
        with cols[i + 1]:
            ex_id = ex["id"]
            if ex_id in pinned_ids:
                if st.button("📌", key=f"hist_unpin_{ex_id}", help="Unpin"):
                    on_unpin(ex_id)
            else:
                if st.button("📍", key=f"hist_pin_{ex_id}", help="Pin"):
                    on_pin(ex_id)


def create_hover_dropdown_html(
    label: str,
    content_html: str,
    dropdown_id: str,
    align_right: bool = False,
    is_pinned: bool = False,
) -> str:
    """
    Create HTML for a single hover dropdown.

    Returns HTML string to be used with st.markdown(unsafe_allow_html=True)
    """
    align_class = "align-right" if align_right else ""
    pinned_class = "pinned" if is_pinned else ""

    return f"""
    <div class="hover-dropdown">
        <div class="hover-trigger">{label}</div>
        <div class="hover-content {align_class} {pinned_class}">
            {content_html}
        </div>
    </div>
    """
