"""
Member controller handling all member-related business logic.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException

from app.controllers.base_controller import BaseController
from app.models.models import Member, Borrowing
from app.schemas.schemas import MemberCreate, MemberUpdate
from app.core.logging import log_business_event, log_error, log_critical


class MemberController(BaseController[Member]):
    """
    Controller for member-related operations.
    """
    
    def __init__(self):
        """Initialize member controller."""
        super().__init__(Member)
    
    def create_member(
        self,
        db: Session,
        member_data: MemberCreate,
        user_id: int
    ) -> Member:
        """
        Create a new library member.
        
        Args:
            db: Database session
            member_data: Member creation data
            user_id: ID of the user creating the member
            
        Returns:
            Created member instance
            
        Raises:
            HTTPException: If email already exists or database error occurs
        """
        try:
            self.logger.info(f"Creating member: {member_data.email}")
            
            # Check if email already exists
            if self.exists_by_field(db, "email", member_data.email):
                log_error(
                    self.logger,
                    "Member creation failed: Email already exists",
                    email=member_data.email,
                    user_id=user_id
                )
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            
            # Create member
            db_member = self.create(db, member_data.model_dump())
            
            log_business_event(
                self.logger,
                "member_created",
                member_id=db_member.id,
                member_email=db_member.email,
                created_by=user_id
            )
            
            return db_member
            
        except HTTPException:
            raise
        except IntegrityError as e:
            db.rollback()
            log_error(
                self.logger,
                "Database integrity error while creating member",
                exception=e,
                email=member_data.email
            )
            raise HTTPException(
                status_code=400,
                detail="Database constraint violation"
            )
        except SQLAlchemyError as e:
            db.rollback()
            log_critical(
                self.logger,
                "Critical database error while creating member",
                exception=e,
                email=member_data.email,
                user_id=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        except Exception as e:
            db.rollback()
            log_critical(
                self.logger,
                "Unexpected error while creating member",
                exception=e,
                email=member_data.email,
                user_id=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    def get_members(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Member]:
        """
        Get all library members with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of member instances
            
        Raises:
            HTTPException: If database error occurs
        """
        try:
            self.logger.info(f"Listing members: skip={skip}, limit={limit}")
            return self.get_all(db, skip=skip, limit=limit)
        except SQLAlchemyError as e:
            log_critical(
                self.logger,
                "Critical database error while listing members",
                exception=e,
                skip=skip,
                limit=limit
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        except Exception as e:
            log_critical(
                self.logger,
                "Unexpected error while listing members",
                exception=e,
                skip=skip,
                limit=limit
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    def get_member_by_id(
        self,
        db: Session,
        member_id: int
    ) -> Member:
        """
        Get a specific member by ID.
        
        Args:
            db: Database session
            member_id: Member ID
            
        Returns:
            Member instance
            
        Raises:
            HTTPException: If member not found or database error occurs
        """
        try:
            self.logger.info(f"Getting member: {member_id}")
            return self.get_by_id(db, member_id)
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            log_error(
                self.logger,
                "Database error while getting member",
                exception=e,
                member_id=member_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        except Exception as e:
            log_critical(
                self.logger,
                "Unexpected error while getting member",
                exception=e,
                member_id=member_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    def update_member(
        self,
        db: Session,
        member_id: int,
        member_update: MemberUpdate,
        user_id: int
    ) -> Member:
        """
        Update member information.
        
        Args:
            db: Database session
            member_id: Member ID to update
            member_update: Update data
            user_id: ID of the user performing the update
            
        Returns:
            Updated member instance
            
        Raises:
            HTTPException: If member not found, email already in use, or database error occurs
        """
        try:
            self.logger.info(f"Updating member: {member_id}")
            
            # Get existing member
            db_member = self.get_by_id(db, member_id)
            
            # Check email uniqueness if email is being updated
            if member_update.email and member_update.email != db_member.email:
                if self.exists_by_field(
                    db,
                    "email",
                    member_update.email,
                    exclude_id=member_id
                ):
                    log_error(
                        self.logger,
                        "Email already in use",
                        member_id=member_id,
                        email=member_update.email,
                        user_id=user_id
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Email already in use"
                    )
            
            # Update member
            update_data = member_update.model_dump(exclude_unset=True)
            db_member = self.update(db, db_member, update_data)
            
            log_business_event(
                self.logger,
                "member_updated",
                member_id=member_id,
                fields_updated=list(update_data.keys()),
                updated_by=user_id
            )
            
            return db_member
            
        except HTTPException:
            raise
        except IntegrityError as e:
            db.rollback()
            log_error(
                self.logger,
                "Database integrity error while updating member",
                exception=e,
                member_id=member_id
            )
            raise HTTPException(
                status_code=400,
                detail="Database constraint violation"
            )
        except SQLAlchemyError as e:
            db.rollback()
            log_critical(
                self.logger,
                "Critical database error while updating member",
                exception=e,
                member_id=member_id,
                user_id=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        except Exception as e:
            db.rollback()
            log_critical(
                self.logger,
                "Unexpected error while updating member",
                exception=e,
                member_id=member_id,
                user_id=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
    
    def delete_member(
        self,
        db: Session,
        member_id: int,
        user_id: int
    ) -> None:
        """
        Delete a member (soft delete).
        
        Args:
            db: Database session
            member_id: Member ID to delete
            user_id: ID of the user performing the deletion
            
        Raises:
            HTTPException: If member not found, has active borrowings, or database error occurs
        """
        try:
            self.logger.info(f"Deleting member: {member_id}")
            
            # Get existing member
            db_member = self.get_by_id(db, member_id)
            
            # Check for active borrowings
            active_borrowings = db.query(Borrowing).filter(
                Borrowing.member_id == member_id,
                Borrowing.status == 'BORROWED'
            ).count()
            
            if active_borrowings > 0:
                log_error(
                    self.logger,
                    "Cannot delete member with active borrowings",
                    member_id=member_id,
                    active_borrowings=active_borrowings,
                    user_id=user_id
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete member. Member has {active_borrowings} active borrowing(s). Please return all borrowed books first."
                )
            
            # Soft delete
            self.delete(db, db_member, soft_delete=True)
            
            log_business_event(
                self.logger,
                "member_deleted",
                member_id=member_id,
                deleted_by=user_id
            )
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            log_critical(
                self.logger,
                "Critical database error while deleting member",
                exception=e,
                member_id=member_id,
                user_id=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        except Exception as e:
            db.rollback()
            log_critical(
                self.logger,
                "Unexpected error while deleting member",
                exception=e,
                member_id=member_id,
                user_id=user_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )


# Singleton instance
member_controller = MemberController()
