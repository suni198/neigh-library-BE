"""
Member controller handling all member-related business logic.
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.controllers.base_controller import BaseController
from app.models.models import Member, Borrowing
from app.schemas.schemas import MemberCreate, MemberUpdate
from app.core.logging import log_business_event, log_error


class MemberController(BaseController[Member]):

    def __init__(self):
        super().__init__(Member)

    def create_member(self, db: Session, member_data: MemberCreate, user_id: int) -> Member:
        """Create a new library member."""
        with self._handle_db_errors(db, "create_member"):
            self.logger.info(f"Creating member: {member_data.email}")
            if self.exists_by_field(db, "email", member_data.email):
                log_error(self.logger, "Member creation failed: Email already exists",
                          email=member_data.email, user_id=user_id)
                raise HTTPException(status_code=400, detail="Email already registered")
            db_member = self.create(db, member_data.model_dump())
            log_business_event(self.logger, "member_created",
                               member_id=db_member.id, member_email=db_member.email,
                               created_by=user_id)
            return db_member

    def get_members(self, db: Session, skip: int = 0, limit: int = 100) -> List[Member]:
        """Get all library members with pagination."""
        with self._handle_db_errors(db, "get_members"):
            self.logger.info(f"Listing members: skip={skip}, limit={limit}")
            return self.get_all(db, skip=skip, limit=limit)

    def get_member_by_id(self, db: Session, member_id: int) -> Member:
        """Get a specific member by ID."""
        with self._handle_db_errors(db, "get_member_by_id"):
            self.logger.info(f"Getting member: {member_id}")
            return self.get_by_id(db, member_id)

    def update_member(
        self, db: Session, member_id: int, member_update: MemberUpdate, user_id: int
    ) -> Member:
        """Update member information."""
        with self._handle_db_errors(db, "update_member"):
            self.logger.info(f"Updating member: {member_id}")
            db_member = self.get_by_id(db, member_id)
            if member_update.email and member_update.email != db_member.email:
                if self.exists_by_field(db, "email", member_update.email, exclude_id=member_id):
                    log_error(self.logger, "Email already in use",
                              member_id=member_id, email=member_update.email, user_id=user_id)
                    raise HTTPException(status_code=400, detail="Email already in use")
            update_data = member_update.model_dump(exclude_unset=True)
            db_member = self.update(db, db_member, update_data)
            log_business_event(self.logger, "member_updated",
                               member_id=member_id, fields_updated=list(update_data.keys()),
                               updated_by=user_id)
            return db_member

    def delete_member(self, db: Session, member_id: int, user_id: int) -> None:
        """Soft-delete a member; blocked if active borrowings exist."""
        with self._handle_db_errors(db, "delete_member"):
            self.logger.info(f"Deleting member: {member_id}")
            db_member = self.get_by_id(db, member_id)
            active_borrowings = db.query(Borrowing).filter(
                Borrowing.member_id == member_id,
                Borrowing.status == 'BORROWED'
            ).count()
            if active_borrowings > 0:
                log_error(self.logger, "Cannot delete member with active borrowings",
                          member_id=member_id, active_borrowings=active_borrowings,
                          user_id=user_id)
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete member. Member has {active_borrowings} active borrowing(s). "
                           "Please return all borrowed books first."
                )
            self.delete(db, db_member, soft_delete=True)
            log_business_event(self.logger, "member_deleted",
                               member_id=member_id, deleted_by=user_id)


member_controller = MemberController()
