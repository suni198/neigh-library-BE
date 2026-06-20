"""
Unit tests for book endpoints
"""

import pytest
from fastapi import status


class TestBookEndpoints:
    """Test cases for book CRUD operations"""
    
    def test_create_book_success(self, client, auth_headers):
        """Test successful book creation"""
        book_data = {
            "title": "New Test Book",
            "author": "New Author",
            "isbn": "978-0-new-001",
            "publication_year": 2024,
            "genre": "Science Fiction",
            "total_copies": 5
        }
        
        response = client.post(
            "/books/",
            json=book_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["total_copies"] == book_data["total_copies"]
        assert data["available_copies"] == book_data["total_copies"]
    
    def test_get_books_list(self, client, auth_headers, test_book):
        """Test listing all books"""
        response = client.get("/books/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(b["isbn"] == test_book.isbn for b in data)
    
    def test_get_book_by_id(self, client, auth_headers, test_book):
        """Test getting a specific book"""
        response = client.get(
            f"/books/{test_book.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_book.id
        assert data["title"] == test_book.title
    
    def test_update_book_success(self, client, auth_headers, test_book):
        """Test successful book update"""
        update_data = {
            "title": "Updated Book Title",
            "total_copies": 10
        }
        
        response = client.put(
            f"/books/{test_book.id}/",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["total_copies"] == update_data["total_copies"]
    
    def test_delete_book_success(self, client, auth_headers, test_book):
        """Test successful book deletion"""
        response = client.delete(
            f"/books/{test_book.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestBorrowingEndpoints:
    """Test cases for borrowing operations"""
    
    def test_borrow_book_success(self, client, auth_headers, test_member, test_book):
        """Test successful book borrowing"""
        from datetime import datetime, timedelta
        
        due_date = (datetime.utcnow() + timedelta(days=14)).isoformat()
        
        borrowing_data = {
            "member_id": test_member.id,
            "book_id": test_book.id,
            "due_date": due_date
        }
        
        response = client.post(
            "/borrowings/",
            json=borrowing_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["member_id"] == test_member.id
        assert data["book_id"] == test_book.id
        assert data["status"] == "BORROWED"
    
    def test_return_book_success(self, client, auth_headers, test_member, test_book, db_session):
        """Test successful book return"""
        from app.models.models import Borrowing
        from datetime import datetime, timedelta
        
        # Create a borrowing first
        borrowing = Borrowing(
            member_id=test_member.id,
            book_id=test_book.id,
            borrowed_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=14),
            status="BORROWED"
        )
        db_session.add(borrowing)
        
        # Update book availability
        test_book.available_copies -= 1
        db_session.commit()
        db_session.refresh(borrowing)
        
        # Return the book
        response = client.post(
            f"/borrowings/{borrowing.id}/return/",
            json={},
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "RETURNED"
        assert data["returned_date"] is not None
    
    def test_get_borrowings_list(self, client, auth_headers):
        """Test listing all borrowings"""
        response = client.get("/borrowings/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
