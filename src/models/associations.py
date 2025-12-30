from sqlmodel import SQLModel, Field


class TeacherModule(SQLModel, table=True):
    teacher_id: str = Field(foreign_key="teachers.id", primary_key=True)
    module_id: str = Field(foreign_key="module.id", primary_key=True)

    __table_args__ = {'schema': 'public'}


class TeacherSpecialty(SQLModel, table=True):
    teacher_id: str = Field(foreign_key="teachers.id", primary_key=True)
    specialty_id: str = Field(foreign_key="specialty.id", primary_key=True)

    __table_args__ = {'schema': 'public'}
