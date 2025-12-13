"""
Session service for Phase 5: Learning & Memory.

Manages pause/resume functionality with time-based context refresh.
Tracks user activity and provides appropriate context when returning
after time away.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from dataclasses import dataclass
import openai
import os

from app.core.models import (
    SessionActivity,
    RefreshLevel,
    Project,
    RawRant,
    Idea,
    IdeaStatus,
)


# =============================================================================
# REFRESH LEVEL CONFIGURATION
# =============================================================================


@dataclass
class RefreshConfig:
    """Configuration for a refresh level."""
    level: RefreshLevel
    min_hours: float
    max_hours: float
    title: str
    description: str


REFRESH_LEVELS = [
    RefreshConfig(
        level=RefreshLevel.MINIMAL,
        min_hours=0,
        max_hours=1,
        title="Quick Return",
        description="Welcome back! Here's where you left off.",
    ),
    RefreshConfig(
        level=RefreshLevel.BRIEF,
        min_hours=1,
        max_hours=4,
        title="Brief Refresh",
        description="You've been away for a bit. Here's a quick summary.",
    ),
    RefreshConfig(
        level=RefreshLevel.MEDIUM,
        min_hours=4,
        max_hours=24,
        title="Session Recap",
        description="Welcome back! Let's recap where things stand.",
    ),
    RefreshConfig(
        level=RefreshLevel.FULL,
        min_hours=24,
        max_hours=72,
        title="Full Context",
        description="It's been a while. Here's everything you need to know.",
    ),
    RefreshConfig(
        level=RefreshLevel.EXTENDED,
        min_hours=72,
        max_hours=168,  # 7 days
        title="Extended Refresh",
        description="Welcome back after some time. Let's get you up to speed.",
    ),
    RefreshConfig(
        level=RefreshLevel.COMPLETE,
        min_hours=168,
        max_hours=float("inf"),
        title="Complete Refresh",
        description="It's been a while! Here's a full project overview.",
    ),
]


def get_refresh_level(hours_away: float) -> RefreshConfig:
    """
    Get the appropriate refresh level based on hours away.

    Args:
        hours_away: Number of hours since last activity

    Returns:
        RefreshConfig for the appropriate level
    """
    for config in REFRESH_LEVELS:
        if config.min_hours <= hours_away < config.max_hours:
            return config
    return REFRESH_LEVELS[-1]  # Complete refresh as fallback


# =============================================================================
# SESSION ACTIVITY TRACKING
# =============================================================================


def get_or_create_activity(
    db: Session,
    user_id: int,
    project_id: int,
) -> SessionActivity:
    """
    Get or create a session activity record.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        SessionActivity record
    """
    try:
        activity = (
            db.query(SessionActivity)
            .filter(
                and_(
                    SessionActivity.user_id == user_id,
                    SessionActivity.project_id == project_id,
                )
            )
            .first()
        )

        if not activity:
            now = datetime.utcnow()
            activity = SessionActivity(
                user_id=user_id,
                project_id=project_id,
                last_active=now,
                session_start=now,
                warmup_completed=False,
            )
            db.add(activity)
            db.commit()
            db.refresh(activity)

        return activity
    except Exception as e:
        # If table doesn't exist yet, create a mock activity
        # This allows the app to work before schema is updated
        if "session_activities" in str(e).lower() or "undefined" in str(e).lower():
            # Return a mock activity object
            mock = SessionActivity(
                user_id=user_id,
                project_id=project_id,
                last_active=datetime.utcnow(),
                session_start=datetime.utcnow(),
                warmup_completed=True,  # Skip warmup if table missing
            )
            mock.id = 0  # Indicate it's a mock
            return mock
        raise


def update_activity(
    db: Session,
    user_id: int,
    project_id: int,
    current_feature: Optional[str] = None,
    last_rant_excerpt: Optional[str] = None,
    agent_os_completion: Optional[float] = None,
    agent_os_gaps: Optional[List[str]] = None,
    session_state: Optional[Dict[str, Any]] = None,
) -> SessionActivity:
    """
    Update session activity with current state.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID
        current_feature: Feature being worked on
        last_rant_excerpt: Excerpt from last rant
        agent_os_completion: Agent OS completion percentage
        agent_os_gaps: List of Agent OS gaps
        session_state: Full session state snapshot

    Returns:
        Updated SessionActivity
    """
    activity = get_or_create_activity(db, user_id, project_id)

    activity.last_active = datetime.utcnow()

    if current_feature is not None:
        activity.current_feature = current_feature
    if last_rant_excerpt is not None:
        # Truncate to 500 chars
        activity.last_rant_excerpt = last_rant_excerpt[:500] if last_rant_excerpt else None
    if agent_os_completion is not None:
        activity.agent_os_completion = agent_os_completion
    if agent_os_gaps is not None:
        activity.agent_os_gaps = agent_os_gaps
    if session_state is not None:
        activity.session_state = session_state

    db.commit()
    db.refresh(activity)
    return activity


def record_activity_ping(db: Session, user_id: int, project_id: int) -> SessionActivity:
    """
    Simple ping to update last_active timestamp.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        Updated SessionActivity
    """
    activity = get_or_create_activity(db, user_id, project_id)
    activity.last_active = datetime.utcnow()
    db.commit()
    db.refresh(activity)
    return activity


def start_new_session(db: Session, user_id: int, project_id: int) -> SessionActivity:
    """
    Start a new work session.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        SessionActivity with new session start time
    """
    activity = get_or_create_activity(db, user_id, project_id)

    now = datetime.utcnow()
    activity.session_start = now
    activity.last_active = now
    # Reset warmup for new day
    if activity.warmup_completed_at:
        last_warmup_date = activity.warmup_completed_at.date()
        if last_warmup_date < now.date():
            activity.warmup_completed = False
            activity.warmup_completed_at = None

    db.commit()
    db.refresh(activity)
    return activity


def complete_warmup(db: Session, user_id: int, project_id: int) -> SessionActivity:
    """
    Mark warmup as completed for this session.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        Updated SessionActivity
    """
    activity = get_or_create_activity(db, user_id, project_id)

    activity.warmup_completed = True
    activity.warmup_completed_at = datetime.utcnow()

    db.commit()
    db.refresh(activity)
    return activity


def needs_warmup(db: Session, user_id: int, project_id: int) -> bool:
    """
    Check if user needs to do warmup.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        True if warmup should be shown
    """
    activity = get_or_create_activity(db, user_id, project_id)

    if not activity.warmup_completed:
        return True

    # Check if it's a new day
    if activity.warmup_completed_at:
        today = datetime.utcnow().date()
        warmup_date = activity.warmup_completed_at.date()
        if warmup_date < today:
            return True

    return False


# =============================================================================
# CONTEXT REFRESH GENERATION
# =============================================================================


def calculate_time_away(db: Session, user_id: int, project_id: int) -> Tuple[float, RefreshConfig]:
    """
    Calculate time away and determine refresh level.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        Tuple of (hours_away, RefreshConfig)
    """
    activity = get_or_create_activity(db, user_id, project_id)

    now = datetime.utcnow()
    delta = now - activity.last_active
    hours_away = delta.total_seconds() / 3600

    refresh_config = get_refresh_level(hours_away)

    return hours_away, refresh_config


def format_time_away(hours: float) -> str:
    """Format hours away as human-readable string."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif hours < 24:
        h = int(hours)
        return f"{h} hour{'s' if h != 1 else ''}"
    else:
        days = int(hours / 24)
        return f"{days} day{'s' if days != 1 else ''}"


def generate_refresh_content(
    db: Session,
    user_id: int,
    project_id: int,
    project: Project,
) -> Dict[str, Any]:
    """
    Generate context refresh content based on time away.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID
        project: Project object

    Returns:
        Dictionary with refresh content
    """
    hours_away, refresh_config = calculate_time_away(db, user_id, project_id)
    activity = get_or_create_activity(db, user_id, project_id)

    content = {
        "level": refresh_config.level.value,
        "title": refresh_config.title,
        "description": refresh_config.description,
        "time_away": format_time_away(hours_away),
        "hours_away": hours_away,
        "project_name": project.name,
        "show_skip": True,
    }

    # Build content based on level
    if refresh_config.level == RefreshLevel.MINIMAL:
        content.update(_generate_minimal_content(activity))
    elif refresh_config.level == RefreshLevel.BRIEF:
        content.update(_generate_brief_content(db, activity, project_id))
    elif refresh_config.level == RefreshLevel.MEDIUM:
        content.update(_generate_medium_content(db, activity, project_id, user_id))
    else:
        # FULL, EXTENDED, COMPLETE
        content.update(_generate_full_content(db, activity, project_id, user_id, project))

    return content


def _generate_minimal_content(activity: SessionActivity) -> Dict[str, Any]:
    """Generate minimal refresh content (< 1 hour away)."""
    content = {
        "sections": [],
    }

    if activity.current_feature:
        content["sections"].append({
            "title": "Working On",
            "content": activity.current_feature,
            "icon": "🔧",
        })

    if activity.last_rant_excerpt:
        content["sections"].append({
            "title": "Last Thing You Said",
            "content": f'"{activity.last_rant_excerpt}"',
            "icon": "💬",
        })

    return content


def _generate_brief_content(
    db: Session,
    activity: SessionActivity,
    project_id: int,
) -> Dict[str, Any]:
    """Generate brief refresh content (1-4 hours away)."""
    content = _generate_minimal_content(activity)

    # Add Agent OS status if available
    if activity.agent_os_completion is not None:
        content["sections"].append({
            "title": "Agent OS Progress",
            "content": f"{activity.agent_os_completion:.0f}% complete",
            "icon": "📊",
        })

    # Add recent decisions from session state
    if activity.session_state and "recent_decisions" in activity.session_state:
        decisions = activity.session_state["recent_decisions"]
        if decisions:
            content["sections"].append({
                "title": "Recent Decisions",
                "content": decisions[:3],  # Max 3 decisions
                "type": "list",
                "icon": "✅",
            })

    return content


def _generate_medium_content(
    db: Session,
    activity: SessionActivity,
    project_id: int,
    user_id: int,
) -> Dict[str, Any]:
    """Generate medium refresh content (4-24 hours away)."""
    content = _generate_brief_content(db, activity, project_id)

    # Add gaps if available
    if activity.agent_os_gaps:
        content["sections"].append({
            "title": "Outstanding Gaps",
            "content": activity.agent_os_gaps[:5],  # Max 5 gaps
            "type": "list",
            "icon": "⚠️",
        })

    # Session summary from state
    if activity.session_state and "session_summary" in activity.session_state:
        content["sections"].append({
            "title": "Session Summary",
            "content": activity.session_state["session_summary"],
            "icon": "📝",
        })

    return content


def _generate_full_content(
    db: Session,
    activity: SessionActivity,
    project_id: int,
    user_id: int,
    project: Project,
) -> Dict[str, Any]:
    """Generate full refresh content (1+ days away)."""
    content = _generate_medium_content(db, activity, project_id, user_id)

    # Add project overview
    if project.description:
        content["sections"].insert(0, {
            "title": "Project Overview",
            "content": project.description,
            "icon": "🎯",
        })

    # Add key ideas from Idea Bank
    ideas = (
        db.query(Idea)
        .filter(
            and_(
                Idea.project_id == project_id,
                Idea.user_id == user_id,
                Idea.status == IdeaStatus.ACTIVE,
            )
        )
        .order_by(desc(Idea.rating))
        .limit(3)
        .all()
    )

    if ideas:
        content["sections"].append({
            "title": "Key Ideas (from Idea Bank)",
            "content": [idea.content for idea in ideas],
            "type": "list",
            "icon": "💡",
        })

    # Add recommended next steps
    next_steps = _generate_next_steps(activity)
    if next_steps:
        content["sections"].append({
            "title": "Recommended Next Steps",
            "content": next_steps,
            "type": "list",
            "icon": "🚀",
        })

    return content


def _generate_next_steps(activity: SessionActivity) -> List[str]:
    """Generate recommended next steps based on session state."""
    steps = []

    if activity.agent_os_completion is not None:
        if activity.agent_os_completion < 50:
            steps.append("Continue filling out the Agent OS document")
        elif activity.agent_os_completion < 100:
            steps.append("Address remaining gaps in Agent OS")

    if activity.agent_os_gaps and len(activity.agent_os_gaps) > 0:
        steps.append(f"Fill gap: {activity.agent_os_gaps[0]}")

    if activity.current_feature:
        steps.append(f"Continue work on: {activity.current_feature}")

    if not steps:
        steps.append("Review your Idea Bank for inspiration")
        steps.append("Start a new rant to capture your thoughts")

    return steps[:3]  # Max 3 steps


# =============================================================================
# AI-POWERED CONTEXT SUMMARY
# =============================================================================


def generate_ai_summary(
    db: Session,
    project_id: int,
    user_id: int,
    project: Project,
    activity: SessionActivity,
) -> Optional[str]:
    """
    Generate an AI-powered summary of where things stand.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        project: Project object
        activity: SessionActivity object

    Returns:
        AI-generated summary or None
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        # Gather context
        context_parts = []

        if project.description:
            context_parts.append(f"Project: {project.name}\nDescription: {project.description}")

        if activity.current_feature:
            context_parts.append(f"Currently working on: {activity.current_feature}")

        if activity.last_rant_excerpt:
            context_parts.append(f"Last discussion: {activity.last_rant_excerpt}")

        if activity.agent_os_completion:
            context_parts.append(f"Agent OS completion: {activity.agent_os_completion}%")

        if activity.agent_os_gaps:
            context_parts.append(f"Outstanding gaps: {', '.join(activity.agent_os_gaps[:5])}")

        if not context_parts:
            return None

        context = "\n\n".join(context_parts)

        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that creates concise project status summaries.
Given context about a design project, create a brief (2-3 sentences) summary that reminds the user
where they left off and what they should focus on. Be encouraging and action-oriented.""",
                },
                {
                    "role": "user",
                    "content": f"Summarize this project status for a returning user:\n\n{context}",
                },
            ],
            temperature=0.5,
            max_tokens=200,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Error generating AI summary: {e}")
        return None


# =============================================================================
# PAUSE/RESUME STATE MANAGEMENT
# =============================================================================


def save_pause_state(
    db: Session,
    user_id: int,
    project_id: int,
    state: Dict[str, Any],
) -> SessionActivity:
    """
    Save current state when pausing work.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID
        state: State to save

    Returns:
        Updated SessionActivity
    """
    activity = get_or_create_activity(db, user_id, project_id)

    activity.session_state = state
    activity.last_active = datetime.utcnow()

    db.commit()
    db.refresh(activity)
    return activity


def get_resume_state(
    db: Session,
    user_id: int,
    project_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Get saved state for resuming work.

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        Saved state or None
    """
    activity = get_or_create_activity(db, user_id, project_id)
    return activity.session_state


def clear_resume_state(db: Session, user_id: int, project_id: int) -> SessionActivity:
    """
    Clear saved resume state (start fresh).

    Args:
        db: Database session
        user_id: User ID
        project_id: Project ID

    Returns:
        Updated SessionActivity
    """
    activity = get_or_create_activity(db, user_id, project_id)

    activity.session_state = None
    activity.current_feature = None
    activity.last_rant_excerpt = None
    activity.agent_os_completion = None
    activity.agent_os_gaps = None

    db.commit()
    db.refresh(activity)
    return activity
