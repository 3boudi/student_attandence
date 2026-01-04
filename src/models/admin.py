from __future__ import annotations
from sqlmodel import Relationship, SQLModel, Field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .report import Report

class AdminBase(SQLModel):
    pass

class Admin(AdminBase, table=True):
    __tablename__ = "admins"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="public.users.id", unique=True)
    
    reports: list[Report] = Relationship(back_populates="admin")    
    __table_args__ = {'schema': 'public'}