from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlmodel import SQLModel, Session, select
from fastapi import HTTPException, status
import uuid

from ..schema import PaginationParams

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)

class BaseController(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base controller with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get a single item by ID"""
        item = db.get(self.model, id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} not found"
            )
        return item
    
    def get_multi(
        self, 
        db: Session, 
        pagination: PaginationParams = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get multiple items with pagination and filtering"""
        if pagination is None:
            pagination = PaginationParams()
        
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        total = db.exec(query).count()
        items = db.exec(
            query.offset(pagination.skip).limit(pagination.limit)
        ).all()
        
        return {
            "items": items,
            "total": total,
            "skip": pagination.skip,
            "limit": pagination.limit
        }
    
    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Create a new item"""
        # Convert Pydantic model to dict for SQLModel
        db_obj = self.model(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        id: int, 
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """Update an existing item"""
        db_obj = self.get(db, id)
        
        # Get update data, excluding unset values
        update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, id: int) -> ModelType:
        """Delete an item"""
        db_obj = self.get(db, id)
        db.delete(db_obj)
        db.commit()
        return db_obj
    
    def exists(self, db: Session, id: int) -> bool:
        """Check if an item exists"""
        return bool(db.get(self.model, id))