from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .module import Module
    from .teacher import Teacher
    from .attendance import AttendanceRecord

class SessionBase(SQLModel):
    session_code: str = Field(index=True)
    datetime: datetime
    duration_minutes: int = Field(default=60)

class Session(SessionBase, table=True):
    __tablename__ = "sessions"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    module_id: int = Field(foreign_key="public.module.id")
    module: Optional["Module"] = Relationship(back_populates="sessions")
    
    teacher_id: int = Field(foreign_key="public.teachers.id")  # ✅ Changed to "teachers"
    teacher: Optional["Teacher"] = Relationship(back_populates="sessions")
    
    attendance_records: List["AttendanceRecord"] = Relationship(back_populates="session")
    
    __table_args__ = {'schema': 'public'}