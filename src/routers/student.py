from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from sqlmodel import Session
from datetime import datetime
import shutil
from pathlib import Path

from ..core.database import get_session
from ..core.dependencies import get_current_student, get_current_profile
from ..controllers.student_controller import student_controller
from ..controllers.attendance_controller import attendance_controller
from ..controllers.justification_controller import justification_controller
from ..schema.justification import JustificationCreate, JustificationResponse
from ..schema.attendance import AttendanceRecordResponse, AttendanceSummary
from ..schema.filter import DateRangeFilter
from ..schema.stats import StudentStatistics
from ..models.student import Student
from ..models.user import User

router = APIRouter(prefix="/students", tags=["students"])

@router.post("/attendance/mark", response_model=AttendanceRecordResponse)
async def mark_attendance(
    session_code: str,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Mark Attendance - Student UC1
    """
    try:
        student_profile = current_profile["profile"]
        attendance_record = student_controller.mark_attendance(
            db, student_profile.id, session_code
        )
        
        return attendance_record
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to mark attendance: {str(e)}"
        )

@router.get("/attendance", response_model=List[AttendanceRecordResponse])
async def view_personal_attendance(
    module_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    View Personal Attendance Information - Student UC2
    """
    try:
        student_profile = current_profile["profile"]
        
        # Create filter object
        filters = DateRangeFilter(start_date=start_date, end_date=end_date)
        
        attendance_records = student_controller.view_attendance(
            db, student_profile.id, filters
        )
        
        # Filter by module if specified
        if module_id:
            attendance_records = [
                record for record in attendance_records 
                if record.session and record.session.module_id == module_id
            ]
        
        return attendance_records
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load attendance information: {str(e)}"
        )

@router.get("/attendance/summary", response_model=AttendanceSummary)
async def get_attendance_summary(
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Get comprehensive attendance summary
    """
    try:
        student_profile = current_profile["profile"]
        summary = student_controller.get_student_attendance_stats(db, student_profile.id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load attendance summary: {str(e)}"
        )

@router.post("/justifications", response_model=JustificationResponse)
async def upload_absence_justification(
    attendance_record_id: str,
    justification_data: JustificationCreate,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Upload Absence Justification - Student UC3
    """
    try:
        student_profile = current_profile["profile"]
        
        justification = student_controller.justify_absence(
            db, student_profile.id, attendance_record_id, justification_data
        )
        
        return justification
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/justifications", response_model=List[JustificationResponse])
async def get_my_justifications(
    status: Optional[str] = None,
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Get all justifications submitted by the student
    """
    student_profile = current_profile["profile"]
    
    from models.enums import JustificationStatus
    justification_status = None
    if status:
        justification_status = JustificationStatus(status)
    
    justifications = justification_controller.get_justifications_by_student(
        db, student_profile.id, justification_status
    )
    
    return justifications

@router.get("/statistics", response_model=StudentStatistics)
async def get_student_statistics(
    current_profile: dict = Depends(get_current_profile),
    db: Session = Depends(get_session)
):
    """
    Get student statistics
    """
    student_profile = current_profile["profile"]
    
    # Get statistics using controller
    stats = student_controller.get_student_attendance_stats(db, student_profile.id)
    # Convert to StudentStatistics schema
    from schema.stats import StudentStatistics
    
    return StudentStatistics(
        student_id=student_profile.id,
        total_modules=stats.get("total_modules", 0),
        total_sessions=stats.get("total_sessions", 0),
        attendance_rate=stats.get("attendance_rate", 0.0),
        justified_absences=stats.get("justified_absences", 0),
        unjustified_absences=stats.get("unjustified_absences", 0),
        exclusion_status={}  # This would be populated from data
    )