"""
Design Tree Studio - Main Streamlit Application

This is the entry point for the Streamlit application.
"""

import streamlit as st
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import settings
from app.core.db import test_connection
from app.ui.layout import (
    render_header,
    render_sidebar,
    render_footer,
    show_success,
    show_error,
    show_warning,
    show_info,
)


def main():
    """Main application entry point."""

    # Page configuration
    st.set_page_config(
        page_title=settings.APP_NAME,
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Render header
    render_header(
        settings.APP_NAME,
        "AI-Powered Design Management System",
    )

    # Render sidebar
    render_sidebar()

    # Main content
    st.header("System Status")

    # Check configuration
    st.subheader("Configuration Status")
    is_valid, errors = settings.validate()

    if is_valid:
        show_success("All required configuration is present")
    else:
        show_error("Configuration incomplete")
        for error in errors:
            st.markdown(f"- {error}")
        show_warning(
            "Please create a `.env` file in the project root with the required variables. "
            "See `.env.example` for reference."
        )

    # Test database connection
    st.subheader("Database Connection")

    if not settings.DATABASE_URL:
        show_warning(
            "Database not configured. Please set DATABASE_URL in your .env file."
        )
        st.code(
            """
# Example .env file:
DATABASE_URL=postgresql://user:password@host/database
OPENAI_API_KEY=sk-...
            """,
            language="bash",
        )
    else:
        with st.spinner("Testing database connection..."):
            success, message = test_connection()

            if success:
                show_success(message)
                st.info("✅ Database is ready for use!")
            else:
                show_error(message)
                st.markdown(
                    """
                    **Troubleshooting tips:**
                    - Verify your DATABASE_URL is correct
                    - Ensure your database is running and accessible
                    - Check network connectivity
                    - For Neon, ensure your connection string includes SSL parameters
                    """
                )

    # OpenAI configuration status
    st.subheader("OpenAI Configuration")
    if settings.OPENAI_API_KEY:
        show_success("OpenAI API key is configured")
        st.info(f"Using model: {settings.OPENAI_MODEL}")
    else:
        show_warning("OpenAI API key not configured")

    # Development info
    if settings.DEBUG:
        st.subheader("Debug Information")
        with st.expander("Show Debug Info"):
            st.json({
                "APP_NAME": settings.APP_NAME,
                "APP_VERSION": settings.APP_VERSION,
                "DEBUG": settings.DEBUG,
                "DATABASE_CONFIGURED": bool(settings.DATABASE_URL),
                "OPENAI_CONFIGURED": bool(settings.OPENAI_API_KEY),
                "OPENAI_MODEL": settings.OPENAI_MODEL,
            })

    # Render footer
    render_footer()


if __name__ == "__main__":
    main()
