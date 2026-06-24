from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    Borrowing as BorrowingSchema, 
    BorrowingCreate, 
    BorrowingReturn,
    BorrowingWithDetails
)
from app.core.deps import get_current_active_user
from app.controllers.borrowing_controller import borrowing_controller

router = APIRouter(prefix="/borrowings", tags=["borrowings"])

@router.post("/", response_model=BorrowingSchema, status_code=status.HTTP_201_CREATED)
def borrow_book(
    borrowing: BorrowingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BorrowingSchema:
    """Record a book being borrowed by a member"""
    return borrowing_controller.borrow_book(db, borrowing, current_user.id)

@router.post("/{borrowing_id}/return", response_model=BorrowingSchema)
def return_book(
    borrowing_id: int,
    return_data: BorrowingReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> BorrowingSchema:
    """Record a borrowed book being returned"""
    return borrowing_controller.return_book(db, borrowing_id, return_data, current_user.id)

@router.get("/", response_model=List[BorrowingWithDetails])
def list_borrowings(
    status: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
) -> List[BorrowingWithDetails]:
    """List all borrowing records with optional status filter"""
    return borrowing_controller.get_borrowings(db, status, skip, limit)

@router.get("/member/{member_id}", response_model=List[BorrowingWithDetails])
def get_member_borrowings(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[BorrowingWithDetails]:
    """Get all books borrowed by a specific member"""
    return borrowing_controller.get_member_borrowings(db, member_id)

@router.get("/book/{book_id}", response_model=List[BorrowingWithDetails])
def get_book_borrowings(
    book_id: int,
    db: Session = Depends(get_db)
) -> List[BorrowingWithDetails]:
    """Get borrowing history for a specific book"""
    return borrowing_controller.get_book_borrowings(db, book_id)


@router.get("/{borrowing_id}", response_model=BorrowingWithDetails)
def get_borrowing(
    borrowing_id: int,
    db: Session = Depends(get_db)
) -> BorrowingWithDetails:
    """Get a specific borrowing record"""
    return borrowing_controller.get_borrowing_by_id(db, borrowing_id)
