from sqlmodel import Session, select
from typing import List
from fastapi import HTTPException, status

from ..models.specialty import Specialty
from ..models.module import Module
from ..models.student import Student
from ..models.user import User


class SpecialtyController:
    """
    Specialty Controller - Handles specialty-related operations
    
    Methods:
        - get_modules_of_specialty(): Get all modules for a specialty
        - get_students_of_specialty(): Get all students in a specialty
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_modules_of_specialty(self, specialty_id: int) -> List[dict]:
        """
        Get all modules associated with a specialty.
        
        Args:
            specialty_id: ID of the specialty
            
        Returns:
            List[dict]: List of modules with their details
        """
        specialty = self.session.get(Specialty, specialty_id)
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specialty with ID {specialty_id} not found"
            )
        
        modules = self.session.exec(
            select(Module).where(Module.specialty_id == specialty_id)
        ).all()
        
        return [
            {
                "id": module.id,
                "name": module.name,
                "code": module.code,
                "room": module.room,
                "specialty_id": module.specialty_id
            }
            for module in modules
        ]
    
    def get_students_of_specialty(self, specialty_id: int) -> List[dict]:
        """
        Get all students associated with a specialty.
        
        Args:
            specialty_id: ID of the specialty
            
        Returns:
            List[dict]: List of students with their details
        """
        specialty = self.session.get(Specialty, specialty_id)
        if not specialty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Specialty with ID {specialty_id} not found"
            )
        
        students = self.session.exec(
            select(Student).where(Student.specialty_id == specialty_id)
        ).all()
        
        result = []
        for student in students:
            user = self.session.get(User, student.user_id)
            result.append({
                "id": student.id,
                "user_id": student.user_id,
                "full_name": user.full_name if user else None,
                "email": user.email if user else None,
                "department": user.department if user else None,
                "specialty_id": student.specialty_id
            })
        
        return result
    
    def create_specialty(self, name: str, year_level: str) -> Specialty:
        """
        Create a new specialty.
        
        Args:
            name: Specialty name
            year_level: Year level (e.g., "1st Year", "2nd Year")
            
        Returns:
            Specialty: The created specialty
        """
        specialty = Specialty(
            name=name,
            year_level=year_level
        )
        self.session.add(specialty)
        self.session.commit()
        self.session.refresh(specialty)
        
        return specialty
    
    def get_all_specialties(self) -> List[dict]:
        """
        Get all specialties.
        
        Returns:
            List[dict]: List of all specialties
        """
        specialties = self.session.exec(select(Specialty)).all()
        
        return [
            {
                "id": specialty.id,
                "name": specialty.name,
                "year_level": specialty.year_level,
                "created_at": specialty.created_at
            }
            for specialty in specialties
        ]
