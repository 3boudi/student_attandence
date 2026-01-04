from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from src.models.attendance import AttendanceRecord
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
    
    attendence_record_id: Optional[int] = Field(
        default=None,
        foreign_key="public.attendance_records.id"
    )
    # Relationships
    attendance_record: Optional["AttendanceRecord"] = Relationship(back_populates="notifications") 
    __table_args__ = {'schema': 'public'}


if TYPE_CHECKING:
    from .user import User