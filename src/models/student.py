from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .specialty import Specialty
    from .enrollement import Enrollment
    from .attendance import AttendanceRecord

class Student(SQLModel, table=True):
    __tablename__ = "students"
    __table_args__ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="public.users.id", unique=True)
    specialty_id: int = Field(foreign_key="public.specialty.id")

    specialty: "Specialty" = Relationship(back_populates="students")
    enrollments: List["Enrollment"] = Relationship(back_populates="student")
    attendance_records: List["AttendanceRecord"] = Relationship(back_populates="student")
