from __future__ import annotations
from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional
from datetime import datetime

from src.models.notification import Notification
from .enums import *

# Base User model
class UserBase(SQLModel):
    full_name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    department: str

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    # Auth fields
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    
    # Role field to distinguish user types
    role: Optional[str] = Field(default=None, index=True)  # "student", "teacher", "admin"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    notifications: List["Notification"] = Relationship(back_populates="user")
    __table_args__ = {'schema': 'public'}
    