from sqlmodel import Relationship, SQLModel, Field
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .admin import Admin
class ReportBase(SQLModel):
    content: str
    period_start: datetime
    period_end: datetime

class Report(ReportBase, table=True):
    __tablename__ = "report"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)  # ✅ Changed from UUID to int
    generated_date: datetime = Field(default_factory=datetime.utcnow)
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    
    admin_id: int = Field(foreign_key="public.users.id")
    admin: "Admin" = Relationship(back_populates="reports")
    
    __table_args__ = {'schema': 'public'}