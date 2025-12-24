"""
Project management service.

Handles project-related business logic and operations.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.models import Project, ProjectContext
from app.core.repositories import ProjectRepository, ProjectContextRepository


def list_user_projects(
    db: Session,
    user_id: int,
    include_archived: bool = False
) -> List[Project]:
    """
    List all projects for a user.

    Args:
        db: Database session
        user_id: User ID
        include_archived: Whether to include archived projects

    Returns:
        List of projects
    """
    repo = ProjectRepository(db)
    return repo.get_by_owner(user_id, include_archived=include_archived)


def create_project(
    db: Session,
    name: str,
    owner_id: int,
    description: Optional[str] = None,
    github_repo: Optional[str] = None
) -> Project:
    """
    Create a new project.

    Args:
        db: Database session
        name: Project name
        owner_id: Owner user ID
        description: Optional project description
        github_repo: Optional GitHub repo in format "owner/repo-name"

    Returns:
        Created Project
    """
    repo = ProjectRepository(db)
    project = repo.create_project(
        name=name,
        owner_id=owner_id,
        description=description,
        github_repo=github_repo
    )

    # Create default context for the project
    context_repo = ProjectContextRepository(db)
    context_repo.get_or_create_default(project.id)

    return project


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """
    Get project by ID.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        Project or None
    """
    repo = ProjectRepository(db)
    return repo.get_by_id(project_id)


def update_project(
    db: Session,
    project_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_archived: Optional[bool] = None,
    github_repo: Optional[str] = None
) -> Optional[Project]:
    """
    Update project fields.

    Args:
        db: Database session
        project_id: Project ID
        name: New name (optional)
        description: New description (optional)
        is_archived: Archive status (optional)
        github_repo: GitHub repo in format "owner/repo-name" (optional)

    Returns:
        Updated Project or None
    """
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        return None

    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if is_archived is not None:
        project.is_archived = is_archived
    if github_repo is not None:
        project.github_repo = github_repo

    return repo.update(project)


def delete_project(db: Session, project_id: int) -> bool:
    """
    Delete a project.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        True if deleted, False if not found
    """
    repo = ProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        return False

    repo.delete(project)
    return True


# Project Context Management

def get_project_context(db: Session, project_id: int) -> Optional[ProjectContext]:
    """
    Get the default project context.

    Args:
        db: Database session
        project_id: Project ID

    Returns:
        ProjectContext or None
    """
    repo = ProjectContextRepository(db)
    return repo.get_or_create_default(project_id)


def update_project_context(
    db: Session,
    project_id: int,
    content: str,
    name: str = "Default Context"
) -> ProjectContext:
    """
    Update project context content.

    Args:
        db: Database session
        project_id: Project ID
        content: New context content
        name: Context name

    Returns:
        Updated ProjectContext
    """
    repo = ProjectContextRepository(db)
    context = repo.get_or_create_default(project_id)

    context.content = content
    context.name = name

    return repo.update(context)
