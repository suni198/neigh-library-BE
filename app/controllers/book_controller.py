"""
Book controller handling all book-related business logic.
"""

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.controllers.base_controller import BaseController
from app.models.models import Book, Borrowing
from app.schemas.schemas import BookCreate, BookUpdate
from app.core.logging import log_business_event, log_error


class BookController(BaseController[Book]):

    def __init__(self):
        super().__init__(Book)

    def create_book(self, db: Session, book_data: BookCreate) -> Book:
        """Add a new book to the library."""
        with self._handle_db_errors(db, "create_book"):
            self.logger.info(f"Creating book: {book_data.title}")
            if book_data.isbn and self.exists_by_field(db, "isbn", book_data.isbn):
                log_error(self.logger, "Book creation failed: ISBN already exists",
                          isbn=book_data.isbn)
                raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
            book_dict = book_data.model_dump()
            total_copies = book_dict['total_copies']
            book_dict['available_copies'] = total_copies
            db_book = self.create(db, book_dict)
            log_business_event(self.logger, "book_created",
                               book_id=db_book.id, book_title=db_book.title,
                               total_copies=db_book.total_copies)
            return db_book

    def get_books(self, db: Session, skip: int = 0, limit: int = 100) -> List[Book]:
        """Get all books with pagination."""
        with self._handle_db_errors(db, "get_books"):
            self.logger.info(f"Listing books: skip={skip}, limit={limit}")
            return self.get_all(db, skip=skip, limit=limit)

    def get_book_by_id(self, db: Session, book_id: int) -> Book:
        """Get a specific book by ID."""
        with self._handle_db_errors(db, "get_book_by_id"):
            self.logger.info(f"Getting book: {book_id}")
            return self.get_by_id(db, book_id)

    def update_book(self, db: Session, book_id: int, book_update: BookUpdate) -> Book:
        """Update book information including availability management."""
        with self._handle_db_errors(db, "update_book"):
            self.logger.info(f"Updating book: {book_id}")
            db_book = self.get_by_id(db, book_id)
            if book_update.isbn and book_update.isbn != db_book.isbn:
                if self.exists_by_field(db, "isbn", book_update.isbn, exclude_id=book_id):
                    log_error(self.logger, "ISBN already in use",
                              book_id=book_id, isbn=book_update.isbn)
                    raise HTTPException(status_code=400, detail="ISBN already in use")
            update_data = book_update.model_dump(exclude_unset=True)
            if 'total_copies' in update_data:
                borrowed_count = db_book.total_copies - db_book.available_copies
                new_total = update_data['total_copies']
                if new_total < borrowed_count:
                    log_error(self.logger, "Cannot reduce total_copies below borrowed count",
                              book_id=book_id, new_total=new_total, borrowed_count=borrowed_count)
                    raise HTTPException(
                        status_code=400,
                        detail=f"Cannot set total copies to {new_total}. "
                               f"{borrowed_count} copies are currently borrowed."
                    )
                update_data['available_copies'] = new_total - borrowed_count
            db_book = self.update(db, db_book, update_data)
            log_business_event(self.logger, "book_updated",
                               book_id=book_id, fields_updated=list(update_data.keys()))
            return db_book

    def delete_book(self, db: Session, book_id: int) -> None:
        """Soft-delete a book; blocked if active borrowings exist."""
        with self._handle_db_errors(db, "delete_book"):
            self.logger.info(f"Deleting book: {book_id}")
            db_book = self.get_by_id(db, book_id)
            active_borrowings = db.query(Borrowing).filter(
                Borrowing.book_id == book_id,
                Borrowing.status == 'BORROWED'
            ).count()
            if active_borrowings > 0:
                log_error(self.logger, "Cannot delete book with active borrowings",
                          book_id=book_id, book_title=db_book.title,
                          active_borrowings=active_borrowings)
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete book. This book has {active_borrowings} active borrowing(s). "
                           "Please wait for all copies to be returned first."
                )
            self.delete(db, db_book, soft_delete=True)
            log_business_event(self.logger, "book_deleted", book_id=book_id)

    # ── availability helpers (called by BorrowingController) ──────────────────

    def check_availability(self, db: Session, book_id: int) -> bool:
        """Return True if the book exists, is active, and has available copies."""
        book = self.get_by_id(db, book_id)
        return book.is_active and book.available_copies > 0

    def decrease_availability(self, db: Session, book: Book) -> None:
        """Decrement available copies when a book is borrowed."""
        if book.available_copies <= 0:
            raise ValueError("No copies available")
        book.available_copies -= 1
        db.commit()

    def increase_availability(self, db: Session, book: Book) -> None:
        """Increment available copies when a book is returned."""
        if book.available_copies >= book.total_copies:
            raise ValueError("Available copies cannot exceed total copies")
        book.available_copies += 1
        db.commit()


book_controller = BookController()
