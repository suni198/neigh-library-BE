"""
Test configuration and fixtures for pytest
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test database URL before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db.database import Base, get_db
from app.core.security import get_password_hash

# Import all models so they are registered with Base.metadata before create_all() is called
import app.models.models  # noqa: F401

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session"""
    # Import app here to avoid database connection during import
    from app.main import app
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app.models.models import User
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user"""
    from app.models.models import User
    
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def auth_token(client, admin_user):
    """Get authentication token for admin user"""
    response = client.post(
        "/auth/login",
        data={
            "username": "admin",
            "password": "adminpassword"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers with token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_member(db_session):
    """Create a test member"""
    from app.models.models import Member
    
    member = Member(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="555-0101",
        address="123 Main St"
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


@pytest.fixture
def test_book(db_session):
    """Create a test book"""
    from app.models.models import Book
    
    book = Book(
        title="Test Book",
        author="Test Author",
        isbn="9780001000001",
        publication_year=2024,
        genre="Fiction",
        total_copies=3,
        available_copies=3
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book
