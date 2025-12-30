from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from passlib.context import CryptContext

from models.admin import Admin
from models.user import User
from models.student import Student
from models.teacher import Teacher
from models.specialty import Specialty
from models.module import Module
from models.schedule import Schedule
from models.attendance import AttendanceRecord
from models.session import Session as ClassSession
from models.teacher import TeacherModule
from schema.specialty import SpecialtyCreate, SpecialtyUpdate
from schema.module import ModuleCreate, ModuleUpdate
from schema.schedule import ScheduleCreate, ScheduleUpdate
from .base_controller import BaseController

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

class AdminController(BaseController[Admin, None, None]):
    def __init__(self):
        super().__init__(Admin)
    
    def get_admin_by_user_id(self, db: Session, user_id: str) -> Optional[Admin]:
        """Get admin by user ID"""
        query = select(Admin).where(Admin.user_id == user_id)
        admin = db.exec(query).first()
        return admin
    
    # Student Management
    def add_student(self, db: Session, user_data: Dict[str, Any], 
                   specialty_id: Optional[str] = None) -> Student:
        """Add a new student"""
        from auth.schemas import UserCreate
        
        # Create user first
        user_create = UserCreate(
            **user_data,
            role="student"
        )
        
        # Note: In practice, you'd use the UserManager to create the user
        # For now, we'll create directly
        from models.user import User
        from models.student import Student
        
        # Check if user with email already exists
        existing_user = db.exec(
            select(User).where(User.email == user_create.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        user = User(
            **user_create.model_dump(exclude={'password'}),
            hashed_password=get_password_hash(user_create.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create student profile
        student = Student(
            user_id=user.id,
            specialty_id=specialty_id
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        
        return student
    
    def update_student(self, db: Session, student_id: str, 
                      updates: Dict[str, Any]) -> Student:
        """Update student information"""
        student = db.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Update student fields
        for key, value in updates.items():
            if hasattr(student, key):
                setattr(student, key, value)
        
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    
    def delete_student(self, db: Session, student_id: str):
        """Delete a student"""
        student = db.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        # Get associated user
        user = db.get(User, student.user_id)
        
        # Delete student and user
        db.delete(student)
        if user:
            db.delete(user)
        
        db.commit()
    
    # Teacher Management
    def add_teacher(self, db: Session, user_data: Dict[str, Any]) -> Teacher:
        """Add a new teacher"""
        from auth.schemas import UserCreate
        from models.user import User
        from models.teacher import Teacher
        
        # Create user
        user_create = UserCreate(
            **user_data,
            role="teacher"
        )
        
        # Check if user with email already exists
        existing_user = db.exec(
            select(User).where(User.email == user_create.email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        user = User(
            **user_create.model_dump(exclude={'password'}),
            hashed_password=get_password_hash(user_create.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create teacher profile
        teacher = Teacher(user_id=user.id)
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        
        return teacher
    
    def assign_module_to_teacher(self, db: Session, teacher_id: str, 
                                module_id: str) -> TeacherModule:
        """Assign a module to a teacher"""
        # Check if teacher exists
        teacher = db.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Check if module exists
        module = db.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        # Check if assignment already exists
        existing_assignment = db.exec(
            select(TeacherModule).where(
                TeacherModule.teacher_id == teacher_id,
                TeacherModule.module_id == module_id
            )
        ).first()
        
        if existing_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Module already assigned to teacher"
            )
        
        # Create assignment
        assignment = TeacherModule(
            teacher_id=teacher_id,
            module_id=module_id
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
    
    # Module Management
    def add_module(self, db: Session, module_data: Dict[str, Any], 
                  specialty_id: Optional[str] = None) -> Module:
        """Add a new module"""
        from models.module import Module
        
        # Check if module code already exists
        existing_module = db.exec(
            select(Module).where(Module.module_code == module_data.get('module_code'))
        ).first()
        
        if existing_module:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Module with this code already exists"
            )
        
        # Create module
        module = Module(
            **module_data,
            specialty_id=specialty_id
        )
        
        db.add(module)
        db.commit()
        db.refresh(module)
        return module
    
    # Specialty Management
    def add_specialty(self, db: Session, specialty_data: Dict[str, Any]) -> Specialty:
        """Add a new specialty"""
        from models.specialty import Specialty
        
        # Check if specialty with same name and year already exists
        existing_specialty = db.exec(
            select(Specialty).where(
                Specialty.name == specialty_data.get('name'),
                Specialty.year_level == specialty_data.get('year_level')
            )
        ).first()
        
        if existing_specialty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specialty already exists"
            )
        
        # Create specialty
        specialty = Specialty(**specialty_data)
        
        db.add(specialty)
        db.commit()
        db.refresh(specialty)
        return specialty
    
    # Schedule Management
    def create_schedule(self, db: Session, specialty_id: str,
                       schedule_data: Dict[str, Any]) -> Schedule:
        """Create a schedule for a specialty"""
        from models.schedule import Schedule
        
        # Check if specialty exists
        specialty = db.get(Specialty, specialty_id)
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specialty not found"
            )
        
        # Check if schedule already exists for this specialty
        existing_schedule = db.exec(
            select(Schedule).where(Schedule.specialty_id == specialty_id)
        ).first()
        
        if existing_schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule already exists for this specialty"
            )
        
        # Create schedule
        schedule = Schedule(
            specialty_id=specialty_id,
            **schedule_data
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule
    
    # Attendance Monitoring
    def monitor_attendance(self, db: Session,
                          specialty_id: Optional[str] = None,
                          module_id: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[AttendanceRecord]:
        """Monitor attendance across the system"""
        query = select(AttendanceRecord)
        
        # Apply filters
        if specialty_id or module_id or start_date or end_date:
            query = query.join(ClassSession)
            
            if specialty_id:
                query = query.join(Module).where(Module.specialty_id == specialty_id)
            if module_id:
                query = query.where(ClassSession.module_id == module_id)
            if start_date:
                query = query.where(ClassSession.datetime >= start_date)
            if end_date:
                query = query.where(ClassSession.datetime <= end_date)
        
        # Order by date
        query = query.join(ClassSession).order_by(ClassSession.datetime.desc())
        
        attendance_records = db.exec(query).all()
        return attendance_records
    
    def get_system_statistics(self, db: Session) -> Dict[str, Any]:
        """Get system-wide statistics"""
        from models.enums import AttendanceStatus
        
        # Count users
        total_users = db.exec(select(User)).count()
        students = db.exec(select(Student)).count()
        teachers = db.exec(select(Teacher)).count()
        admins = db.exec(select(Admin)).count()
        
        # Count specialties and modules
        specialties = db.exec(select(Specialty)).count()
        modules = db.exec(select(Module)).count()
        
        # Attendance statistics
        attendance_records = db.exec(select(AttendanceRecord)).all()
        total_attendance = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status == AttendanceStatus.PRESENT)
        
        # Justification statistics
        from models.justification import Justification
        from models.enums import JustificationStatus
        justifications = db.exec(select(Justification)).all()
        pending_justifications = sum(1 for j in justifications if j.status == JustificationStatus.PENDING)
        
        return {
            "total_users": total_users,
            "students": students,
            "teachers": teachers,
            "admins": admins,
            "specialties": specialties,
            "modules": modules,
            "attendance_records": total_attendance,
            "attendance_rate": round((present / total_attendance * 100), 2) if total_attendance > 0 else 0,
            "pending_justifications": pending_justifications
        }

admin_controller = AdminController()