from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from fastapi import HTTPException, status

from ..models.user import User
from ..models.student import Student
from ..models.teacher import Teacher
from ..models.admin import Admin
from ..schema.user import UserCreate, UserUpdate, UserWithProfile
from .base_controller import BaseController

class UserController(BaseController[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)
    
    def get_user_with_profile(self, db: Session, user_id: int) -> UserWithProfile:
        """Get user with their role-specific profile"""
        user = self.get(db, user_id)
        
        # Load profile based on role
        if user.role == "student":
            student = db.exec(
                select(Student).where(Student.user_id == user.id)
            ).first()
            user.student_profile = student
        elif user.role == "teacher":
            teacher = db.exec(
                select(Teacher).where(Teacher.user_id == user.id)
            ).first()
            user.teacher_profile = teacher
        elif user.role == "admin":
            admin = db.exec(
                select(Admin).where(Admin.user_id == user.id)
            ).first()
            user.admin_profile = admin
        
        return user
    
    def get_users_by_role(self, db: Session, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        query = select(User).where(User.role == role)
        users = db.exec(query.offset(skip).limit(limit)).all()
        return users
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        user = db.exec(query).first()
        return user
    
    def update_user_role(self, db: Session, user_id: int, role: str) -> User:
        """Update user role"""
        user = self.get(db, user_id)
        user.role = role
        
        # Remove existing profiles
        if user.role != "student" and user.student_profile:
            db.delete(user.student_profile)
        if user.role != "teacher" and user.teacher_profile:
            db.delete(user.teacher_profile)
        if user.role != "admin" and user.admin_profile:
            db.delete(user.admin_profile)
        
        # Create new profile if needed
        if role == "student":
            student = Student(user_id=user.id)
            db.add(student)
        elif role == "teacher":
            teacher = Teacher(user_id=user.id)
            db.add(teacher)
        elif role == "admin":
            admin = Admin(user_id=user.id)
            db.add(admin)
        
        db.commit()
        db.refresh(user)
        return user
    
    def deactivate_user(self, db: Session, user_id: int) -> User:
        """Deactivate a user"""
        user = self.get(db, user_id)
        user.is_active = False
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def activate_user(self, db: Session, user_id: int) -> User:
        """Activate a user"""
        user = self.get(db, user_id)
        user.is_active = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

user_controller = UserController()