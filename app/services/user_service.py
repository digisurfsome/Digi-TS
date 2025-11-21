"""
User management service.

Handles user-related business logic and operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.models import UserProfile
from app.core.repositories import UserProfileRepository


def get_or_create_default_user(db: Session) -> UserProfile:
    """
    Get or create a default user for the application.

    Args:
        db: Database session

    Returns:
        Default UserProfile
    """
    repo = UserProfileRepository(db)

    # Try to get existing default user
    user = repo.get_by_username("default_user")

    if not user:
        # Create default user
        user = repo.create_user(
            username="default_user",
            email="user@designtreestudio.local",
            full_name="Default User",
            is_active=True
        )

    return user


def list_all_users(db: Session) -> List[UserProfile]:
    """
    List all active users.

    Args:
        db: Database session

    Returns:
        List of active users
    """
    repo = UserProfileRepository(db)
    return repo.get_active_users()


def create_user(
    db: Session,
    username: str,
    email: str,
    full_name: Optional[str] = None
) -> UserProfile:
    """
    Create a new user.

    Args:
        db: Database session
        username: Username
        email: Email address
        full_name: Optional full name

    Returns:
        Created UserProfile
    """
    repo = UserProfileRepository(db)
    return repo.create_user(username=username, email=email, full_name=full_name)


def get_user_by_id(db: Session, user_id: int) -> Optional[UserProfile]:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        UserProfile or None
    """
    repo = UserProfileRepository(db)
    return repo.get_by_id(user_id)
