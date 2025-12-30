from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from sqlmodel import Session
import shutil
import os
from pathlib import Path

from ..core.database import get_session
from ..core.dependencies import get_current_user, get_current_profile, get_user_with_complete_profile
from controllers.user_controller import user_controller
from controllers.notification_controller import notification_controller
from schema.user import UserUpdate, UserResponse
from schema.notification import NotificationResponse
from models.user import User

router = APIRouter(prefix="/user", tags=["user"])

# Upload directory for user avatars
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/profile", response_model=dict)
async def view_personal_information(
    current_profile: dict = Depends(get_current_profile)
):
    """
    View Personal Information - UC1
    Returns user's personal profile information
    """
    try:
        return {
            "message": "Personal information retrieved successfully",
            "data": current_profile
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load personal information: {str(e)}"
        )

@router.put("/profile", response_model=dict)
async def update_personal_information(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update personal information
    """
    try:
        updated_user = user_controller.update(session, current_user.id, user_update)
        return {
            "message": "Personal information updated successfully",
            "data": updated_user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to update personal information: {str(e)}"
        )

@router.post("/upload-avatar")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Upload profile picture
    """
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG, JPG, and PNG images are allowed"
            )
        
        # Validate file size (max 5MB)
        file_size = 0
        for chunk in file.file:
            file_size += len(chunk)
            if file_size > 5 * 1024 * 1024:  # 5MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 5MB limit"
                )
        
        # Save file
        file_extension = file.filename.split(".")[-1]
        filename = f"{current_user.id}_avatar.{file_extension}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user with avatar URL
        avatar_url = f"/uploads/avatars/{filename}"
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": avatar_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to upload avatar: {str(e)}"
        )

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user notifications
    """
    notifications = notification_controller.get_user_notifications(
        session, current_user.id, unread_only, limit
    )
    return notifications

@router.get("/notifications/unread-count")
async def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get count of unread notifications
    """
    count = notification_controller.get_unread_count(session, current_user.id)
    return {"unread_count": count}

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Mark notification as read
    """
    notification = notification_controller.mark_as_read(session, notification_id)
    return {
        "message": "Notification marked as read",
        "notification": notification
    }

@router.post("/notifications/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Mark all notifications as read
    """
    count = notification_controller.mark_all_as_read(session, current_user.id)
    return {
        "message": f"{count} notifications marked as read"
    }