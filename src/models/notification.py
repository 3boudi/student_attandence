from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from .enums import NotificationType
import uuid

class NotificationBase(SQLModel):
    title: str
    message: str
    type: NotificationType

class Notification(NotificationBase, table=True):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)
    
    # Relationships
    user_id: str = Field(foreign_key="users.id")
    user: Optional["User"] = Relationship(back_populates="notifications")
    __table_args__ = {'schema': 'public'}


if TYPE_CHECKING:
    from .user import User