from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlmodel import Session
from datetime import datetime

from ..core.database import get_session
from ..core.dependencies import get_current_teacher, get_current_profile
from controllers.teacher_controller import teacher_controller
from controllers.session_controller import session_controller
from controllers.attendance_controller import attendance_controller
from controllers.justification_controller import justification_controller
from schema.session import SessionCreate, SessionResponse, SessionWithQR
from schema.attendance import AttendanceRecordResponse, AttendanceBulkCreate, AttendanceSummary
from schema.justification import JustificationResponse, JustificationValidation
from schema.filter import DateRangeFilter
from schema.stats import TeacherStatistics
from models.teacher import Teacher
from models.user import User

router = APIRouter(prefix="/teachers", tags=["teachers"])

@router.post("/sessions", response_model=SessionWithQR)
async def create_class_session(
    session_data: SessionCreate,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Create Class Sessions - Teacher UC1
    """
    try:
        teacher_profile = current_profile["profile"]
        
        # Check if teacher already has an active session
        from sqlmodel import select
        from models.session import Session as ClassSession
        
        active_sessions = db.exec(
            select(ClassSession).where(
                ClassSession.teacher_id == teacher_profile.id,
                ClassSession.is_active == True
            )
        ).all()
        
        if active_sessions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active session."
            )
        
        # Create session using schema data
        session = teacher_controller.create_session(
            db, teacher_profile.id, session_data.module_id, session_data.duration_minutes
        )
        
        return session
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create session: {str(e)}"
        )

@router.post("/justifications/{justification_id}/validate", response_model=JustificationResponse)
async def validate_student_absence_justification(
    justification_id: str,
    validation_data: JustificationValidation,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Validate Student Absence Justification - Teacher UC2
    """
    try:
        teacher_profile = current_profile["profile"]
        
        justification = teacher_controller.validate_justification(
            db, teacher_profile.id, justification_id, 
            validation_data.decision, validation_data.reason
        )
        
        return justification
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to process justification: {str(e)}"
        )

@router.get("/attendance/records", response_model=List[AttendanceRecordResponse])
async def view_attendance_records(
    module_id: Optional[str] = None,
    session_id: Optional[str] = None,
    date: Optional[datetime] = None,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    View Attendance Records - Teacher UC3
    """
    try:
        teacher_profile = current_profile["profile"]
        
        attendance_records = teacher_controller.view_attendance_records(
            db, teacher_profile.id, module_id, session_id, date
        )
        
        return attendance_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load attendance data: {str(e)}"
        )

@router.get("/statistics", response_model=TeacherStatistics)
async def get_teacher_statistics(
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Get teacher statistics
    """
    teacher_profile = current_profile["profile"]
    
    stats = teacher_controller.get_teacher_statistics(db, teacher_profile.id)
    
    # Convert to TeacherStatistics schema
    from schema.stats import TeacherStatistics
    
    return TeacherStatistics(
        teacher_id=teacher_profile.id,
        assigned_modules=stats.get("assigned_modules", 0),
        conducted_sessions=stats.get("total_sessions", 0),
        total_students=stats.get("total_students", 0),
        average_attendance_rate=stats.get("attendance_rate", 0.0),
        pending_justifications=stats.get("pending_justifications", 0)
    )