from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .student import Student
    from .module import Module

class Enrollment(SQLModel, table=True):
    __tablename__ = "enrollments"
    __table_args__ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="public.students.id")
    module_id: int = Field(foreign_key="public.module.id")

    number_of_absences: int = Field(default=0)
    is_excluded: bool = Field(default=False)

    student: "Student" = Relationship(back_populates="enrollments")
    module: "Module" = Relationship(back_populates="enrollments")
