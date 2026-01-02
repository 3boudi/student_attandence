from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional

class StudentBase(SQLModel):
    pass

class Student(StudentBase, table=True):
    __tablename__ = "students"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="public.users.id", unique=True)
    
    __table_args__ = {'schema': 'public'}