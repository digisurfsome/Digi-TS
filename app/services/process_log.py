"""
Process Log Service - Real-time activity and debug logging.

Provides a way to track operations, errors, and timing information
for debugging and monitoring the application.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import streamlit as st


class LogLevel(Enum):
    """Log entry severity levels."""
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    level: LogLevel
    category: str
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            "timestamp": self.timestamp.strftime("%H:%M:%S.%f")[:-3],
            "level": self.level.value,
            "category": self.category,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
        }


class ProcessLog:
    """
    Process logging service using Streamlit session state.

    Stores logs in session state so they persist across reruns
    but are cleared when the session ends.
    """

    MAX_ENTRIES = 200  # Keep last N entries to prevent memory issues
    SESSION_KEY = "process_log_entries"

    @classmethod
    def _get_entries(cls) -> List[LogEntry]:
        """Get log entries from session state."""
        if cls.SESSION_KEY not in st.session_state:
            st.session_state[cls.SESSION_KEY] = []
        return st.session_state[cls.SESSION_KEY]

    @classmethod
    def _add_entry(cls, entry: LogEntry) -> None:
        """Add entry to session state."""
        entries = cls._get_entries()
        entries.append(entry)
        # Trim old entries
        if len(entries) > cls.MAX_ENTRIES:
            st.session_state[cls.SESSION_KEY] = entries[-cls.MAX_ENTRIES:]

    @classmethod
    def log(
        cls,
        level: LogLevel,
        category: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """
        Add a log entry.

        Args:
            level: Log severity level
            category: Category/component name (e.g., "Chat", "Database", "AI")
            message: Log message
            details: Optional additional details
            duration_ms: Optional operation duration in milliseconds
        """
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            details=details,
            duration_ms=duration_ms
        )
        cls._add_entry(entry)

    @classmethod
    def debug(cls, category: str, message: str, **kwargs) -> None:
        """Log a debug message."""
        cls.log(LogLevel.DEBUG, category, message, **kwargs)

    @classmethod
    def info(cls, category: str, message: str, **kwargs) -> None:
        """Log an info message."""
        cls.log(LogLevel.INFO, category, message, **kwargs)

    @classmethod
    def success(cls, category: str, message: str, **kwargs) -> None:
        """Log a success message."""
        cls.log(LogLevel.SUCCESS, category, message, **kwargs)

    @classmethod
    def warning(cls, category: str, message: str, **kwargs) -> None:
        """Log a warning message."""
        cls.log(LogLevel.WARNING, category, message, **kwargs)

    @classmethod
    def error(cls, category: str, message: str, **kwargs) -> None:
        """Log an error message."""
        cls.log(LogLevel.ERROR, category, message, **kwargs)

    @classmethod
    def get_entries(
        cls,
        level_filter: Optional[LogLevel] = None,
        category_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[LogEntry]:
        """
        Get log entries with optional filtering.

        Args:
            level_filter: Only return entries of this level or higher
            category_filter: Only return entries from this category
            limit: Maximum number of entries to return

        Returns:
            List of log entries, newest first
        """
        entries = cls._get_entries()

        # Filter by level
        if level_filter:
            level_order = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.SUCCESS, LogLevel.WARNING, LogLevel.ERROR]
            min_idx = level_order.index(level_filter)
            entries = [e for e in entries if level_order.index(e.level) >= min_idx]

        # Filter by category
        if category_filter:
            entries = [e for e in entries if e.category.lower() == category_filter.lower()]

        # Return newest first, limited
        return list(reversed(entries[-limit:]))

    @classmethod
    def clear(cls) -> None:
        """Clear all log entries."""
        st.session_state[cls.SESSION_KEY] = []

    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of unique categories in the log."""
        entries = cls._get_entries()
        return list(set(e.category for e in entries))


def render_process_log(
    show_filters: bool = True,
    max_height: int = 400
) -> None:
    """
    Render the process log UI component.

    Args:
        show_filters: Whether to show filter controls
        max_height: Maximum height of the log container in pixels
    """
    st.subheader("Process Log")

    # Filter controls
    if show_filters:
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            level_options = ["All"] + [l.value.title() for l in LogLevel]
            selected_level = st.selectbox(
                "Level",
                level_options,
                key="process_log_level_filter"
            )
            level_filter = None if selected_level == "All" else LogLevel(selected_level.lower())

        with col2:
            categories = ["All"] + ProcessLog.get_categories()
            selected_category = st.selectbox(
                "Category",
                categories,
                key="process_log_category_filter"
            )
            category_filter = None if selected_category == "All" else selected_category

        with col3:
            limit = st.number_input(
                "Show",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                key="process_log_limit"
            )

        with col4:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("Clear Log", key="clear_process_log"):
                ProcessLog.clear()
                st.rerun()
    else:
        level_filter = None
        category_filter = None
        limit = 50

    # Get filtered entries
    entries = ProcessLog.get_entries(
        level_filter=level_filter,
        category_filter=category_filter,
        limit=limit
    )

    if not entries:
        st.info("No log entries yet. Activity will appear here as you use the app.")
        return

    # Level colors and icons
    level_styles = {
        LogLevel.DEBUG: ("gray", "🔍"),
        LogLevel.INFO: ("blue", "ℹ️"),
        LogLevel.SUCCESS: ("green", "✅"),
        LogLevel.WARNING: ("orange", "⚠️"),
        LogLevel.ERROR: ("red", "❌"),
    }

    # Render log entries
    log_container = st.container()

    with log_container:
        for entry in entries:
            color, icon = level_styles.get(entry.level, ("gray", "•"))

            # Build the log line
            time_str = entry.timestamp.strftime("%H:%M:%S")
            duration_str = f" ({entry.duration_ms:.0f}ms)" if entry.duration_ms else ""

            # Use markdown with colored text
            log_line = f"`{time_str}` {icon} **[{entry.category}]** {entry.message}{duration_str}"

            if entry.level == LogLevel.ERROR:
                st.error(log_line)
            elif entry.level == LogLevel.WARNING:
                st.warning(log_line)
            elif entry.level == LogLevel.SUCCESS:
                st.success(log_line)
            else:
                st.markdown(log_line)

            # Show details if present
            if entry.details:
                with st.expander("Details"):
                    st.json(entry.details)
