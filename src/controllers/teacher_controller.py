from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets
import string

from models.teacher import Teacher
from models.user import User
from models.session import Session as ClassSession
from models.attendance import AttendanceRecord
from models.justification import Justification
from models.module import Module
from models.specialty import Specialty
from models.enums import AttendanceStatus, JustificationStatus, NotificationType
from schema.session import SessionCreate, SessionUpdate
from .base_controller import BaseController
from models.student import Student

class TeacherController(BaseController[Teacher, None, None]):
    def __init__(self):
        super().__init__(Teacher)
    
    def get_teacher_by_user_id(self, db: Session, user_id: str) -> Optional[Teacher]:
        """Get teacher by user ID"""
        query = select(Teacher).where(Teacher.user_id == user_id)
        teacher = db.exec(query).first()
        return teacher
    
    def get_teacher_with_user(self, db: Session, teacher_id: str) -> Optional[Teacher]:
        """Get teacher with user details"""
        query = select(Teacher).where(Teacher.id == teacher_id)
        teacher = db.exec(query).first()
        
        if teacher:
            user = db.get(User, teacher.user_id)
            teacher.user = user
        
        return teacher
    
    def create_session(self, db: Session, teacher_id: str, 
                      module_id: str, duration_minutes: int = 60) -> ClassSession:
        """Create a new session for a module"""
        # Verify teacher is assigned to the module
        from models.teacher import TeacherModule
        assignment = db.exec(
            select(TeacherModule).where(
                TeacherModule.teacher_id == teacher_id,
                TeacherModule.module_id == module_id
            )
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this module"
            )
        
        # Generate unique session code
        session_code = self._generate_session_code()
        
        # Create session
        session = ClassSession(
            teacher_id=teacher_id,
            module_id=module_id,
            session_code=session_code,
            datetime=datetime.utcnow(),
            duration_minutes=duration_minutes,
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def _generate_session_code(self, length: int = 6) -> str:
        """Generate a random session code"""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def validate_justification(self, db: Session, teacher_id: str,
                              justification_id: str, 
                              decision: str, 
                              reason: Optional[str] = None) -> Justification:
        """Validate a student's justification"""
        justification = db.get(Justification, justification_id)
        
        if not justification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Justification not found"
            )
        
        # Check if teacher is authorized (teacher should be the one who created the session)
        attendance_record = db.get(AttendanceRecord, justification.attendance_record_id)
        if not attendance_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance record not found"
            )
        
        session = db.get(ClassSession, attendance_record.session_id)
        if not session or session.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to validate this justification"
            )
        
        # Update justification status
        if decision == "approve":
            justification.status = JustificationStatus.APPROVED
            # Update attendance status to excluded
            attendance_record.status = AttendanceStatus.EXCLUDED
            db.add(attendance_record)
            
            # Create notification for student
            self._create_validation_notification(
                db, attendance_record.student_id, 
                "Justification Approved", 
                "Your justification has been approved",
                NotificationType.JUSTIFICATION_APPROVED
            )
        elif decision == "reject":
            justification.status = JustificationStatus.REJECTED
            justification.rejection_reason = reason
            
            # Create notification for student
            self._create_validation_notification(
                db, attendance_record.student_id,
                "Justification Rejected",
                f"Your justification has been rejected. Reason: {reason}",
                NotificationType.JUSTIFICATION_REJECTED
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid decision. Must be 'approve' or 'reject'"
            )
        
        justification.validation_date = datetime.utcnow()
        justification.validator_id = teacher_id
        
        db.add(justification)
        db.commit()
        db.refresh(justification)
        return justification
    
    def _create_validation_notification(self, db: Session, student_id: str,
                                       title: str, message: str, 
                                       notification_type: NotificationType):
        """Create notification for student about justification validation"""
        from models.notification import Notification
        
        # Get student to get user_id
        student = db.get(Student, student_id)
        if student:
            notification = Notification(
                user_id=student.user_id,
                title=title,
                message=message,
                type=notification_type
            )
            db.add(notification)
    
    def view_attendance_records(self, db: Session, teacher_id: str,
                               module_id: Optional[str] = None,
                               session_id: Optional[str] = None,
                               date: Optional[datetime] = None) -> List[AttendanceRecord]:
        """View attendance records for teacher's sessions"""
        query = select(AttendanceRecord)
        
        # Join with session and filter by teacher
        query = query.join(ClassSession).where(ClassSession.teacher_id == teacher_id)
        
        # Apply additional filters
        if module_id:
            query = query.where(ClassSession.module_id == module_id)
        if session_id:
            query = query.where(ClassSession.id == session_id)
        if date:
            # Filter by date (ignoring time)
            query = query.where(
                ClassSession.datetime >= date.replace(hour=0, minute=0, second=0),
                ClassSession.datetime <= date.replace(hour=23, minute=59, second=59)
            )
        
        # Order by session datetime
        query = query.order_by(ClassSession.datetime.desc())
        
        attendance_records = db.exec(query).all()
        return attendance_records
    
    def get_teacher_modules(self, db: Session, teacher_id: str) -> List[Module]:
        """Get all modules assigned to a teacher"""
        from models.teacher import TeacherModule
        
        query = select(Module).join(TeacherModule).where(
            TeacherModule.teacher_id == teacher_id
        )
        modules = db.exec(query).all()
        return modules
    
    def get_teacher_specialties(self, db: Session, teacher_id: str) -> List[Specialty]:
        """Get all specialties assigned to a teacher"""
        from models.teacher import TeacherSpecialty
        
        query = select(Specialty).join(TeacherSpecialty).where(
            TeacherSpecialty.teacher_id == teacher_id
        )
        specialties = db.exec(query).all()
        return specialties
    
    def close_session(self, db: Session, teacher_id: str, session_id: str) -> ClassSession:
        """Close an active session"""
        session = db.get(ClassSession, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to close this session"
            )
        
        session.is_active = False
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def get_pending_justifications(self, db: Session, teacher_id: str) -> List[Justification]:
        """Get pending justifications for teacher's sessions"""
        query = select(Justification).join(AttendanceRecord).join(ClassSession).where(
            Justification.status == JustificationStatus.PENDING,
            ClassSession.teacher_id == teacher_id
        )
        
        justifications = db.exec(query).all()
        return justifications
    
    def get_teacher_statistics(self, db: Session, teacher_id: str) -> Dict[str, Any]:
        """Get statistics for a teacher"""
        # Get all teacher's sessions
        sessions = db.exec(
            select(ClassSession).where(ClassSession.teacher_id == teacher_id)
        ).all()
        
        # Get attendance records for these sessions
        session_ids = [session.id for session in sessions]
        attendance_query = select(AttendanceRecord).where(
            AttendanceRecord.session_id.in_(session_ids)
        )
        attendance_records = db.exec(attendance_query).all()
        
        # Calculate statistics
        total_sessions = len(sessions)
        active_sessions = sum(1 for s in sessions if s.is_active)
        
        total_attendance = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status == AttendanceStatus.PRESENT)
        absent = sum(1 for r in attendance_records if r.status == AttendanceStatus.ABSENT)
        
        # Get pending justifications
        pending_justifications = len(self.get_pending_justifications(db, teacher_id))
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_attendance_records": total_attendance,
            "present_count": present,
            "absent_count": absent,
            "attendance_rate": round((present / total_attendance * 100), 2) if total_attendance > 0 else 0,
            "pending_justifications": pending_justifications,
            "assigned_modules": len(self.get_teacher_modules(db, teacher_id)),
            "assigned_specialties": len(self.get_teacher_specialties(db, teacher_id))
        }

teacher_controller = TeacherController()