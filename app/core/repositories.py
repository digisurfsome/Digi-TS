"""
Data access layer (repositories) for database operations.

Repositories encapsulate database queries and provide a clean interface
for business logic to interact with the database.
"""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.core.db import Base
from app.core.models import (
    UserProfile,
    Project,
    ProjectContext,
    Node,
    NodeVersion,
    NodeStatus,
    NodeType,
    ChatSession,
    ChatMessage,
    DraftMeta,
)

# Type variable for generic repository
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    Can be extended for specific models with custom queries.
    """

    def __init__(self, model: Type[ModelType], db: Session):
        """
        Initialize repository with model class and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj: ModelType) -> ModelType:
        """Create a new record."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        """Update an existing record."""
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        """Delete a record."""
        self.db.delete(obj)
        self.db.commit()


# UserProfile Repository
class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for UserProfile model with custom queries."""

    def __init__(self, db: Session):
        super().__init__(UserProfile, db)

    def get_by_username(self, username: str) -> Optional[UserProfile]:
        """Get user by username."""
        return self.db.query(self.model).filter(
            self.model.username == username
        ).first()

    def get_by_email(self, email: str) -> Optional[UserProfile]:
        """Get user by email."""
        return self.db.query(self.model).filter(
            self.model.email == email
        ).first()

    def create_user(
        self,
        username: str,
        email: str,
        full_name: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """
        Create a new user profile.

        Args:
            username: Unique username
            email: User email
            full_name: Optional full name
            **kwargs: Additional user fields

        Returns:
            Created UserProfile
        """
        user = UserProfile(
            username=username,
            email=email,
            full_name=full_name,
            **kwargs
        )
        return self.create(user)

    def get_active_users(self) -> List[UserProfile]:
        """Get all active users."""
        return self.db.query(self.model).filter(
            self.model.is_active == True
        ).all()


# Project Repository
class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model with custom queries."""

    def __init__(self, db: Session):
        super().__init__(Project, db)

    def get_by_owner(
        self,
        owner_id: int,
        include_archived: bool = False
    ) -> List[Project]:
        """Get all projects for a user."""
        query = self.db.query(self.model).filter(
            self.model.owner_id == owner_id
        )

        if not include_archived:
            query = query.filter(self.model.is_archived == False)

        return query.order_by(desc(self.model.created_at)).all()

    def create_project(
        self,
        name: str,
        owner_id: int,
        description: Optional[str] = None,
        **kwargs
    ) -> Project:
        """
        Create a new project.

        Args:
            name: Project name
            owner_id: ID of the project owner
            description: Optional project description
            **kwargs: Additional project fields

        Returns:
            Created Project
        """
        project = Project(
            name=name,
            owner_id=owner_id,
            description=description,
            **kwargs
        )
        return self.create(project)

    def get_by_name_and_owner(
        self,
        name: str,
        owner_id: int
    ) -> Optional[Project]:
        """Get project by name and owner."""
        return self.db.query(self.model).filter(
            and_(
                self.model.name == name,
                self.model.owner_id == owner_id
            )
        ).first()


# ProjectContext Repository
class ProjectContextRepository(BaseRepository[ProjectContext]):
    """Repository for ProjectContext model with custom queries."""

    def __init__(self, db: Session):
        super().__init__(ProjectContext, db)

    def get_by_project(
        self,
        project_id: int,
        active_only: bool = True
    ) -> List[ProjectContext]:
        """Get all contexts for a project."""
        query = self.db.query(self.model).filter(
            self.model.project_id == project_id
        )

        if active_only:
            query = query.filter(self.model.is_active == True)

        return query.order_by(desc(self.model.priority)).all()

    def create_context(
        self,
        project_id: int,
        name: str,
        content: str,
        context_type: str = "general",
        **kwargs
    ) -> ProjectContext:
        """
        Create a new project context.

        Args:
            project_id: ID of the project
            name: Context name
            content: Context content
            context_type: Type of context
            **kwargs: Additional context fields

        Returns:
            Created ProjectContext
        """
        context = ProjectContext(
            project_id=project_id,
            name=name,
            content=content,
            context_type=context_type,
            **kwargs
        )
        return self.create(context)

    def get_or_create_default(
        self,
        project_id: int
    ) -> ProjectContext:
        """
        Get or create default project context.

        Args:
            project_id: ID of the project

        Returns:
            Default ProjectContext
        """
        context = self.db.query(self.model).filter(
            and_(
                self.model.project_id == project_id,
                self.model.context_type == "general",
                self.model.name == "Default Context"
            )
        ).first()

        if not context:
            context = self.create_context(
                project_id=project_id,
                name="Default Context",
                content="Default project context",
                context_type="general",
                is_active=True,
                priority=0
            )

        return context


# Node Repository
class NodeRepository(BaseRepository[Node]):
    """Repository for Node model with custom queries."""

    def __init__(self, db: Session):
        super().__init__(Node, db)

    def get_by_project(
        self,
        project_id: int,
        status: Optional[NodeStatus] = None
    ) -> List[Node]:
        """Get all nodes for a project."""
        query = self.db.query(self.model).filter(
            self.model.project_id == project_id
        )

        if status:
            query = query.filter(self.model.status == status)

        return query.order_by(self.model.order_index).all()

    def get_root_nodes(self, project_id: int) -> List[Node]:
        """Get root nodes (nodes without parent) for a project."""
        return self.db.query(self.model).filter(
            and_(
                self.model.project_id == project_id,
                self.model.parent_id.is_(None)
            )
        ).order_by(self.model.order_index).all()

    def get_children(self, node_id: int) -> List[Node]:
        """Get child nodes of a given node."""
        return self.db.query(self.model).filter(
            self.model.parent_id == node_id
        ).order_by(self.model.order_index).all()

    def create_node(
        self,
        project_id: int,
        name: str,
        node_type: NodeType = NodeType.COMPONENT,
        parent_id: Optional[int] = None,
        **kwargs
    ) -> Node:
        """
        Create a new node.

        Args:
            project_id: ID of the project
            name: Node name
            node_type: Type of the node
            parent_id: Optional parent node ID
            **kwargs: Additional node fields

        Returns:
            Created Node
        """
        node = Node(
            project_id=project_id,
            name=name,
            node_type=node_type,
            parent_id=parent_id,
            status=NodeStatus.ACTIVE,
            **kwargs
        )
        return self.create(node)


# NodeVersion Repository
class NodeVersionRepository(BaseRepository[NodeVersion]):
    """Repository for NodeVersion model with custom queries."""

    def __init__(self, db: Session):
        super().__init__(NodeVersion, db)

    def get_by_node(
        self,
        node_id: int,
        published_only: bool = False
    ) -> List[NodeVersion]:
        """Get all versions for a node."""
        query = self.db.query(self.model).filter(
            self.model.node_id == node_id
        )

        if published_only:
            query = query.filter(self.model.is_published == True)

        return query.order_by(desc(self.model.version_number)).all()

    def get_latest_version(self, node_id: int) -> Optional[NodeVersion]:
        """Get the latest version of a node."""
        return self.db.query(self.model).filter(
            self.model.node_id == node_id
        ).order_by(desc(self.model.version_number)).first()

    def create_version(
        self,
        node_id: int,
        content: Optional[str] = None,
        content_type: str = "text",
        **kwargs
    ) -> NodeVersion:
        """
        Create a new node version.

        Args:
            node_id: ID of the node
            content: Version content
            content_type: Type of content
            **kwargs: Additional version fields

        Returns:
            Created NodeVersion
        """
        # Get the latest version number
        latest = self.get_latest_version(node_id)
        version_number = (latest.version_number + 1) if latest else 1

        version = NodeVersion(
            node_id=node_id,
            version_number=version_number,
            content=content,
            content_type=content_type,
            **kwargs
        )
        return self.create(version)
