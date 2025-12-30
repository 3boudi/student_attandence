from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .specialty import Specialty
    from .attendance import AttendanceRecord
    from .justification import Justification
import uuid

class StudentBase(SQLModel):
    # Student-specific fields can go here
    pass

class Student(StudentBase, table=True):
    __tablename__ = "students"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Foreign key to User
    user_id: str = Field(foreign_key="users.id", unique=True)
    user: Optional["User"] = Relationship(back_populates="student_profile")
    
    # Relationships
    specialty_id: Optional[str] = Field(foreign_key="specialty.id")
    specialty: Optional["Specialty"] = Relationship(back_populates="students")
    
    attendance_records: List["AttendanceRecord"] = Relationship(back_populates="student")
    justifications: List["Justification"] = Relationship(back_populates="student")
    
    __table_args__ = {'schema': 'public'}


if TYPE_CHECKING:
    from .user import User