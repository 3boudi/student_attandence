from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional

class TeacherBase(SQLModel):
    pass

class Teacher(TeacherBase, table=True):
    __tablename__ = "teacher"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="public.users.id", unique=True)
    
    __table_args__ = {'schema': 'public'}