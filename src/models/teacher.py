from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from .associations import TeacherModule, TeacherSpecialty
from typing import TYPE_CHECKING
import uuid

class TeacherBase(SQLModel):
    # Teacher-specific base fields
    pass

class Teacher(TeacherBase, table=True):
    __tablename__ = "teachers"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Foreign key to User
    user_id: str = Field(foreign_key="users.id", unique=True)
    user: Optional["User"] = Relationship(back_populates="teacher_profile")
    
    # Relationships
    assigned_modules: List["Module"] = Relationship(
        back_populates="teachers",
        link_model=TeacherModule
    )
    assigned_specialties: List["Specialty"] = Relationship(
        back_populates="teachers",
        link_model=TeacherSpecialty
    )
    sessions: List["Session"] = Relationship(back_populates="teacher")
    validated_justifications: List["Justification"] = Relationship(back_populates="validator")
    
    __table_args__ = {'schema': 'public'}


if TYPE_CHECKING:
    from .user import User
    from .module import Module
    from .specialty import Specialty
    from .session import Session
    from .justification import Justification