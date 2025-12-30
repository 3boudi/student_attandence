from __future__ import annotations
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TypeVar, Generic, Type, TYPE_CHECKING
from datetime import datetime
from .enums import *
import uuid
from typing import Optional, List, TypeVar, Generic, Type, TYPE_CHECKING

# Base User model for fastapi-users
class UserBase(SQLModel):
    full_name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    department: str

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    hashed_password: str
    
    # For fastapi-users
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    
    # Role field to distinguish user types
    role: Optional[str] = Field(default=None, index=True)  # "student", "teacher", "admin"
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Relationships
    notifications: List["Notification"] = Relationship(back_populates="user")
    
    # Polymorphic relationships
    student_profile: Optional["Student"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )
    teacher_profile: Optional["Teacher"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )
    admin_profile: Optional["Admin"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False}
    )
    
    __table_args__ = {'schema': 'public'}
    
    @property
    def profile(self):
        """Get the user's profile based on role"""
        if self.role == "student":
            return self.student_profile
        elif self.role == "teacher":
            return self.teacher_profile
        elif self.role == "admin":
            return self.admin_profile
        return None


if TYPE_CHECKING:
    from .notification import Notification
    from .student import Student
    from .teacher import Teacher
    from .admin import Admin