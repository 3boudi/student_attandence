from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from ..models.session import Session as ClassSession
from ..models.attendance import AttendanceRecord
from ..models.module import Module
from ..models.teacher import Teacher
from ..schema.session import SessionCreate, SessionUpdate
from .base_controller import BaseController

class SessionController(BaseController[ClassSession, SessionCreate, SessionUpdate]):
    def __init__(self):
        super().__init__(ClassSession)
    
    def get_active_sessions(self, db: Session) -> List[ClassSession]:
        """Get all active sessions"""
        query = select(ClassSession).where(
            ClassSession.is_active == True,
            ClassSession.datetime <= datetime.utcnow(),
            ClassSession.datetime + timedelta(minutes=ClassSession.duration_minutes) >= datetime.utcnow()
        )
        sessions = db.exec(query).all()
        return sessions
    
    def get_session_with_details(self, db: Session, session_id: int) -> Optional[ClassSession]:
        """Get session with module, teacher, and attendance details"""
        session = db.get(ClassSession, session_id)
        if session:
            # Eager load related data
            session.module = db.get(Module, session.module_id)
            session.teacher = db.get(Teacher, session.teacher_id)
            
            # Get attendance records
            attendance_query = select(AttendanceRecord).where(
                AttendanceRecord.session_id == session_id
            )
            session.attendance_records = db.exec(attendance_query).all()
        
        return session
    
    def get_sessions_by_module(self, db: Session, module_id: int, 
                              active_only: bool = False) -> List[ClassSession]:
        """Get all sessions for a module"""
        query = select(ClassSession).where(ClassSession.module_id == module_id)
        
        if active_only:
            query = query.where(ClassSession.is_active == True)
        
        query = query.order_by(ClassSession.datetime.desc())
        sessions = db.exec(query).all()
        return sessions
    
    def get_sessions_by_teacher(self, db: Session, teacher_id: int,
                               start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> List[ClassSession]:
        """Get sessions by teacher with date range"""
        query = select(ClassSession).where(ClassSession.teacher_id == teacher_id)
        
        if start_date:
            query = query.where(ClassSession.datetime >= start_date)
        if end_date:
            query = query.where(ClassSession.datetime <= end_date)
        
        query = query.order_by(ClassSession.datetime.desc())
        sessions = db.exec(query).all()
        return sessions
    
    def get_todays_sessions(self, db: Session, teacher_id: Optional[int] = None) -> List[ClassSession]:
        """Get today's sessions"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        query = select(ClassSession).where(
            ClassSession.datetime >= today_start,
            ClassSession.datetime < today_end
        )
        
        if teacher_id:
            query = query.where(ClassSession.teacher_id == teacher_id)
        
        query = query.order_by(ClassSession.datetime.asc())
        sessions = db.exec(query).all()
        return sessions
    
    def close_expired_sessions(self, db: Session) -> List[ClassSession]:
        """Close sessions that have passed their end time"""
        sessions = self.get_active_sessions(db)
        expired_sessions = []
        
        for session in sessions:
            session_end = session.datetime + timedelta(minutes=session.duration_minutes)
            if datetime.utcnow() > session_end:
                session.is_active = False
                db.add(session)
                expired_sessions.append(session)
        
        if expired_sessions:
            db.commit()
        
        return expired_sessions
    
    def get_session_attendance_summary(self, db: Session, session_id: int) -> Dict[str, Any]:
        """Get attendance summary for a session"""
        from ..models.enums import AttendanceStatus
        
        session = self.get(db, session_id)
        
        # Get attendance records
        attendance_records = db.exec(
            select(AttendanceRecord).where(AttendanceRecord.session_id == session_id)
        ).all()
        
        total_students = len(attendance_records)
        present = sum(1 for r in attendance_records if r.status == AttendanceStatus.PRESENT)
        absent = sum(1 for r in attendance_records if r.status == AttendanceStatus.ABSENT)
        excluded = sum(1 for r in attendance_records if r.status == AttendanceStatus.EXCLUDED)
        
        return {
            "session": session,
            "total_students": total_students,
            "present": present,
            "absent": absent,
            "excluded": excluded,
            "attendance_rate": round((present / total_students * 100), 2) if total_students > 0 else 0
        }

session_controller = SessionController()