from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, User as UserSchema, Token
from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.controllers.auth_controller import auth_controller

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
) -> UserSchema:
    """Register a new user"""
    return auth_controller.register_user(db, user)


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """Login to get access token"""
    return auth_controller.login(db, form_data.username, form_data.password)


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserSchema:
    """Get current user information"""
    logger.info(f"User info requested", extra={"user_id": current_user.id})
    return current_user
