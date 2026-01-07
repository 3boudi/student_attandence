from __future__ import annotations

from sqlmodel import Relationship, SQLModel, Field
from typing import Optional
from datetime import datetime

from src.models.user import User


from .enums import NotificationType


class NotificationBase(SQLModel):
    title: str
    message: str
    type: NotificationType

class Notification(NotificationBase, table=True):
    __tablename__ = "notifications"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    message: str
    type: NotificationType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)
    
    
    
    user_id: int = Field(foreign_key="public.users.id")
    user: "User" = Relationship(back_populates="notifications")
    
    __table_args__ = {'schema': 'public'}
