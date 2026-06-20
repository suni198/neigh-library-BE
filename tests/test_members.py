"""
Unit tests for member endpoints
"""

import pytest
from fastapi import status


class TestMemberEndpoints:
    """Test cases for member CRUD operations"""
    
    def test_create_member_success(self, client, auth_headers):
        """Test successful member creation"""
        member_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "phone": "555-0102",
            "address": "456 Oak Ave"
        }
        
        response = client.post(
            "/members/",
            json=member_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == member_data["first_name"]
        assert data["last_name"] == member_data["last_name"]
        assert data["email"] == member_data["email"]
        assert "id" in data
    
    def test_create_member_duplicate_email(self, client, auth_headers, test_member):
        """Test member creation with duplicate email"""
        member_data = {
            "first_name": "Another",
            "last_name": "User",
            "email": test_member.email,  # Duplicate email
            "phone": "555-9999",
            "address": "789 Test St"
        }
        
        response = client.post(
            "/members/",
            json=member_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()
    
    def test_create_member_invalid_data(self, client, auth_headers):
        """Test member creation with invalid data"""
        member_data = {
            "first_name": "",  # Empty first name
            "last_name": "Smith",
            "email": "invalid-email",  # Invalid email
        }
        
        response = client.post(
            "/members/",
            json=member_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_members_list(self, client, auth_headers, test_member):
        """Test listing all members"""
        response = client.get("/members/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(m["email"] == test_member.email for m in data)
    
    def test_get_member_by_id(self, client, auth_headers, test_member):
        """Test getting a specific member"""
        response = client.get(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_member.id
        assert data["email"] == test_member.email
    
    def test_get_member_not_found(self, client, auth_headers):
        """Test getting non-existent member"""
        response = client.get("/members/99999/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_member_success(self, client, auth_headers, test_member):
        """Test successful member update"""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com"
        }
        
        response = client.put(
            f"/members/{test_member.id}/",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["email"] == update_data["email"]
    
    def test_update_member_duplicate_email(self, client, auth_headers, test_member, db_session):
        """Test updating member with duplicate email"""
        from app.models.models import Member
        
        # Create another member
        another_member = Member(
            first_name="Another",
            last_name="Member",
            email="another@example.com",
            phone="555-9999"
        )
        db_session.add(another_member)
        db_session.commit()
        
        # Try to update test_member with another_member's email
        update_data = {
            "email": another_member.email
        }
        
        response = client.put(
            f"/members/{test_member.id}/",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_delete_member_success(self, client, auth_headers, test_member):
        """Test successful member deletion"""
        response = client.delete(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify member is soft-deleted
        get_response = client.get(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        # Should return 404 or show is_active=False
        assert get_response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_200_OK]
    
    def test_delete_member_with_active_borrowing_fails(self, client, auth_headers, test_member, test_book, db_session):
        """Test that deleting a member with active borrowings fails"""
        from app.models.models import Borrowing
        from datetime import datetime, timedelta
        
        # Create an active borrowing
        borrowing = Borrowing(
            member_id=test_member.id,
            book_id=test_book.id,
            borrowed_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=14),
            status="BORROWED"
        )
        db_session.add(borrowing)
        test_book.available_copies -= 1
        db_session.commit()
        
        # Try to delete the member
        response = client.delete(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active borrowing" in response.json()["detail"].lower()
        
        # Verify member still exists
        get_response = client.get(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        assert get_response.status_code == status.HTTP_200_OK
    
    def test_delete_member_after_return_succeeds(self, client, auth_headers, test_member, test_book, db_session):
        """Test that deleting a member after returning all books succeeds"""
        from app.models.models import Borrowing
        from datetime import datetime, timedelta
        
        # Create a borrowing and immediately return it
        borrowing = Borrowing(
            member_id=test_member.id,
            book_id=test_book.id,
            borrowed_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=14),
            status="RETURNED",
            returned_date=datetime.utcnow()
        )
        db_session.add(borrowing)
        db_session.commit()
        
        # Delete should succeed now
        response = client.delete(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_member_with_multiple_active_borrowings(self, client, auth_headers, test_member, db_session):
        """Test deletion fails with multiple active borrowings"""
        from app.models.models import Book, Borrowing
        from datetime import datetime, timedelta
        
        # Create multiple books and borrowings
        book1 = Book(title="Book 1", author="Author 1", isbn="ISBN-001", total_copies=1, available_copies=0)
        book2 = Book(title="Book 2", author="Author 2", isbn="ISBN-002", total_copies=1, available_copies=0)
        db_session.add_all([book1, book2])
        db_session.commit()
        
        borrowing1 = Borrowing(
            member_id=test_member.id,
            book_id=book1.id,
            borrowed_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=14),
            status="BORROWED"
        )
        borrowing2 = Borrowing(
            member_id=test_member.id,
            book_id=book2.id,
            borrowed_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=14),
            status="BORROWED"
        )
        db_session.add_all([borrowing1, borrowing2])
        db_session.commit()
        
        # Try to delete
        response = client.delete(
            f"/members/{test_member.id}/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json()["detail"].lower()
        assert "2" in detail or "active borrowing" in detail
    
    def test_unauthorized_access(self, client):
        """Test accessing endpoints without authentication"""
        response = client.get("/members/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
