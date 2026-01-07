from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status, UploadFile
from datetime import datetime
import os
import uuid

from ..models.student import Student
from ..models.attendance import AttendanceRecord
from ..models.justification import Justification
from ..models.enrollement import Enrollment
from ..models.session import Session as ClassSession
from ..models.module import Module
from ..models.enums import AttendanceStatus, JustificationStatus, NotificationType
from .notification_controller import NotificationController


class StudentController:
    """
    Student Controller - Handles student-related operations
    
    Methods:
        - mark_attendance(): Mark attendance using session code
        - view_attendance_records(): View all attendance records
        - justify_absence(): Submit justification for an absence
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_student_by_id(self, student_id: int) -> Student:
        """Get student by ID"""
        student = self.session.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} not found"
            )
        return student
    
    def get_student_by_user_id(self, user_id: int) -> Student:
        """Get student by user ID"""
        student = self.session.exec(
            select(Student).where(Student.user_id == user_id)
        ).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with user ID {user_id} not found"
            )
        return student
    
    def get_student_enrollments(self, student_id: int) -> List[Enrollment]:
        """Get all enrollments for a student"""
        student = self.get_student_by_id(student_id)
        
        enrollments = self.session.exec(
            select(Enrollment).where(Enrollment.student_id == student_id)
        ).all()
        
        return enrollments
    
    def mark_attendance(self, student_id: int, session_code: str) -> AttendanceRecord:
        """
        Mark student attendance using the session code.
        
        Args:
            student_id: ID of the student
            session_code: The session code to mark attendance
            
        Returns:
            AttendanceRecord: Updated attendance record
        """
        student = self.get_student_by_id(student_id)
        
        # Find session by code
        session_obj = self.session.exec(
            select(ClassSession).where(ClassSession.session_code == session_code)
        ).first()
        
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid session code"
            )
        
        if not session_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is closed. Cannot mark attendance."
            )
        
        # Get the module from teacher_module relationship
        from ..models.teacher_modules import TeacherModules
        teacher_module = self.session.get(TeacherModules, session_obj.teacher_module_id)
        if not teacher_module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found for this session"
            )
        
        module_id = teacher_module.module_id
        
        # Find student's enrollment in this module
        enrollment = self.session.exec(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.module_id == module_id
            )
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this module"
            )
        
        if enrollment.is_excluded:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are excluded from this module"
            )
        
        # Find attendance record for this session and enrollment
        attendance = self.session.exec(
            select(AttendanceRecord).where(
                AttendanceRecord.session_id == session_obj.id,
                AttendanceRecord.enrollement_id == enrollment.id
            )
        ).first()
        
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No attendance record found for this session"
            )
        
        if attendance.status == AttendanceStatus.PRESENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance already marked as present"
            )
        
        # Mark as present
        attendance.status = AttendanceStatus.PRESENT
        self.session.add(attendance)
        self.session.commit()
        self.session.refresh(attendance)
        
        return attendance
    
    def view_attendance_records(
        self, 
        student_id: int, 
        module_id: Optional[int] = None,
        status_filter: Optional[AttendanceStatus] = None
    ) -> List[Dict[str, Any]]:
        """
        View all attendance records for a student.
        
        Args:
            student_id: ID of the student
            module_id: Optional - filter by module
            status_filter: Optional - filter by status
            
        Returns:
            List of attendance records with details
        """
        student = self.get_student_by_id(student_id)
        
        # Get student's enrollments
        enrollments_query = select(Enrollment).where(Enrollment.student_id == student_id)
        if module_id:
            enrollments_query = enrollments_query.where(Enrollment.module_id == module_id)
        
        enrollments = self.session.exec(enrollments_query).all()
        enrollment_ids = [e.id for e in enrollments]
        
        if not enrollment_ids:
            return []
        
        # Get attendance records
        attendance_query = select(AttendanceRecord).where(
            AttendanceRecord.enrollement_id.in_(enrollment_ids)
        )
        
        if status_filter:
            attendance_query = attendance_query.where(
                AttendanceRecord.status == status_filter
            )
        
        attendance_records = self.session.exec(attendance_query).all()
        
        results = []
        for record in attendance_records:
            session_obj = self.session.get(ClassSession, record.session_id)
            module = self.session.get(Module, record.module_id)
            
            results.append({
                "attendance_id": record.id,
                "module_id": record.module_id,
                "module_name": module.name if module else "Unknown",
                "session_id": record.session_id,
                "session_date": session_obj.date_time if session_obj else None,
                "status": record.status.value if record.status else "ABSENT",
                "has_justification": record.justification is not None
            })
        
        return results
    
    def get_attendance_summary(self, student_id: int) -> Dict[str, Any]:
        """Get attendance summary for a student"""
        student = self.get_student_by_id(student_id)
        
        # Get all enrollments
        enrollments = self.session.exec(
            select(Enrollment).where(Enrollment.student_id == student_id)
        ).all()
        
        enrollment_ids = [e.id for e in enrollments]
        
        if not enrollment_ids:
            return {
               
                "absent": 0,
                }
        
        # Get all attendance records
        attendance_records = self.session.exec(
            select(AttendanceRecord).where(
                AttendanceRecord.enrollement_id.in_(enrollment_ids)
            )
        ).all()
        
        absent = sum(1 for r in attendance_records if r.status == AttendanceStatus.ABSENT)
        
        return {
            "absent": absent,
        }
    
    def justify_absence(
        self, 
        student_id: int, 
        attendance_record_id: int,
        comment: str,
        file_url: Optional[str] = None
    ) -> Justification:
        """
        Submit a justification for an absence.
        
        Args:
            student_id: ID of the student
            attendance_id: ID of the attendance record
            reason: Reason for the absence
            document_url: Optional URL to supporting document
            
        Returns:
            Justification: The created justification
        """
        student = self.get_student_by_id(student_id)
        
        # Get attendance record
        attendance = self.session.get(AttendanceRecord, attendance_record_id)
        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attendance record with ID {attendance_record_id} not found"
            )
        
        # Verify attendance belongs to student
        enrollment = self.session.get(Enrollment, attendance.enrollement_id)
        if not enrollment or enrollment.student_id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This attendance record does not belong to you"
            )
        
        # Check if attendance is ABSENT
        if attendance.status != AttendanceStatus.ABSENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only justify absences"
            )
        
        # Check if justification already exists
        existing = self.session.exec(
            select(Justification).where(Justification.attendance_record_id == attendance_record_id)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A justification already exists for this absence"
            )
        
        # Create justification
        justification = Justification(
            attendance_record_id=attendance_record_id,
            comment=comment,
            file_url=file_url,
            status=JustificationStatus.PENDING,
            submitted_at=datetime.utcnow()
        )
        
        self.session.add(justification)
        self.session.commit()
        self.session.refresh(justification)
        
        # Create notification for justification submitted
        notification_ctrl = NotificationController(self.session)
        notification_ctrl.create_notification(
            user_id=student.user_id,
            title="Justification Submitted",
            message=f"Your justification for attendance record #{attendance_record_id} has been submitted and is pending review.",
            notification_type=NotificationType.JUSTIFICATION_SUBMITTED
        )
        
        return justification
    
    def get_justifications(self, student_id: int) -> List[Justification]:
        """Get all justifications submitted by a student"""
        student = self.get_student_by_id(student_id)
        
        # Get student's enrollments
        enrollments = self.session.exec(
            select(Enrollment).where(Enrollment.student_id == student_id)
        ).all()
        
        enrollment_ids = [e.id for e in enrollments]
        
        # Get attendance records
        attendance_records = self.session.exec(
            select(AttendanceRecord).where(
                AttendanceRecord.enrollement_id.in_(enrollment_ids)
            )
        ).all()
        
        attendance_ids = [a.id for a in attendance_records]
        
        # Get justifications
        justifications = self.session.exec(
            select(Justification).where(
                Justification.attendance_id.in_(attendance_ids)
            )
        ).all()
        
        return justifications
    
    def get_modules(self, student_id: int) -> List[Module]:
        """Get all modules a student is enrolled in"""
        student = self.get_student_by_id(student_id)
        
        enrollments = self.session.exec(
            select(Enrollment).where(
                Enrollment.student_id == student_id,
                Enrollment.is_excluded == False
            )
        ).all()
        
        modules = []
        for enrollment in enrollments:
            module = self.session.get(Module, enrollment.module_id)
            if module:
                modules.append(module)
        
        return modules
