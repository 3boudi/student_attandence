from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SpecialtyBase(BaseModel):
    """Base specialty schema"""
    name: str
    year_level: str

class SpecialtyCreate(SpecialtyBase):
    """Schema for creating a specialty"""
    pass

class SpecialtyUpdate(BaseModel):
    """Schema for updating a specialty"""
    name: Optional[str] = None
    year_level: Optional[str] = None

class SpecialtyResponse(SpecialtyBase):
    """Schema for specialty response"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    modules: Optional[List[Dict[str, Any]]] = None
    students: Optional[List[Dict[str, Any]]] = None
    teachers: Optional[List[Dict[str, Any]]] = None
    schedule: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)