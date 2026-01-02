from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class ReportBase(SQLModel):
    content: str
    period_start: datetime
    period_end: datetime

class Report(ReportBase, table=True):
    __tablename__ = "reports"  # ✅ Add explicit table name
    
    id: Optional[int] = Field(default=None, primary_key=True)  # ✅ Changed from UUID to int
    generated_date: datetime = Field(default_factory=datetime.utcnow)
    pdf_url: Optional[str] = None
    excel_url: Optional[str] = None
    
    __table_args__ = {'schema': 'public'}