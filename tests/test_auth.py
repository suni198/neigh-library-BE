"""
Unit tests for authentication endpoints
"""

import pytest
from fastapi import status


class TestAuthEndpoints:
    """Test cases for authentication"""
    
    def test_login_success(self, client, admin_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            data={
                "username": "admin",
                "password": "adminpassword"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, admin_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login",
            data={
                "username": "admin",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user(self, client, auth_headers, admin_user):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "admin"
        assert data["email"] == admin_user.email
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without token"""
        response = client.get("/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_register_user_success(self, client):
        """Test successful user registration"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_register_duplicate_username(self, client, admin_user):
        """Test registration with duplicate username"""
        user_data = {
            "username": admin_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
