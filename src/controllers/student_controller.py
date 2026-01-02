from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, or_
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from ..models.student import Student
from ..models.user import User
from ..models.attendance import AttendanceRecord
from ..models.session import Session as ClassSession
from ..models.justification import Justification
from ..models.specialty import Specialty
from ..schema.student import StudentCreate, StudentUpdate
from ..schema.attendance import AttendanceRecordCreate, AttendanceBulkCreate
from ..schema.justification import JustificationCreate, JustificationValidation
from ..schema.filter import PaginationParams, DateRangeFilter
from .base_controller import BaseController

class StudentController(BaseController[Student, StudentCreate, StudentUpdate]):
    def __init__(self):
        super().__init__(Student)
    
    def get_student_by_user_id(self, db: Session, user_id: int) -> Optional[Student]:
        """Get student by user ID"""
        query = select(Student).where(Student.user_id == user_id)
        student = db.exec(query).first()
        return student
    
    def get_student_with_user(self, db: Session, student_id: int) -> Optional[Student]:
        """Get student with user details"""
        query = select(Student).where(Student.id == student_id)
        student = db.exec(query).first()
        
        if student:
            # Eager load user
            user = db.get(User, student.user_id)
            student.user = user
        
        return student
    
    def mark_attendance(self, db: Session, student_id: int, session_code: str) -> AttendanceRecord:
        """Mark attendance for a student in a session"""
        # Find session by code
        session_query = select(ClassSession).where(
            ClassSession.session_code == session_code,
            ClassSession.is_active == True
        )
        session = db.exec(session_query).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or inactive"
            )
        
        # Check if session is still valid (within duration)
        session_end = session.datetime + timedelta(minutes=session.duration_minutes)
        if datetime.utcnow() > session_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session has ended"
            )
        
        # Check if attendance already exists
        existing_attendance = db.exec(
            select(AttendanceRecord).where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.session_id == session.id
            )
        ).first()
        
        if existing_attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance already marked for this session"
            )
        
        # Create attendance record
        from ..models.enums import AttendanceStatus
        attendance = AttendanceRecord(
            student_id=student_id,
            session_id=session.id,
            status=AttendanceStatus.PRESENT
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance
    
    def view_attendance(self, db: Session, student_id: int, 
                       filters: DateRangeFilter = None) -> List[AttendanceRecord]:
        """Get attendance records for a student"""
        query = select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id
        )
        
        # Apply date filters if provided
        if filters and filters.start_date:
            query = query.join(ClassSession).where(ClassSession.datetime >= filters.start_date)
        if filters and filters.end_date:
            query = query.join(ClassSession).where(ClassSession.datetime <= filters.end_date)
        
        # Order by session datetime
        query = query.join(ClassSession).order_by(ClassSession.datetime.desc())
        
        attendance_records = db.exec(query).all()
        return attendance_records
    
    def justify_absence(self, db: Session, student_id: int, 
                       attendance_record_id: int, 
                       justification_data: JustificationCreate) -> Justification:
        """Submit justification for absence"""
        # Check if attendance record exists and belongs to student
        attendance = db.get(AttendanceRecord, attendance_record_id)
        if not attendance or attendance.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        # Check if justification already exists
        existing_justification = db.exec(
            select(Justification).where(
                Justification.attendance_record_id == attendance_record_id
            )
        ).first()
        
        if existing_justification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Justification already submitted for this absence"
            )
        
        # Check if attendance is marked as absent
        from ..models.enums import AttendanceStatus
        if attendance.status != AttendanceStatus.ABSENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only justify absences"
            )
        
        # Create justification using schema data
        justification = Justification(
            student_id=student_id,
            attendance_record_id=attendance_record_id,
            **justification_data.dict()
        )
        
        db.add(justification)
        db.commit()
        db.refresh(justification)
        
        return justification
    def get_student_statics(self, db: Session, student_id: int) -> Dict[str, Any]:
        """Get attendance statistics for a student"""
        total_records = db.exec(
            select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
        ).all()
        
        total_count = len(total_records)
        present_count = len([rec for rec in total_records if rec.status.name == "PRESENT"])
        absent_count = len([rec for rec in total_records if rec.status.name == "ABSENT"])
        justified_count = len([
            rec for rec in total_records 
            if rec.status.name == "ABSENT" and rec.justification is not None
        ])
        
        stats = {
            "total_sessions": total_count,
            "present": present_count,
            "absent": absent_count,
            "justified_absences": justified_count,
            "attendance_rate": (present_count / total_count * 100) if total_count > 0 else 0.0
        }
        
        return stats
    
    # Update other methods to use schemas...

student_controller = StudentController()