"""
Data access layer (repositories) for database operations.

Repositories encapsulate database queries and provide a clean interface
for business logic to interact with the database.
"""

from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from app.core.db import Base

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


# TODO: Add specific repositories in later phases
# Example:
# class ProjectRepository(BaseRepository[Project]):
#     """Repository for Project model with custom queries."""
#
#     def get_by_name(self, name: str) -> Optional[Project]:
#         return self.db.query(self.model).filter(
#             self.model.name == name
#         ).first()
