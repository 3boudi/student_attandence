from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from .enums import AttendanceStatus
import uuid

if TYPE_CHECKING:
    from .session import Session
    from .student import Student
    from .justification import Justification

class AttendanceRecordBase(SQLModel):
    status: AttendanceStatus = Field(default=AttendanceStatus.ABSENT)

class AttendanceRecord(AttendanceRecordBase, table=True):
    __tablename__ = "attendance_records"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session_id: int = Field(foreign_key="public.sessions.id")  # ✅ Changed to "sessions"
    session: Optional["Session"] = Relationship(back_populates="attendance_records")

    student_id: int = Field(foreign_key="public.students.id")  # ✅ Changed to "students"
    student: Optional["Student"] = Relationship(back_populates="attendance_records")

    justification: Optional["Justification"] = Relationship(back_populates="attendance_record")
    
    __table_args__ = {'schema': 'public'}