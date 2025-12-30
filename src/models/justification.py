from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from .enums import JustificationStatus
import uuid

if TYPE_CHECKING:
    from .attendance import AttendanceRecord
    from .student import Student
    from .teacher import Teacher

class JustificationBase(SQLModel):
    comment: str
    file_url: Optional[str] = None  # Store file path or URL

class Justification(JustificationBase, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    status: JustificationStatus = Field(default=JustificationStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    validation_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Relationships
    attendance_record_id: str = Field(foreign_key="attendancerecord.id")
    attendance_record: Optional["AttendanceRecord"] = Relationship(back_populates="justification")

    student_id: str = Field(foreign_key="student.id")
    student: Optional["Student"] = Relationship(back_populates="justifications")

    validator_id: Optional[str] = Field(default=None, foreign_key="teacher.id")
    validator: Optional["Teacher"] = Relationship(back_populates="validated_justifications")
    
    __table_args__ = {'schema': 'public'}