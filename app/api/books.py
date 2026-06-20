from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.schemas import Book as BookSchema, BookCreate, BookUpdate
from app.controllers.book_controller import book_controller

router = APIRouter(prefix="/books", tags=["books"])


@router.post("/", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
def create_book(
    book: BookCreate,
    db: Session = Depends(get_db)
) -> BookSchema:
    """Add a new book to the library"""
    return book_controller.create_book(db, book)


@router.get("/", response_model=List[BookSchema])
def list_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[BookSchema]:
    """List all books in the library"""
    return book_controller.get_books(db, skip, limit)


@router.get("/{book_id}", response_model=BookSchema)
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
) -> BookSchema:
    """Get a specific book by ID"""
    return book_controller.get_book_by_id(db, book_id)


@router.put("/{book_id}", response_model=BookSchema)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db)
) -> BookSchema:
    """Update book information"""
    return book_controller.update_book(db, book_id, book_update)


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
) -> None:
    """Delete a book (soft delete by setting is_active=False)"""
    book_controller.delete_book(db, book_id)
    return None
