from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Date, DECIMAL, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    address = Column(Text)
    membership_date = Column(Date, nullable=False, server_default=func.current_date())
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    borrowings = relationship("Borrowing", back_populates="member")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(13), unique=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    publisher = Column(String(255))
    publication_year = Column(Integer)
    genre = Column(String(100))
    total_copies = Column(Integer, nullable=False, default=1)
    available_copies = Column(Integer, nullable=False, default=1)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('total_copies >= 0', name='check_total_copies'),
        CheckConstraint('available_copies >= 0', name='check_available_copies'),
        CheckConstraint('available_copies <= total_copies', name='check_available_lte_total'),
    )

    borrowings = relationship("Borrowing", back_populates="book")

class Borrowing(Base):
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="RESTRICT"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="RESTRICT"), nullable=False, index=True)
    borrowed_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    due_date = Column(DateTime(timezone=True), nullable=False, index=True)
    return_date = Column(DateTime(timezone=True))
    fine_amount = Column(DECIMAL(10, 2), default=0.00)
    status = Column(String(20), nullable=False, default='BORROWED', index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('BORROWED', 'RETURNED', 'OVERDUE', 'LOST')", name='check_status'),
        CheckConstraint('fine_amount >= 0', name='check_fine_amount'),
    )

    member = relationship("Member", back_populates="borrowings")
    book = relationship("Book", back_populates="borrowings")
