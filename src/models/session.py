from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .teacher_modules import TeacherModules
    from .attendance import AttendanceRecord

class Session(SQLModel, table=True):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    session_code: str
    session_qrcode: str
    date_time: datetime = Field(default_factory=datetime.utcnow)
    duration_minutes: int = Field(default=90)
    room: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)

    teacher_module_id: int = Field(foreign_key="public.teacher_modules.id")

    teacher_module: "TeacherModules" = Relationship(back_populates="sessions")
    attendance_records: List["AttendanceRecord"] = Relationship(back_populates="session")
