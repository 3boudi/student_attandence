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
    file_url: Optional[str] = None

class Justification(JustificationBase, table=True):
    __tablename__ = "justifications"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)
    status: JustificationStatus = Field(default=JustificationStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    validation_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Relationships
    attendance_record_id: int = Field(foreign_key="public.attendance_records.id")  # ✅ Changed
    attendance_record: Optional["AttendanceRecord"] = Relationship(back_populates="justification")

    student_id: int = Field(foreign_key="public.students.id")  # ✅ Changed to "students"
    student: Optional["Student"] = Relationship(back_populates="justifications")

    validator_id: Optional[int] = Field(default=None, foreign_key="public.teachers.id")  # ✅ Changed to "teachers"
    validator: Optional["Teacher"] = Relationship(back_populates="validated_justifications")
    
    __table_args__ = {'schema': 'public'}