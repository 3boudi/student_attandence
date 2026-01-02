from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional, Dict, Any
from sqlmodel import Session
from datetime import datetime
import csv
import io
import shutil
from pathlib import Path

from ..core.database import get_session
from ..core.dependencies import get_current_admin, get_current_profile
from ..controllers.admin_controller import admin_controller
from ..controllers.user_controller import user_controller
from ..controllers.attendance_controller import attendance_controller
from ..controllers.justification_controller import justification_controller
from ..schema.user import UserCreate, UserResponse
from ..schema.student import StudentCreate, StudentResponse
from ..schema.teacher import TeacherCreate, TeacherResponse
from ..schema.specialty import SpecialtyCreate, SpecialtyResponse
from ..schema.module import ModuleCreate, ModuleResponse
from ..schema.report import ReportExport, ReportResponse
from ..schema.bulk import BulkStudentImport, ImportResult
from ..schema.filter import PaginationParams, UserFilter
from ..schema.stats import SystemStatistics
from ..models.admin import Admin
from ..models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/students", response_model=StudentResponse)
async def add_student(
    student_data: StudentCreate,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Add Student - Admin UC1 Main Flow
    """
    try:
        # Extract user data from student_data
        user_create_data = student_data.user
        
        # Create UserCreate object
        from schema.user import UserCreate
        user_create = UserCreate(
            **user_create_data,
            role="student"
        )
        
        student = admin_controller.add_student(
            db, user_create.dict(), student_data.specialty_id
        )
        
        return student
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create student account: {str(e)}"
        )

@router.post("/students/bulk-import", response_model=ImportResult)
async def bulk_import_students(
    import_data: BulkStudentImport,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Bulk Import Students - Admin UC1 Alternative Flow A3
    
    Expected JSON format from frontend (parsed from CSV):
    {
        "students": [
            {
                "user": {
                    "full_name": "John Doe",
                    "email": "john@example.com",
                    "password": "password123",
                    "department": "Computer Science"
                },
                "specialty_id": "specialty-uuid-here"
            }
        ],
        "send_welcome_emails": true
    }
    """
    # Verify admin access
    if current_profile["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        students_created = []
        errors = []
        
        for i, student_data in enumerate(import_data.students, start=1):
            try:
                # Extract user data
                user_create_data = student_data.get("user", {})
                
                # Validate required fields
                if not user_create_data:
                    errors.append(f"Student {i}: User data is required")
                    continue
                if "email" not in user_create_data or not user_create_data.get("email"):
                    errors.append(f"Student {i}: Email is required")
                    continue
                if "full_name" not in user_create_data or not user_create_data.get("full_name"):
                    errors.append(f"Student {i}: Full name is required")
                    continue
                if "password" not in user_create_data or not user_create_data.get("password"):
                    errors.append(f"Student {i}: Password is required")
                    continue
                if "department" not in user_create_data or not user_create_data.get("department"):
                    errors.append(f"Student {i}: Department is required")
                    continue
                
                specialty_id = student_data.get("specialty_id")
                if not specialty_id:
                    errors.append(f"Student {i}: Specialty ID is required")
                    continue
                
                user_create = UserCreate(
                    **user_create_data,
                    role="student"
                )
                
                student = admin_controller.add_student(db, user_create.model_dump(), specialty_id)
                students_created.append(student)
                
            except Exception as e:
                errors.append(f"Student {i}: {str(e)}")
        
        # Generate import summary
        summary = ImportResult(
            total_processed=len(import_data.students),
            successful=len(students_created),
            failed=len(errors),
            errors=errors
        )
        
        return summary
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to process bulk import: {str(e)}"
        )

@router.get("/students", response_model=List[StudentResponse])
async def search_students(
    query: Optional[str] = None,
    specialty_id: Optional[str] = None,
    pagination: PaginationParams = None,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Search students by various criteria
    """
    from sqlmodel import select, or_
    from models.student import Student
    from models.user import User
    
    if pagination is None:
        pagination = PaginationParams()
    
    search_query = select(Student)
    
    if query:
        search_query = search_query.join(User).where(
            or_(
                User.full_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )
    
    if specialty_id:
        search_query = search_query.where(Student.specialty_id == specialty_id)
    
    students = db.exec(
        search_query.offset(pagination.skip).limit(pagination.limit)
    ).all()
    
    # Load user information for each student
    for student in students:
        student.user = db.get(User, student.user_id)
    
    return students

@router.post("/teachers", response_model=TeacherResponse)
async def add_teacher(
    teacher_data: TeacherCreate,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Add Teacher - Admin UC2 Main Flow
    """
    try:
        # Extract user data from teacher_data
        user_create_data = teacher_data.user
        
        # Create UserCreate object
        from schema.user import UserCreate
        user_create = UserCreate(
            **user_create_data,
            role="teacher"
        )
        
        teacher = admin_controller.add_teacher(db, user_create.dict())
        
        return teacher
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create teacher account: {str(e)}"
        )

@router.post("/modules", response_model=ModuleResponse)
async def add_module(
    module_data: ModuleCreate,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Add Module - Admin UC3 Main Flow
    """
    try:
        module = admin_controller.add_module(db, module_data.dict())
        return module
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create module: {str(e)}"
        )

@router.get("/statistics", response_model=SystemStatistics)
async def get_system_statistics(
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Get system-wide statistics
    """
    try:
        stats = admin_controller.get_system_statistics(db)
        
        # Convert to SystemStatistics schema
        from schema.stats import SystemStatistics
        
        return SystemStatistics(
            total_users=stats.get("total_users", 0),
            total_students=stats.get("students", 0),
            total_teachers=stats.get("teachers", 0),
            total_admins=stats.get("admins", 0),
            total_modules=stats.get("modules", 0),
            total_specialties=stats.get("specialties", 0),
            total_sessions=stats.get("total_sessions", 0),
            total_attendance_records=stats.get("attendance_records", 0),
            total_pending_justifications=stats.get("pending_justifications", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load system statistics: {str(e)}"
        )

@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    report_data: ReportExport,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Generate a report
    """
    try:
        # This would be implemented in a report controller
        # For now, return placeholder
        
        from schema.report import ReportResponse
        import datetime
        
        return ReportResponse(
            id="report_001",
            report_type=report_data.filters.get("type", "attendance") if report_data.filters else "attendance",
            period_start=datetime.datetime.utcnow() - datetime.timedelta(days=30),
            period_end=datetime.datetime.utcnow(),
            filters=report_data.filters,
            content="Report content would be generated here",
            generated_date=datetime.datetime.utcnow(),
            generated_by=current_profile["user"].id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate report: {str(e)}"
        )