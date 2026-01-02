from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from .associations import TeacherSpecialty
from .schedule import Schedule

class SpecialtyBase(SQLModel):
    name: str = Field(index=True)
    year_level: str

class Specialty(SpecialtyBase, table=True):
    __tablename__ = "specialty"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    modules: List["Module"] = Relationship(back_populates="specialty")
    students: List["Student"] = Relationship(back_populates="specialty")
    teachers: List["Teacher"] = Relationship(
        back_populates="assigned_specialties",
        link_model=TeacherSpecialty
    )
    schedule: Optional["Schedule"] = Relationship(back_populates="specialty")

    __table_args__ = {'schema': 'public'}


if TYPE_CHECKING:
    from .module import Module
    from .student import Student
    from .teacher import Teacher