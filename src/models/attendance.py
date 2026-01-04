from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from .enums import AttendanceStatus

if TYPE_CHECKING:
    from .session import Session
    from .student import Student
    from .justification import Justification

class AttendanceRecord(SQLModel, table=True):
    __tablename__ = "attendance_records"
    __table_args__ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    status: AttendanceStatus = Field(default=AttendanceStatus.ABSENT)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session_id: int = Field(foreign_key="public.sessions.id")
    student_id: int = Field(foreign_key="public.students.id")
    justification_id: Optional[int] = Field(
        foreign_key="public.justifications.id",
        default=None,
        unique=True
    )
    session: "Session" = Relationship(back_populates="attendance_records")
    student: "Student" = Relationship(back_populates="attendance_records")
    justification: Optional["Justification"] = Relationship(back_populates="attendance_record")
