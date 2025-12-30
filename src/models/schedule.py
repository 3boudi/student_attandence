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
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    specialty_id: str = Field(foreign_key="specialty.id")
    specialty: Optional["Specialty"] = Relationship(back_populates="schedule")
    
    # For timetable, we'll store it as JSON or have separate SessionSchedule table
    # In practice, you might want a separate SessionSchedule table
    
    __table_args__ = {'schema': 'public'}
    