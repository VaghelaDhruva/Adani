"""
PHASE 3 - CORE API ENDPOINTS: CRUD Service Layer

This service provides standardized CRUD operations for all core data entities
with proper validation, error handling, and pagination support.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from fastapi import HTTPException
from pydantic import BaseModel
import logging

from app.utils.exceptions import DataValidationError

logger = logging.getLogger(__name__)

# Generic types for CRUD operations
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic CRUD service with pagination and validation."""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    def get_by_id(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            raise DataValidationError(f"Failed to retrieve {self.model.__name__}")
    
    def get_multi(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get multiple records with pagination and filtering."""
        try:
            query = db.query(self.model)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        query = query.filter(getattr(self.model, field) == value)
            
            # Get total count before pagination
            total = query.count()
            
            # Apply ordering
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            # Apply pagination
            items = query.offset(skip).limit(limit).all()
            
            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": skip + limit < total,
                "has_prev": skip > 0
            }
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} list: {e}")
            raise DataValidationError(f"Failed to retrieve {self.model.__name__} list")
    
    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        try:
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__} with id: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise DataValidationError(f"Failed to create {self.model.__name__}: {str(e)}")
    
    def update(self, db: Session, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update an existing record."""
        try:
            obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__} with id: {getattr(db_obj, 'id', 'N/A')}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise DataValidationError(f"Failed to update {self.model.__name__}: {str(e)}")
    
    def delete(self, db: Session, id: Any) -> bool:
        """Delete a record by ID."""
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if not obj:
                return False
            
            db.delete(obj)
            db.commit()
            logger.info(f"Deleted {self.model.__name__} with id: {id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__} with id {id}: {e}")
            raise DataValidationError(f"Failed to delete {self.model.__name__}: {str(e)}")


class PlantCRUDService(CRUDService):
    """Specialized CRUD service for PlantMaster with plant_id as primary key."""
    
    def get_by_id(self, db: Session, plant_id: str):
        """Get plant by plant_id."""
        try:
            return db.query(self.model).filter(self.model.plant_id == plant_id).first()
        except Exception as e:
            logger.error(f"Error getting plant by plant_id {plant_id}: {e}")
            raise DataValidationError("Failed to retrieve plant")
    
    def delete(self, db: Session, plant_id: str) -> bool:
        """Delete plant by plant_id."""
        try:
            obj = db.query(self.model).filter(self.model.plant_id == plant_id).first()
            if not obj:
                return False
            
            db.delete(obj)
            db.commit()
            logger.info(f"Deleted plant with plant_id: {plant_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting plant with plant_id {plant_id}: {e}")
            raise DataValidationError(f"Failed to delete plant: {str(e)}")


def create_standardized_response(
    data: Any, 
    message: str = "Success", 
    status_code: int = 200,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized JSON response format."""
    response = {
        "status": "success" if status_code < 400 else "error",
        "message": message,
        "data": data,
        "status_code": status_code
    }
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def create_paginated_response(
    items: List[Any],
    total: int,
    skip: int,
    limit: int,
    has_next: bool,
    has_prev: bool,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create standardized paginated response format."""
    return {
        "status": "success",
        "message": message,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": has_next,
                "has_prev": has_prev,
                "current_page": (skip // limit) + 1 if limit > 0 else 1,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1
            }
        },
        "status_code": 200
    }