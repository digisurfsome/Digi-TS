"""
Idea Bank service for Phase 5: Learning & Memory.

Manages the Idea Bank - a daily warmup system that actively surfaces
the user's best ideas every login until they're internalized.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
import openai
import os

from app.core.models import (
    Idea,
    IdeaCategory,
    IdeaSource,
    IdeaStatus,
    Project,
    RawRant,
)


# =============================================================================
# IDEA CRUD OPERATIONS
# =============================================================================


def create_idea(
    db: Session,
    project_id: int,
    user_id: int,
    content: str,
    category: IdeaCategory = IdeaCategory.INSIGHT,
    source: IdeaSource = IdeaSource.MANUAL,
    rating: int = 3,
    source_ref: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Idea:
    """
    Create a new idea in the Idea Bank.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        content: The idea content
        category: Category of the idea
        source: Source of the idea
        rating: Star rating (1-5)
        source_ref: Optional reference to source (e.g., rant ID)
        tags: Optional list of tags

    Returns:
        Created Idea
    """
    # Clamp rating to 1-5
    rating = max(1, min(5, rating))

    idea = Idea(
        project_id=project_id,
        user_id=user_id,
        content=content,
        category=category,
        source=source,
        status=IdeaStatus.ACTIVE,
        rating=rating,
        times_shown=0,
        source_ref=source_ref,
        tags=tags or [],
    )

    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def get_idea_by_id(db: Session, idea_id: int) -> Optional[Idea]:
    """Get an idea by ID."""
    return db.query(Idea).filter(Idea.id == idea_id).first()


def list_ideas(
    db: Session,
    project_id: int,
    user_id: Optional[int] = None,
    status: Optional[IdeaStatus] = None,
    category: Optional[IdeaCategory] = None,
    min_rating: Optional[int] = None,
) -> List[Idea]:
    """
    List ideas with optional filters.

    Args:
        db: Database session
        project_id: Project ID
        user_id: Optional user ID filter
        status: Optional status filter
        category: Optional category filter
        min_rating: Minimum rating filter

    Returns:
        List of matching ideas
    """
    try:
        query = db.query(Idea).filter(Idea.project_id == project_id)

        if user_id is not None:
            query = query.filter(Idea.user_id == user_id)
        if status is not None:
            query = query.filter(Idea.status == status)
        if category is not None:
            query = query.filter(Idea.category == category)
        if min_rating is not None:
            query = query.filter(Idea.rating >= min_rating)

        # Order by rating (desc), then times_shown (asc for less-shown ideas)
        return query.order_by(desc(Idea.rating), Idea.times_shown).all()
    except Exception as e:
        # If table doesn't exist yet, return empty list
        if "ideas" in str(e).lower() or "undefined" in str(e).lower():
            return []
        raise


def update_idea(
    db: Session,
    idea_id: int,
    content: Optional[str] = None,
    category: Optional[IdeaCategory] = None,
    rating: Optional[int] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Idea]:
    """
    Update an idea.

    Args:
        db: Database session
        idea_id: Idea ID
        content: New content (optional)
        category: New category (optional)
        rating: New rating (optional)
        tags: New tags (optional)

    Returns:
        Updated idea or None
    """
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return None

    if content is not None:
        idea.content = content
    if category is not None:
        idea.category = category
    if rating is not None:
        idea.rating = max(1, min(5, rating))
    if tags is not None:
        idea.tags = tags

    db.commit()
    db.refresh(idea)
    return idea


def delete_idea(db: Session, idea_id: int) -> bool:
    """Delete an idea permanently."""
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return False

    db.delete(idea)
    db.commit()
    return True


def retire_idea(db: Session, idea_id: int) -> Optional[Idea]:
    """
    Retire an idea (mark as internalized).

    Args:
        db: Database session
        idea_id: Idea ID

    Returns:
        Updated idea or None
    """
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return None

    idea.status = IdeaStatus.RETIRED
    db.commit()
    db.refresh(idea)
    return idea


def archive_idea(db: Session, idea_id: int) -> Optional[Idea]:
    """
    Archive an idea (remove but preserve).

    Args:
        db: Database session
        idea_id: Idea ID

    Returns:
        Updated idea or None
    """
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return None

    idea.status = IdeaStatus.ARCHIVED
    db.commit()
    db.refresh(idea)
    return idea


def reactivate_idea(db: Session, idea_id: int) -> Optional[Idea]:
    """
    Reactivate a retired or archived idea.

    Args:
        db: Database session
        idea_id: Idea ID

    Returns:
        Updated idea or None
    """
    idea = get_idea_by_id(db, idea_id)
    if not idea:
        return None

    idea.status = IdeaStatus.ACTIVE
    db.commit()
    db.refresh(idea)
    return idea


# =============================================================================
# WARMUP OPERATIONS
# =============================================================================


def get_warmup_ideas(
    db: Session,
    project_id: int,
    user_id: int,
    max_ideas: int = 5,
) -> List[Idea]:
    """
    Get ideas for daily warmup display.

    Prioritizes:
    1. Highest rated ideas
    2. Ideas shown fewer times (less familiar)
    3. Recently added ideas

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        max_ideas: Maximum number of ideas to return

    Returns:
        List of ideas for warmup
    """
    try:
        # Get active ideas only
        ideas = (
            db.query(Idea)
            .filter(
                and_(
                    Idea.project_id == project_id,
                    Idea.user_id == user_id,
                    Idea.status == IdeaStatus.ACTIVE,
                )
            )
            # Score: rating * 2 - log(times_shown + 1)
            # High rating + low times_shown = higher priority
            .order_by(
                desc(Idea.rating),
                Idea.times_shown,
                desc(Idea.created_at),
            )
            .limit(max_ideas)
            .all()
        )

        return ideas
    except Exception as e:
        # If table doesn't exist yet, return empty list
        if "ideas" in str(e).lower() or "undefined" in str(e).lower():
            return []
        raise


def mark_ideas_shown(db: Session, idea_ids: List[int]) -> int:
    """
    Mark ideas as shown (increment times_shown).

    Args:
        db: Database session
        idea_ids: List of idea IDs

    Returns:
        Number of ideas updated
    """
    now = datetime.utcnow()
    count = 0

    for idea_id in idea_ids:
        idea = get_idea_by_id(db, idea_id)
        if idea:
            idea.times_shown += 1
            idea.last_shown = now
            count += 1

    db.commit()
    return count


def get_idea_stats(db: Session, project_id: int, user_id: int) -> Dict[str, Any]:
    """
    Get statistics about the idea bank.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID

    Returns:
        Dictionary with stats
    """
    try:
        base_query = db.query(Idea).filter(
            and_(
                Idea.project_id == project_id,
                Idea.user_id == user_id,
            )
        )

        total = base_query.count()
        active = base_query.filter(Idea.status == IdeaStatus.ACTIVE).count()
        retired = base_query.filter(Idea.status == IdeaStatus.RETIRED).count()
        archived = base_query.filter(Idea.status == IdeaStatus.ARCHIVED).count()

        # Category breakdown (active only)
        category_counts = {}
        for cat in IdeaCategory:
            count = base_query.filter(
                and_(
                    Idea.status == IdeaStatus.ACTIVE,
                    Idea.category == cat,
                )
            ).count()
            category_counts[cat.value] = count

        # Average rating of active ideas
        avg_rating = (
            db.query(func.avg(Idea.rating))
            .filter(
                and_(
                    Idea.project_id == project_id,
                    Idea.user_id == user_id,
                    Idea.status == IdeaStatus.ACTIVE,
                )
            )
            .scalar()
        ) or 0

        # Total times shown
        total_shown = (
            db.query(func.sum(Idea.times_shown))
            .filter(
                and_(
                    Idea.project_id == project_id,
                    Idea.user_id == user_id,
                )
            )
            .scalar()
        ) or 0

        return {
            "total": total,
            "active": active,
            "retired": retired,
            "archived": archived,
            "by_category": category_counts,
            "avg_rating": round(float(avg_rating), 1),
            "total_times_shown": int(total_shown),
        }
    except Exception as e:
        # If table doesn't exist yet, return empty stats
        if "ideas" in str(e).lower() or "undefined" in str(e).lower():
            return {
                "total": 0,
                "active": 0,
                "retired": 0,
                "archived": 0,
                "by_category": {},
                "avg_rating": 0,
                "total_times_shown": 0,
            }
        raise


# =============================================================================
# QUICK ADD FROM RANT
# =============================================================================


def quick_add_from_text(
    db: Session,
    project_id: int,
    user_id: int,
    text: str,
    category: IdeaCategory = IdeaCategory.INSIGHT,
    rating: int = 3,
    source_ref: Optional[str] = None,
) -> Idea:
    """
    Quick add an idea from selected text.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        text: Selected text to save as idea
        category: Category for the idea
        rating: Initial rating
        source_ref: Reference to source (e.g., rant ID)

    Returns:
        Created idea
    """
    # Clean up the text
    content = text.strip()

    # Truncate if too long (keep first 500 chars)
    if len(content) > 500:
        content = content[:497] + "..."

    return create_idea(
        db=db,
        project_id=project_id,
        user_id=user_id,
        content=content,
        category=category,
        source=IdeaSource.RANT,
        rating=rating,
        source_ref=source_ref,
    )


# =============================================================================
# AI-POWERED IDEA DETECTION
# =============================================================================


def detect_valuable_ideas(
    db: Session,
    project_id: int,
    user_id: int,
    rant_content: str,
    rant_id: Optional[int] = None,
) -> List[Idea]:
    """
    Use AI to detect valuable ideas from rant content.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        rant_content: The rant text to analyze
        rant_id: Optional reference to the rant

    Returns:
        List of created ideas
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    try:
        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """You are an idea extraction assistant. Analyze the given text and extract valuable ideas that would be worth remembering and reviewing daily.

For each idea found, respond with a JSON array of objects with these fields:
- content: The idea in a concise, memorable form (1-2 sentences max)
- category: One of "vision", "feature", "insight", "pattern"
- rating: 1-5 based on importance (5 = core vision, 1 = minor detail)

Only extract truly valuable ideas - things worth remembering. Not every statement is an idea.
Respond ONLY with the JSON array, no other text.""",
                },
                {
                    "role": "user",
                    "content": f"Extract valuable ideas from this text:\n\n{rant_content}",
                },
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        # Parse the response
        import json
        content = response.choices[0].message.content.strip()

        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        ideas_data = json.loads(content)

        created_ideas = []
        for idea_data in ideas_data:
            if not isinstance(idea_data, dict):
                continue

            idea_content = idea_data.get("content", "").strip()
            if not idea_content:
                continue

            # Map category string to enum
            cat_str = idea_data.get("category", "insight").lower()
            category_map = {
                "vision": IdeaCategory.VISION,
                "feature": IdeaCategory.FEATURE,
                "insight": IdeaCategory.INSIGHT,
                "pattern": IdeaCategory.PATTERN,
            }
            category = category_map.get(cat_str, IdeaCategory.INSIGHT)

            # Get rating
            rating = idea_data.get("rating", 3)
            if not isinstance(rating, int):
                rating = 3

            idea = create_idea(
                db=db,
                project_id=project_id,
                user_id=user_id,
                content=idea_content,
                category=category,
                source=IdeaSource.AI_DETECTED,
                rating=rating,
                source_ref=f"rant:{rant_id}" if rant_id else None,
            )
            created_ideas.append(idea)

        return created_ideas

    except Exception as e:
        print(f"Error detecting ideas: {e}")
        return []


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_category_icon(category: IdeaCategory) -> str:
    """Get emoji icon for a category."""
    icons = {
        IdeaCategory.VISION: "🎯",
        IdeaCategory.FEATURE: "⚙️",
        IdeaCategory.INSIGHT: "💡",
        IdeaCategory.PATTERN: "🔄",
    }
    return icons.get(category, "💡")


def get_status_icon(status: IdeaStatus) -> str:
    """Get emoji icon for a status."""
    icons = {
        IdeaStatus.ACTIVE: "✅",
        IdeaStatus.RETIRED: "🎓",
        IdeaStatus.ARCHIVED: "📦",
    }
    return icons.get(status, "❓")


def render_star_rating(rating: int) -> str:
    """Render star rating as string."""
    filled = "⭐" * rating
    empty = "☆" * (5 - rating)
    return filled + empty


def format_idea_for_display(idea: Idea) -> Dict[str, Any]:
    """Format an idea for UI display."""
    return {
        "id": idea.id,
        "content": idea.content,
        "category": idea.category.value,
        "category_icon": get_category_icon(idea.category),
        "status": idea.status.value,
        "status_icon": get_status_icon(idea.status),
        "rating": idea.rating,
        "rating_display": render_star_rating(idea.rating),
        "times_shown": idea.times_shown,
        "last_shown": idea.last_shown.isoformat() if idea.last_shown else None,
        "created_at": idea.created_at.isoformat(),
        "source": idea.source.value,
        "tags": idea.tags or [],
    }
