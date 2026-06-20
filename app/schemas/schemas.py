from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

# User/Auth Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Member Schemas
class MemberBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

class MemberCreate(MemberBase):
    pass

class MemberUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    is_active: Optional[bool] = None

class Member(MemberBase):
    id: int
    membership_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Book Schemas
class BookBase(BaseModel):
    isbn: Optional[str] = Field(None, max_length=13)
    title: str = Field(..., min_length=1, max_length=500)
    author: str = Field(..., min_length=1, max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    publication_year: Optional[int] = Field(None, ge=1000, le=9999)
    genre: Optional[str] = Field(None, max_length=100)
    total_copies: int = Field(default=1, ge=0)
    description: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    isbn: Optional[str] = Field(None, max_length=13)
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    publication_year: Optional[int] = Field(None, ge=1000, le=9999)
    genre: Optional[str] = Field(None, max_length=100)
    total_copies: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Book(BookBase):
    id: int
    available_copies: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Borrowing Schemas
class BorrowingBase(BaseModel):
    member_id: int
    book_id: int
    due_date: datetime
    notes: Optional[str] = None

class BorrowingCreate(BorrowingBase):
    pass

class BorrowingReturn(BaseModel):
    fine_amount: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None

class Borrowing(BorrowingBase):
    id: int
    borrowed_date: datetime
    return_date: Optional[datetime] = None
    fine_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BorrowingWithDetails(Borrowing):
    member: Member
    book: Book

    class Config:
        from_attributes = True
