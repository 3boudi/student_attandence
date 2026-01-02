from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional

class AdminBase(SQLModel):
    pass

class Admin(AdminBase, table=True):
    __tablename__ = "admins"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="public.users.id", unique=True)
    
    __table_args__ = {'schema': 'public'}