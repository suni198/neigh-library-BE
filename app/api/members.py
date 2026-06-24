from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import Member as MemberSchema, MemberCreate, MemberUpdate
from app.core.deps import get_current_active_user
from app.controllers.member_controller import member_controller

router = APIRouter(prefix="/members", tags=["members"])


@router.post("/", response_model=MemberSchema, status_code=status.HTTP_201_CREATED)
def create_member(
    member: MemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MemberSchema:
    """Create a new library member"""
    return member_controller.create_member(db, member, current_user.id)


@router.get("/", response_model=List[MemberSchema])
def list_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[MemberSchema]:
    """List all library members"""
    return member_controller.get_members(db, skip, limit)


@router.get("/{member_id}", response_model=MemberSchema)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MemberSchema:
    """Get a specific member by ID"""
    return member_controller.get_member_by_id(db, member_id)


@router.put("/{member_id}", response_model=MemberSchema)
def update_member(
    member_id: int,
    member_update: MemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> MemberSchema:
    """Update member information"""
    return member_controller.update_member(db, member_id, member_update, current_user.id)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete a member (soft delete by setting is_active=False)"""
    member_controller.delete_member(db, member_id, current_user.id)
    return None
