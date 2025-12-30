from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ModuleBase(BaseModel):
    """Base module schema"""
    module_name: str
    module_code: str
    description: Optional[str] = None
    credits: Optional[int] = None

class ModuleCreate(ModuleBase):
    """Schema for creating a module"""
    specialty_id: Optional[str] = None

class ModuleUpdate(BaseModel):
    """Schema for updating a module"""
    module_name: Optional[str] = None
    module_code: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    specialty_id: Optional[str] = None

class ModuleResponse(ModuleBase):
    """Schema for module response"""
    id: str
    specialty_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    specialty: Optional[Dict[str, Any]] = None
    teachers: Optional[List[Dict[str, Any]]] = None
    sessions: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(from_attributes=True)