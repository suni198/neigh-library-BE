"""
Base controller class with common functionality for all controllers.
"""

from contextlib import contextmanager
from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from app.db.database import Base
from app.core.logging import get_logger, log_db_operation, log_error

ModelType = TypeVar("ModelType", bound=Base)


class BaseController(Generic[ModelType]):
    """
    Base controller providing common CRUD operations and utilities.
    
    Attributes:
        model: SQLAlchemy model class
        logger: Logger instance for the controller
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize base controller with a model.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self.logger = get_logger(self.__class__.__name__)

    @contextmanager
    def _handle_db_errors(self, db: Session, operation: str):
        """Translate DB exceptions into HTTP responses.

        Replaces the repetitive try/except HTTPException/SQLAlchemyError/Exception
        pattern. Business-logic HTTPExceptions raised inside the block pass through
        unchanged; DB errors trigger a rollback and a clean 400/500 response.
        """
        try:
            yield
        except HTTPException:
            raise
        except IntegrityError as e:
            db.rollback()
            self.logger.error(
                f"Integrity error in {operation}",
                extra={"exception": str(e)},
                exc_info=True,
            )
            raise HTTPException(status_code=400, detail="Database constraint violation")
        except SQLAlchemyError as e:
            db.rollback()
            self.logger.error(
                f"Database error in {operation}",
                extra={"exception": str(e)},
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail="Internal server error")
        except Exception as e:
            db.rollback()
            self.logger.error(
                f"Unexpected error in {operation}",
                extra={"exception": str(e)},
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail="Internal server error")

    def get_by_id(
        self, 
        db: Session, 
        id: int, 
        raise_not_found: bool = True
    ) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            raise_not_found: Whether to raise HTTPException if not found
            
        Returns:
            Model instance or None
            
        Raises:
            HTTPException: If record not found and raise_not_found is True
        """
        instance = db.query(self.model).filter(self.model.id == id).first()
        
        if not instance and raise_not_found:
            log_error(
                self.logger,
                f"{self.model.__name__} not found",
                id=id
            )
            raise HTTPException(
                status_code=404, 
                detail=f"{self.model.__name__} not found"
            )
        
        if instance:
            log_db_operation(
                self.logger,
                "SELECT",
                self.model.__tablename__,
                id=id
            )
        
        return instance
    
    def get_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[ModelType]:
        """
        Get all records with pagination and optional filters.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Optional dictionary of filter conditions
            
        Returns:
            List of model instances
        """
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        instances = query.offset(skip).limit(limit).all()
        
        log_db_operation(
            self.logger,
            "SELECT",
            self.model.__tablename__,
            count=len(instances)
        )
        
        return instances
    
    def create(
        self,
        db: Session,
        obj_data: dict
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_data: Dictionary of object data
            
        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        log_db_operation(
            self.logger,
            "INSERT",
            self.model.__tablename__,
            id=db_obj.id
        )
        
        return db_obj
    
    def update(
        self,
        db: Session,
        db_obj: ModelType,
        update_data: dict
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            update_data: Dictionary of fields to update
            
        Returns:
            Updated model instance
        """
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.commit()
        db.refresh(db_obj)
        
        log_db_operation(
            self.logger,
            "UPDATE",
            self.model.__tablename__,
            id=db_obj.id
        )
        
        return db_obj
    
    def delete(
        self,
        db: Session,
        db_obj: ModelType,
        soft_delete: bool = True
    ) -> None:
        """
        Delete a record (soft or hard delete).
        
        Args:
            db: Database session
            db_obj: Model instance to delete
            soft_delete: If True, sets is_active=False; if False, removes from DB
        """
        if soft_delete and hasattr(db_obj, 'is_active'):
            db_obj.is_active = False
            db.commit()
            log_db_operation(
                self.logger,
                "UPDATE",
                self.model.__tablename__,
                id=db_obj.id,
                action="soft_delete"
            )
        else:
            db.delete(db_obj)
            db.commit()
            log_db_operation(
                self.logger,
                "DELETE",
                self.model.__tablename__,
                id=db_obj.id
            )
    
    def exists_by_field(
        self,
        db: Session,
        field_name: str,
        field_value: Any,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check if a record exists with a specific field value.
        
        Args:
            db: Database session
            field_name: Name of the field to check
            field_value: Value to check for
            exclude_id: Optional ID to exclude from the check
            
        Returns:
            True if record exists, False otherwise
        """
        query = db.query(self.model).filter(
            getattr(self.model, field_name) == field_value
        )
        
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)
        
        return query.first() is not None
