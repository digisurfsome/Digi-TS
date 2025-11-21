"""
SQLAlchemy models for Design Tree Studio.

This module will contain all database models/tables.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.db import Base


# Example model - will be expanded in later phases
class BaseModel:
    """Base model with common fields."""

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# TODO: Add your models here in later phases
# Example:
# class Project(Base, BaseModel):
#     __tablename__ = "projects"
#
#     name = Column(String(255), nullable=False)
#     description = Column(Text)
