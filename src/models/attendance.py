from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from .enums import AttendanceStatus

if TYPE_CHECKING:
    from .session import Session
    from .enrollement import Enrollment
    from .justification import Justification
    from .module import Module


class AttendanceRecord(SQLModel, table=True):
    __tablename__ = "attendance_records"
    __table_args__ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    status: AttendanceStatus = Field(default=AttendanceStatus.ABSENT)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session_id: int = Field(foreign_key="public.sessions.id")
    module_id: int = Field(foreign_key="public.module.id")
    enrollement_id: int = Field(foreign_key="public.enrollments.id")
    justification_id: Optional[int] = Field(
        foreign_key="public.justifications.id",
        default=None,
        unique=True
    )
    module: "Module" = Relationship(back_populates="attendance_records")
    enrollement: "Enrollment" = Relationship(back_populates="attendance_records")
    session: "Session" = Relationship(back_populates="attendance_records")
    justification: Optional["Justification"] = Relationship(back_populates="attendance_record_rel")
