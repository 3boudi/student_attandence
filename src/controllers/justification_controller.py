from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
from datetime import datetime

from ..models.justification import Justification
from ..models.enums import JustificationStatus
from ..schema.justification import JustificationCreate, JustificationUpdate
from .base_controller import BaseController

class JustificationController(BaseController[Justification, JustificationCreate, JustificationUpdate]):
    def __init__(self):
        super().__init__(Justification)
    
    def get_pending_justifications(self, db: Session) -> List[Justification]:
        """Get all pending justifications"""
        query = select(Justification).where(
            Justification.status == JustificationStatus.PENDING
        ).order_by(Justification.created_at.desc())
        
        justifications = db.exec(query).all()
        return justifications
    
    def get_justifications_by_student(self, db: Session, student_id: int,
                                     status: Optional[JustificationStatus] = None) -> List[Justification]:
        """Get justifications for a specific student"""
        query = select(Justification).where(
            Justification.student_id == student_id
        )
        
        if status:
            query = query.where(Justification.status == status)
        
        query = query.order_by(Justification.created_at.desc())
        justifications = db.exec(query).all()
        return justifications
    
    def get_justifications_by_status(self, db: Session, status: JustificationStatus) -> List[Justification]:
        """Get justifications by status"""
        query = select(Justification).where(
            Justification.status == status
        ).order_by(Justification.created_at.desc())
        
        justifications = db.exec(query).all()
        return justifications
    
    def approve_justification(self, db: Session, justification_id: int,
                             validator_id: int) -> Justification:
        """Approve a justification"""
        justification = self.get(db, justification_id)
        
        if justification.status != JustificationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Justification is not pending"
            )
        
        justification.status = JustificationStatus.APPROVED
        justification.validator_id = validator_id
        justification.validation_date = datetime.utcnow()
        
        # Update associated attendance record status
        from ..models.attendance import AttendanceRecord
        from ..models.enums import AttendanceStatus
        
        attendance = db.get(AttendanceRecord, justification.attendance_record_id)
        if attendance:
            attendance.status = AttendanceStatus.EXCLUDED
            db.add(attendance)
        
        db.add(justification)
        db.commit()
        db.refresh(justification)
        return justification
    
    def reject_justification(self, db: Session, justification_id: int,
                            validator_id: int, reason: str) -> Justification:
        """Reject a justification"""
        justification = self.get(db, justification_id)
        
        if justification.status != JustificationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Justification is not pending"
            )
        
        justification.status = JustificationStatus.REJECTED
        justification.validator_id = validator_id
        justification.validation_date = datetime.utcnow()
        justification.rejection_reason = reason
        
        db.add(justification)
        db.commit()
        db.refresh(justification)
        return justification
    
    def get_justification_statistics(self, db: Session) -> Dict[str, Any]:
        """Get justification statistics"""
        total = db.exec(select(Justification)).count()
        pending = db.exec(
            select(Justification).where(Justification.status == JustificationStatus.PENDING)
        ).count()
        approved = db.exec(
            select(Justification).where(Justification.status == JustificationStatus.APPROVED)
        ).count()
        rejected = db.exec(
            select(Justification).where(Justification.status == JustificationStatus.REJECTED)
        ).count()
        
        approval_rate = (approved / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": round(approval_rate, 2),
            "pending_percentage": round((pending / total * 100), 2) if total > 0 else 0
        }

justification_controller = JustificationController()