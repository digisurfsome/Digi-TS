"""
UI layout components and helpers for Streamlit.

This module provides reusable UI components and layout functions.
"""

import streamlit as st
from typing import Optional


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
