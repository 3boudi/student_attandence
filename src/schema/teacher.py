from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .user import UserResponse

class TeacherBase(BaseModel):
    """Base teacher schema"""
    pass

class TeacherCreate(TeacherBase):
    """Schema for creating a teacher"""
    user: Dict[str, Any]  # UserCreate dict
    assigned_modules: Optional[List[str]] = Field(default_factory=list)
    assigned_specialties: Optional[List[str]] = Field(default_factory=list)

class TeacherUpdate(BaseModel):
    """Schema for updating a teacher"""
    assigned_modules: Optional[List[str]] = None
    assigned_specialties: Optional[List[str]] = None

class TeacherResponse(TeacherBase):
    """Schema for teacher response"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    assigned_modules: Optional[List[Dict[str, Any]]] = None
    assigned_specialties: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(from_attributes=True)

class TeacherAssignment(BaseModel):
    """Schema for teacher-module assignment"""
    teacher_id: int
    module_id: int
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    teaching_hours_per_week: Optional[int] = None