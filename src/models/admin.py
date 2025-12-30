from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from .user import User
import uuid

class AdminBase(SQLModel):
    # Admin-specific fields can go here
    pass

class Admin(AdminBase, table=True):
    __tablename__ = "admins"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    
    # Foreign key to User
    user_id: str = Field(foreign_key="users.id", unique=True)
    user: Optional["User"] = Relationship(back_populates="admin_profile")
    
    __table_args__ = {'schema': 'public'}