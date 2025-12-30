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
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    module_id: str = Field(foreign_key="module.id")
    module: Optional["Module"] = Relationship(back_populates="sessions")

    teacher_id: str = Field(foreign_key="teacher.id")
    teacher: Optional["Teacher"] = Relationship(back_populates="sessions")

    attendance_records: List["AttendanceRecord"] = Relationship(back_populates="session")
    
    __table_args__ = {'schema': 'public'}