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
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session_id: str = Field(foreign_key="session.id")
    session: Optional["Session"] = Relationship(back_populates="attendance_records")

    student_id: str = Field(foreign_key="student.id")
    student: Optional["Student"] = Relationship(back_populates="attendance_records")

    justification: Optional["Justification"] = Relationship(back_populates="attendance_record")
    
    __table_args__ = {'schema': 'public'}