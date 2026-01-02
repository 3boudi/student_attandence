from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from ..models.notification import Notification
from ..models.enums import NotificationType
from ..schema.notification import NotificationCreate, NotificationUpdate
from .base_controller import BaseController

class NotificationController(BaseController[Notification, NotificationCreate, NotificationUpdate]):
    def __init__(self):
        super().__init__(Notification)
    
    def get_user_notifications(self, db: Session, user_id: int,
                              unread_only: bool = False,
                              limit: int = 50) -> List[Notification]:
        """Get notifications for a specific user"""
        query = select(Notification).where(
            Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        
        notifications = db.exec(query).all()
        return notifications
    
    def mark_as_read(self, db: Session, notification_id: int) -> Notification:
        """Mark a notification as read"""
        notification = self.get(db, notification_id)
        notification.is_read = True
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    def mark_all_as_read(self, db: Session, user_id: int) -> int:
        """Mark all user notifications as read"""
        notifications = self.get_user_notifications(db, user_id, unread_only=True)
        
        for notification in notifications:
            notification.is_read = True
            db.add(notification)
        
        db.commit()
        return len(notifications)
    
    def create_notification(self, db: Session, user_id: int,
                           title: str, message: str,
                           notification_type: NotificationType) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    def create_bulk_notifications(self, db: Session, user_ids: List[int],
                                 title: str, message: str,
                                 notification_type: NotificationType) -> List[Notification]:
        """Create notifications for multiple users"""
        notifications = []
        
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=notification_type
            )
            db.add(notification)
            notifications.append(notification)
        
        db.commit()
        
        # Refresh all notifications
        for notification in notifications:
            db.refresh(notification)
        
        return notifications
    
    def get_unread_count(self, db: Session, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        count = db.exec(query).count()
        return count
    
    def cleanup_old_notifications(self, db: Session, days_old: int = 30) -> int:
        """Clean up notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        query = select(Notification).where(
            Notification.created_at < cutoff_date,
            Notification.is_read == True
        )
        
        old_notifications = db.exec(query).all()
        
        for notification in old_notifications:
            db.delete(notification)
        
        db.commit()
        return len(old_notifications)
    
    def get_notification_statistics(self, db: Session, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get notification statistics"""
        query = select(Notification)
        
        if user_id:
            query = query.where(Notification.user_id == user_id)
        
        total = db.exec(query).count()
        
        unread_query = query.where(Notification.is_read == False)
        unread = db.exec(unread_query).count()
        
        # Count by type
        type_counts = {}
        for notification_type in NotificationType:
            type_query = query.where(Notification.type == notification_type)
            type_counts[notification_type.value] = db.exec(type_query).count()
        
        return {
            "total": total,
            "unread": unread,
            "read": total - unread,
            "unread_percentage": round((unread / total * 100), 2) if total > 0 else 0,
            "by_type": type_counts
        }

notification_controller = NotificationController()