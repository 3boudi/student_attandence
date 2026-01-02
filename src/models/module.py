from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from .associations import TeacherModule
import uuid

class ModuleBase(SQLModel):
    module_name: str = Field(index=True)
    module_code: str = Field(unique=True, index=True)

class Module(ModuleBase, table=True):
    __tablename__ = "module"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    specialty_id: Optional[int] = Field(foreign_key="public.specialty.id")
    specialty: Optional["Specialty"] = Relationship(back_populates="modules")
    
    teachers: List["Teacher"] = Relationship(
        back_populates="assigned_modules",
        link_model=TeacherModule
    )
    sessions: List["Session"] = Relationship(back_populates="module")
    
    __table_args__ = {'schema': 'public'}


if TYPE_CHECKING:
    from .specialty import Specialty
    from .teacher import Teacher
    from .session import Session