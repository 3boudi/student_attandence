from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from models.attendance import AttendanceRecord
from models.session import Session as ClassSession
from models.student import Student
from models.enums import AttendanceStatus
from schema.attendance import AttendanceRecordCreate, AttendanceRecordUpdate
from .base_controller import BaseController

class AttendanceController(BaseController[AttendanceRecord, AttendanceRecordCreate, AttendanceRecordUpdate]):
    def __init__(self):
        super().__init__(AttendanceRecord)
    
    def mark_attendance_bulk(self, db: Session, session_id: str,
                            student_ids: List[str],
                            status: AttendanceStatus = AttendanceStatus.PRESENT) -> List[AttendanceRecord]:
        """Mark attendance for multiple students"""
        # Check if session exists and is active
        session = db.get(ClassSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not active"
            )
        
        # Check if session is still valid
        session_end = session.datetime + timedelta(minutes=session.duration_minutes)
        if datetime.utcnow() > session_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session has ended"
            )
        
        attendance_records = []
        
        for student_id in student_ids:
            # Check if student exists
            student = db.get(Student, student_id)
            if not student:
                continue  # Skip non-existent students
            
            # Check if attendance already exists
            existing = db.exec(
                select(AttendanceRecord).where(
                    AttendanceRecord.session_id == session_id,
                    AttendanceRecord.student_id == student_id
                )
            ).first()
            
            if existing:
                # Update existing record
                existing.status = status
                existing.timestamp = datetime.utcnow()
                db.add(existing)
                attendance_records.append(existing)
            else:
                # Create new record
                attendance = AttendanceRecord(
                    session_id=session_id,
                    student_id=student_id,
                    status=status,
                    timestamp=datetime.utcnow()
                )
                db.add(attendance)
                attendance_records.append(attendance)
        
        db.commit()
        
        # Refresh all records
        for record in attendance_records:
            db.refresh(record)
        
        return attendance_records
    
    def get_attendance_by_student_and_session(self, db: Session,
                                            student_id: str,
                                            session_id: str) -> Optional[AttendanceRecord]:
        """Get attendance record for specific student and session"""
        query = select(AttendanceRecord).where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.session_id == session_id
        )
        attendance = db.exec(query).first()
        return attendance
    
    def update_attendance_status(self, db: Session, attendance_id: str,
                                status: AttendanceStatus) -> AttendanceRecord:
        """Update attendance status"""
        attendance = self.get(db, attendance_id)
        attendance.status = status
        attendance.timestamp = datetime.utcnow()
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance
    
    def get_attendance_summary(self, db: Session,
                              student_id: Optional[str] = None,
                              module_id: Optional[str] = None,
                              specialty_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get attendance summary with filters"""
        query = select(AttendanceRecord)
        
        # Apply filters through joins
        if student_id or module_id or specialty_id or start_date or end_date:
            query = query.join(ClassSession)
            
            if student_id:
                query = query.where(AttendanceRecord.student_id == student_id)
            if module_id:
                query = query.where(ClassSession.module_id == module_id)
            if specialty_id:
                query = query.join(Module).where(Module.specialty_id == specialty_id)
            if start_date:
                query = query.where(ClassSession.datetime >= start_date)
            if end_date:
                query = query.where(ClassSession.datetime <= end_date)
        
        attendance_records = db.exec(query).all()
        
        # Calculate statistics
        total = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status == AttendanceStatus.PRESENT)
        absent = sum(1 for r in attendance_records if r.status == AttendanceStatus.ABSENT)
        excluded = sum(1 for r in attendance_records if r.status == AttendanceStatus.EXCLUDED)
        
        return {
            "total_records": total,
            "present": present,
            "absent": absent,
            "excluded": excluded,
            "attendance_rate": round((present / total * 100), 2) if total > 0 else 0
        }
    
    def export_attendance_data(self, db: Session,
                              filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Export attendance data for reporting"""
        query = select(AttendanceRecord)
        
        # Apply filters
        if filters:
            query = query.join(ClassSession)
            
            for key, value in filters.items():
                if value is not None:
                    if key == "student_id":
                        query = query.where(AttendanceRecord.student_id == value)
                    elif key == "session_id":
                        query = query.where(AttendanceRecord.session_id == value)
                    elif key == "module_id":
                        query = query.where(ClassSession.module_id == value)
                    elif key == "start_date":
                        query = query.where(ClassSession.datetime >= value)
                    elif key == "end_date":
                        query = query.where(ClassSession.datetime <= value)
        
        # Join with student and session for complete data
        query = query.join(Student).join(ClassSession)
        
        attendance_records = db.exec(query).all()
        
        # Format data for export
        export_data = []
        for record in attendance_records:
            export_data.append({
                "id": record.id,
                "student_name": record.student.user.full_name if record.student and record.student.user else "Unknown",
                "student_email": record.student.user.email if record.student and record.student.user else "Unknown",
                "session_code": record.session.session_code if record.session else "Unknown",
                "module_name": record.session.module.module_name if record.session and record.session.module else "Unknown",
                "date": record.session.datetime.isoformat() if record.session else "Unknown",
                "status": record.status,
                "timestamp": record.timestamp.isoformat(),
                "justification": record.justification.comment if record.justification else None,
                "justification_status": record.justification.status if record.justification else None
            })
        
        return export_data

attendance_controller = AttendanceController()