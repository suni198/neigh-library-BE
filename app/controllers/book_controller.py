"""
Book controller handling all book-related business logic.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.controllers.base_controller import BaseController
from app.models.models import Book
from app.schemas.schemas import BookCreate, BookUpdate
from app.core.logging import log_business_event, log_error


class BookController(BaseController[Book]):
    """
    Controller for book-related operations including availability management.
    """
    
    def __init__(self):
        """Initialize book controller."""
        super().__init__(Book)
    
    def create_book(
        self,
        db: Session,
        book_data: BookCreate
    ) -> Book:
        """
        Add a new book to the library.
        
        Args:
            db: Database session
            book_data: Book creation data
            
        Returns:
            Created book instance
            
        Raises:
            HTTPException: If ISBN already exists
        """
        self.logger.info(f"Creating book: {book_data.title}")
        
        # Check if ISBN already exists
        if book_data.isbn and self.exists_by_field(db, "isbn", book_data.isbn):
            log_error(
                self.logger,
                "Book creation failed: ISBN already exists",
                isbn=book_data.isbn
            )
            raise HTTPException(
                status_code=400,
                detail="Book with this ISBN already exists"
            )
        
        # Prepare book data with available_copies set to total_copies
        book_dict = book_data.model_dump()
        total_copies = book_dict.pop('total_copies')
        book_dict['total_copies'] = total_copies
        book_dict['available_copies'] = total_copies
        
        # Create book
        db_book = self.create(db, book_dict)
        
        log_business_event(
            self.logger,
            "book_created",
            book_id=db_book.id,
            book_title=db_book.title,
            total_copies=db_book.total_copies
        )
        
        return db_book
    
    def get_books(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Book]:
        """
        Get all books with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of book instances
        """
        self.logger.info(f"Listing books: skip={skip}, limit={limit}")
        return self.get_all(db, skip=skip, limit=limit)
    
    def get_book_by_id(
        self,
        db: Session,
        book_id: int
    ) -> Book:
        """
        Get a specific book by ID.
        
        Args:
            db: Database session
            book_id: Book ID
            
        Returns:
            Book instance
            
        Raises:
            HTTPException: If book not found
        """
        self.logger.info(f"Getting book: {book_id}")
        return self.get_by_id(db, book_id)
    
    def update_book(
        self,
        db: Session,
        book_id: int,
        book_update: BookUpdate
    ) -> Book:
        """
        Update book information including availability management.
        
        Args:
            db: Database session
            book_id: Book ID to update
            book_update: Update data
            
        Returns:
            Updated book instance
            
        Raises:
            HTTPException: If book not found, ISBN already in use,
                          or total_copies would be less than borrowed copies
        """
        self.logger.info(f"Updating book: {book_id}")
        
        # Get existing book
        db_book = self.get_by_id(db, book_id)
        
        # Check ISBN uniqueness if ISBN is being updated
        if book_update.isbn and book_update.isbn != db_book.isbn:
            if self.exists_by_field(
                db,
                "isbn",
                book_update.isbn,
                exclude_id=book_id
            ):
                log_error(
                    self.logger,
                    "ISBN already in use",
                    book_id=book_id,
                    isbn=book_update.isbn
                )
                raise HTTPException(
                    status_code=400,
                    detail="ISBN already in use"
                )
        
        update_data = book_update.model_dump(exclude_unset=True)
        
        # Handle total_copies update with availability management
        if 'total_copies' in update_data:
            borrowed_count = db_book.total_copies - db_book.available_copies
            new_total = update_data['total_copies']
            
            if new_total < borrowed_count:
                log_error(
                    self.logger,
                    "Cannot reduce total_copies below borrowed count",
                    book_id=book_id,
                    new_total=new_total,
                    borrowed_count=borrowed_count
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot set total copies to {new_total}. "
                           f"{borrowed_count} copies are currently borrowed."
                )
            
            # Update available_copies to maintain borrowed count
            update_data['available_copies'] = new_total - borrowed_count
        
        # Update book
        db_book = self.update(db, db_book, update_data)
        
        log_business_event(
            self.logger,
            "book_updated",
            book_id=book_id,
            fields_updated=list(update_data.keys())
        )
        
        return db_book
    
    def delete_book(
        self,
        db: Session,
        book_id: int
    ) -> None:
        """
        Delete a book (soft delete).
        
        Args:
            db: Database session
            book_id: Book ID to delete
            
        Raises:
            HTTPException: If book not found
        """
        self.logger.info(f"Deleting book: {book_id}")
        
        # Get existing book
        db_book = self.get_by_id(db, book_id)
        
        # Soft delete
        self.delete(db, db_book, soft_delete=True)
        
        log_business_event(
            self.logger,
            "book_deleted",
            book_id=book_id
        )
    
    def check_availability(
        self,
        db: Session,
        book_id: int
    ) -> bool:
        """
        Check if a book is available for borrowing.
        
        Args:
            db: Database session
            book_id: Book ID to check
            
        Returns:
            True if available, False otherwise
        """
        book = self.get_by_id(db, book_id)
        return book.is_active and book.available_copies > 0
    
    def decrease_availability(
        self,
        db: Session,
        book: Book
    ) -> None:
        """
        Decrease available copies when a book is borrowed.
        
        Args:
            db: Database session
            book: Book instance
        """
        if book.available_copies <= 0:
            raise ValueError("No copies available")
        
        book.available_copies -= 1
        db.commit()
    
    def increase_availability(
        self,
        db: Session,
        book: Book
    ) -> None:
        """
        Increase available copies when a book is returned.
        
        Args:
            db: Database session
            book: Book instance
        """
        if book.available_copies >= book.total_copies:
            raise ValueError("Available copies cannot exceed total copies")
        
        book.available_copies += 1
        db.commit()


# Singleton instance
book_controller = BookController()
