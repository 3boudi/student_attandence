from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status
from datetime import datetime

from ..models.session import Session as ClassSession
from ..models.attendance import AttendanceRecord
from ..models.teacher import Teacher
from ..models.teacher_modules import TeacherModules
from ..models.enrollement import Enrollment
from ..models.module import Module
from ..models.enums import AttendanceStatus
from .session_controller import SessionController


class TeacherController:
    """
    Teacher Controller - Handles teacher operations
    
    Workflow:
        1. Teacher creates session → SessionController generates QR + code
        2. Creates attendance records for ALL enrolled students (status=ABSENT)
        3. Student scans QR or enters code → mark_attendance → status=PRESENT
        4. Teacher closes session → no more attendance marking
    
    Methods:
        - create_session(): Create session with QR code and attendance records
        - close_session(): Close session
        - get_my_modules(): Get teacher's assigned modules
        - validate_attendance_records(): View attendance for a session
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.session_ctrl = SessionController(session)
    
    def create_session(
        self,
        teacher_id: int,
        module_id: int,
        duration_minutes: int = 90,
        room: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new session with QR code and attendance records.
        
        Workflow:
            1. Verify teacher is assigned to module
            2. Create session with share_code
            3. Generate QR code → save to uploads/qrcodes/
            4. Create attendance records for ALL enrolled students (ABSENT)
        
        Args:
            teacher_id: ID of the teacher
            module_id: ID of the module
            duration_minutes: Session duration (default 90)
            
        Returns:
            dict: Session info with QR code URL and share code
        """
        # Verify teacher exists
        teacher = self.session.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with ID {teacher_id} not found"
            )
        
        # Verify module exists
        module = self.session.get(Module, module_id)
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Module with ID {module_id} not found"
            )
        
        # Verify teacher is assigned to this module
        teacher_module = self.session.exec(
            select(TeacherModules).where(
                TeacherModules.teacher_id == teacher_id,
                TeacherModules.module_id == module_id
            )
        ).first()
        
        if not teacher_module:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not assigned to this module"
            )
        
        # Generate share code using SessionController
        share_code = self.session_ctrl.generate_share_code()
        
        # Create session
        new_session = ClassSession(
            teacher_module_id=teacher_module.id,
            date_time=datetime.utcnow(),
            duration_minutes=duration_minutes,
            session_code=share_code,
            room=room,
            is_active=True
        )
        self.session.add(new_session)
        self.session.commit()
        self.session.refresh(new_session)
        
        # Generate QR code using SessionController
        qrcode_url = self.session_ctrl.generate_qrcode(new_session.id, share_code)
        new_session.session_qrcode = qrcode_url
        self.session.add(new_session)
        self.session.commit()
        
        # Get all enrollments for this module
        enrollments = self.session.exec(
            select(Enrollment).where(
                Enrollment.module_id == module_id,
                Enrollment.is_excluded == False
            )
        ).all()
        
        # Create attendance records for ALL enrolled students (ABSENT by default)
        attendance_records = []
        for enrollment in enrollments:
            attendance = AttendanceRecord(
                session_id=new_session.id,
                enrollement_id=enrollment.id,
                status=AttendanceStatus.ABSENT
            )
            self.session.add(attendance)
            self.session.commit()
            self.session.refresh(attendance)
            
            attendance_records.append({
                "attendance_id": attendance.id,
                "student_id": enrollment.student_id,
                "student_name": enrollment.student_name or "Unknown",
                "student_email": enrollment.student_email or "N/A",
                "enrollment_id": enrollment.id,
                "number_of_absences": enrollment.number_of_absences,
                "number_of_absences_justified": enrollment.number_of_absences_justified,
                "is_excluded": enrollment.is_excluded,
                "status": AttendanceStatus.ABSENT.value
            })
        
        return {
            "session_id": new_session.id,
            "module_id": module_id,
            "module_name": module.name,
            "teacher_id": teacher_id,
            "share_code": share_code,
            "qrcode_url": qrcode_url,
            "date_time": new_session.date_time,
            "duration_minutes": duration_minutes,
            "room": room,
            "is_active": True,
            "students_enrolled": len(attendance_records),
            "attendance_records": attendance_records,
            "message": f"Session created. {len(attendance_records)} attendance records created."
        }
    
    def close_session(self, session_id: int, teacher_id: int) -> Dict[str, Any]:
        """Close session by delegating to SessionController"""
        return self.session_ctrl.close_session(session_id, teacher_id)
    
    def get_my_modules(self, teacher_id: int) -> List[Dict[str, Any]]:
        """Get all modules assigned to teacher"""
        teacher = self.session.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teacher with ID {teacher_id} not found"
            )
        
        teacher_modules = self.session.exec(
            select(TeacherModules).where(TeacherModules.teacher_id == teacher_id)
        ).all()
        
        modules = []
        for tm in teacher_modules:
            module = self.session.get(Module, tm.module_id)
            if module:
                # Count enrolled students
                enrollments = self.session.exec(
                    select(Enrollment).where(
                        Enrollment.module_id == module.id,
                        Enrollment.is_excluded == False
                    )
                ).all()
                
                modules.append({
                    "teacher_module_id": tm.id,
                    "module_id": module.id,
                    "module_name": module.name,
                    "module_code": module.code,
                    "specialty_id": module.specialty_id,
                    "enrolled_students": len(enrollments)
                })
        
        return modules
    
    def get_my_sessions(self, teacher_id: int) -> List[Dict[str, Any]]:
        """Get all sessions created by teacher"""
        teacher_modules = self.session.exec(
            select(TeacherModules).where(TeacherModules.teacher_id == teacher_id)
        ).all()
        
        sessions = []
        for tm in teacher_modules:
            module = self.session.get(Module, tm.module_id)
            tm_sessions = self.session.exec(
                select(ClassSession).where(ClassSession.teacher_module_id == tm.id)
            ).all()
            
            for sess in tm_sessions:
                # Get attendance stats
                records = self.session.exec(
                    select(AttendanceRecord).where(AttendanceRecord.session_id == sess.id)
                ).all()
                present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
                
                sessions.append({
                    "session_id": sess.id,
                    "module_name": module.name if module else "Unknown",
                    "share_code": sess.session_code,
                    "qrcode_url": sess.session_qrcode,
                    "date_time": sess.date_time,
                    "duration_minutes": sess.duration_minutes,
                    "room": sess.room,
                    "is_active": sess.is_active,
                    "total_students": len(records),
                    "present": present
                })
        
        return sessions
    
    def validate_attendance_records(self, session_id: int) -> Dict[str, Any]:
        """Get detailed attendance for a session"""
        session_obj = self.session.get(ClassSession, session_id)
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session with ID {session_id} not found"
            )
        
        records = self.session.exec(
            select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)
        ).all()
        
        students = []
        for record in records:
            enrollment = self.session.get(Enrollment, record.enrollement_id)
            if enrollment and enrollment.student:
                student = enrollment.student
                user = student.user if student else None
                students.append({
                    "attendance_id": record.id,
                    "student_id": student.id,
                    "student_name": user.full_name if user else "Unknown",
                    "status": record.status.value,
                    "marked_at": record.created_at
                })
        
        present = sum(1 for s in students if s["status"] == "PRESENT")
        absent = sum(1 for s in students if s["status"] == "ABSENT")
        
        return {
            "session_id": session_id,
            "share_code": session_obj.session_code,
            "qrcode_url": session_obj.session_qrcode,
            "room": session_obj.room,
            "is_active": session_obj.is_active,
            "date_time": session_obj.date_time,
            "statistics": {
                "total": len(students),
                "present": present,
                "absent": absent,
                "rate": round((present / len(students) * 100), 2) if students else 0
            },
            "students": students
        }
        

