from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, Dict, TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .specialty import Specialty

class ScheduleBase(SQLModel):
    pass

class Schedule(ScheduleBase, table=True):
    __tablename__ = "schedules"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    specialty_id: int = Field(foreign_key="public.specialty.id")
    specialty: Optional["Specialty"] = Relationship(back_populates="schedule")
    
    __table_args__ = {'schema': 'public'}