"""
Authentication controller handling user registration and login logic.
"""

from typing import Dict
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import User
from app.schemas.schemas import UserCreate
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.core.logging import get_logger, log_business_event, log_error


class AuthController:
    """
    Controller for authentication operations including registration and login.
    """
    
    def __init__(self):
        """Initialize auth controller."""
        self.logger = get_logger(self.__class__.__name__)
    
    def register_user(
        self,
        db: Session,
        user_data: UserCreate
    ) -> User:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            Created user instance
            
        Raises:
            HTTPException: If username or email already exists
        """
        self.logger.info(f"Registration attempt for username: {user_data.username}")
        
        # Check if username exists
        existing_user = db.query(User).filter(
            User.username == user_data.username
        ).first()
        
        if existing_user:
            log_error(
                self.logger,
                "Registration failed: Username already exists",
                username=user_data.username
            )
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        # Check if email exists
        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()
        
        if existing_email:
            log_error(
                self.logger,
                "Registration failed: Email already exists",
                email=user_data.email
            )
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Create user with hashed password
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        log_business_event(
            self.logger,
            "user_registered",
            user_id=db_user.id,
            username=db_user.username
        )
        
        return db_user
    
    def authenticate_user(
        self,
        db: Session,
        username: str,
        password: str
    ) -> User:
        """
        Authenticate user with username and password.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            Authenticated user instance
            
        Raises:
            HTTPException: If authentication fails or user is inactive
        """
        self.logger.info(f"Authentication attempt for username: {username}")
        
        # Get user
        user = db.query(User).filter(User.username == username).first()
        
        # Verify password
        if not user or not verify_password(password, user.hashed_password):
            log_error(
                self.logger,
                "Authentication failed: Invalid credentials",
                username=username
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            log_error(
                self.logger,
                "Authentication failed: Inactive user",
                username=username,
                user_id=user.id
            )
            raise HTTPException(
                status_code=400,
                detail="Inactive user"
            )
        
        return user
    
    def create_user_token(
        self,
        user: User
    ) -> Dict[str, str]:
        """
        Create access token for authenticated user.
        
        Args:
            user: Authenticated user instance
            
        Returns:
            Dictionary with access_token and token_type
        """
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        log_business_event(
            self.logger,
            "user_logged_in",
            user_id=user.id,
            username=user.username
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    def login(
        self,
        db: Session,
        username: str,
        password: str
    ) -> Dict[str, str]:
        """
        Login user and return access token.
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            Dictionary with access_token and token_type
            
        Raises:
            HTTPException: If authentication fails
        """
        # Authenticate user
        user = self.authenticate_user(db, username, password)
        
        # Create and return token
        return self.create_user_token(user)


# Singleton instance
auth_controller = AuthController()
