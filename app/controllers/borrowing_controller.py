"""
Borrowing controller handling all borrowing-related business logic.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from app.controllers.base_controller import BaseController
from app.controllers.book_controller import book_controller
from app.models.models import Borrowing, Book, Member
from app.schemas.schemas import BorrowingCreate, BorrowingReturn
from app.core.logging import log_business_event, log_error


class BorrowingController(BaseController[Borrowing]):
    """
    Controller for borrowing operations including borrow and return logic.
    """
    
    def __init__(self):
        """Initialize borrowing controller."""
        super().__init__(Borrowing)
    
    def borrow_book(
        self,
        db: Session,
        borrowing_data: BorrowingCreate,
        user_id: int
    ) -> Borrowing:
        """
        Record a book being borrowed by a member.
        
        Args:
            db: Database session
            borrowing_data: Borrowing creation data
            user_id: ID of the user processing the transaction
            
        Returns:
            Created borrowing instance
            
        Raises:
            HTTPException: If member/book not found, book unavailable,
                          or member already has the book borrowed
        """
        self.logger.info(
            f"Borrow book request",
            extra={
                "member_id": borrowing_data.member_id,
                "book_id": borrowing_data.book_id
            }
        )
        
        # Verify member exists and is active
        member = db.query(Member).filter(
            Member.id == borrowing_data.member_id,
            Member.is_active == True
        ).first()
        
        if not member:
            log_error(
                self.logger,
                "Active member not found",
                member_id=borrowing_data.member_id
            )
            raise HTTPException(
                status_code=404,
                detail="Active member not found"
            )
        
        # Verify book exists and is active
        book = db.query(Book).filter(
            Book.id == borrowing_data.book_id,
            Book.is_active == True
        ).first()
        
        if not book:
            log_error(
                self.logger,
                "Active book not found",
                book_id=borrowing_data.book_id,
                member_id=borrowing_data.member_id
            )
            raise HTTPException(
                status_code=404,
                detail="Active book not found"
            )
        
        # Check availability
        if book.available_copies <= 0:
            log_error(
                self.logger,
                "No copies available",
                member_id=borrowing_data.member_id,
                book_id=borrowing_data.book_id,
                book_title=book.title
            )
            raise HTTPException(
                status_code=400,
                detail="No copies of this book are currently available"
            )
        
        # Check if member already has this book borrowed
        active_borrowing = db.query(Borrowing).filter(
            Borrowing.member_id == borrowing_data.member_id,
            Borrowing.book_id == borrowing_data.book_id,
            Borrowing.status == 'BORROWED'
        ).first()
        
        if active_borrowing:
            log_error(
                self.logger,
                "Member already has this book borrowed",
                member_id=borrowing_data.member_id,
                book_id=borrowing_data.book_id
            )
            raise HTTPException(
                status_code=400,
                detail="Member already has this book borrowed"
            )
        
        # Decrease book availability
        book_controller.decrease_availability(db, book)
        
        # Create borrowing record
        borrowing_dict = borrowing_data.model_dump()
        borrowing_dict['status'] = 'BORROWED'
        db_borrowing = self.create(db, borrowing_dict)
        
        log_business_event(
            self.logger,
            "book_borrowed",
            borrowing_id=db_borrowing.id,
            member_id=borrowing_data.member_id,
            book_id=borrowing_data.book_id,
            book_title=book.title,
            member_name=f"{member.first_name} {member.last_name}",
            due_date=borrowing_data.due_date.isoformat()
        )
        
        return db_borrowing
    
    def return_book(
        self,
        db: Session,
        borrowing_id: int,
        return_data: BorrowingReturn,
        user_id: int
    ) -> Borrowing:
        """
        Record a borrowed book being returned.
        
        Args:
            db: Database session
            borrowing_id: Borrowing record ID
            return_data: Return data including fine and notes
            user_id: ID of the user processing the return
            
        Returns:
            Updated borrowing instance
            
        Raises:
            HTTPException: If borrowing not found or book not currently borrowed
        """
        self.logger.info(
            f"Return book request",
            extra={"borrowing_id": borrowing_id}
        )
        
        # Get borrowing record
        db_borrowing = self.get_by_id(db, borrowing_id)
        
        # Verify book is currently borrowed
        if db_borrowing.status != 'BORROWED':
            log_error(
                self.logger,
                "Book is not currently borrowed",
                borrowing_id=borrowing_id,
                member_id=db_borrowing.member_id,
                current_status=db_borrowing.status
            )
            raise HTTPException(
                status_code=400,
                detail="Book is not currently borrowed"
            )
        
        # Get book to update availability
        book = db.query(Book).filter(Book.id == db_borrowing.book_id).first()
        
        # Increase book availability
        book_controller.increase_availability(db, book)
        
        # Update borrowing record
        update_dict = {
            'return_date': datetime.now(),
            'status': 'RETURNED',
            'fine_amount': return_data.fine_amount
        }
        
        if return_data.notes:
            update_dict['notes'] = return_data.notes
        
        db_borrowing = self.update(db, db_borrowing, update_dict)
        
        borrowed_days = (datetime.now() - db_borrowing.borrowed_date).days
        
        log_business_event(
            self.logger,
            "book_returned",
            borrowing_id=borrowing_id,
            member_id=db_borrowing.member_id,
            book_id=db_borrowing.book_id,
            book_title=book.title,
            fine_amount=float(return_data.fine_amount),
            borrowed_days=borrowed_days
        )
        
        return db_borrowing
    
    def get_borrowings(
        self,
        db: Session,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Borrowing]:
        """
        Get all borrowing records with optional status filter.
        
        Args:
            db: Database session
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of borrowing instances
            
        Raises:
            HTTPException: If invalid status provided
        """
        self.logger.info(
            f"Listing borrowings: status={status}, skip={skip}, limit={limit}"
        )
        
        if status:
            valid_statuses = ['BORROWED', 'RETURNED', 'OVERDUE', 'LOST']
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid status"
                )
            
            return self.get_all(db, skip=skip, limit=limit, filters={'status': status})
        
        return self.get_all(db, skip=skip, limit=limit)
    
    def get_member_borrowings(
        self,
        db: Session,
        member_id: int
    ) -> List[Borrowing]:
        """
        Get all borrowings for a specific member.
        
        Args:
            db: Database session
            member_id: Member ID
            
        Returns:
            List of borrowing instances
            
        Raises:
            HTTPException: If member not found
        """
        self.logger.info(f"Getting borrowings for member: {member_id}")
        
        # Verify member exists
        member = db.query(Member).filter(Member.id == member_id).first()
        if not member:
            log_error(self.logger, "Member not found", member_id=member_id)
            raise HTTPException(
                status_code=404,
                detail="Member not found"
            )
        
        borrowings = db.query(Borrowing).filter(
            Borrowing.member_id == member_id
        ).all()
        
        self.logger.info(
            f"Found {len(borrowings)} borrowings for member {member_id}"
        )
        
        return borrowings
    
    def get_book_borrowings(
        self,
        db: Session,
        book_id: int
    ) -> List[Borrowing]:
        """
        Get borrowing history for a specific book.
        
        Args:
            db: Database session
            book_id: Book ID
            
        Returns:
            List of borrowing instances
            
        Raises:
            HTTPException: If book not found
        """
        self.logger.info(f"Getting borrowings for book: {book_id}")
        
        # Verify book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            log_error(self.logger, "Book not found", book_id=book_id)
            raise HTTPException(
                status_code=404,
                detail="Book not found"
            )
        
        borrowings = db.query(Borrowing).filter(
            Borrowing.book_id == book_id
        ).all()
        
        self.logger.info(
            f"Found {len(borrowings)} borrowings for book {book_id}"
        )
        
        return borrowings
    
    def get_borrowing_by_id(
        self,
        db: Session,
        borrowing_id: int
    ) -> Borrowing:
        """
        Get a specific borrowing record.
        
        Args:
            db: Database session
            borrowing_id: Borrowing ID
            
        Returns:
            Borrowing instance
            
        Raises:
            HTTPException: If borrowing not found
        """
        self.logger.info(f"Getting borrowing: {borrowing_id}")
        return self.get_by_id(db, borrowing_id)


# Singleton instance
borrowing_controller = BorrowingController()
