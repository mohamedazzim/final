from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, UserRole, Cause
from schemas import UserAdminResponse, CauseResponse, CauseCreate, UserUpdateRole
from routers.auth import get_current_user

router = APIRouter()


def check_superadmin(current_user: User):
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Not authorized. Superadmin access required.")


@router.get("/users", response_model=List[UserAdminResponse])
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superadmin(current_user)
    users = db.query(User).all()
    return users


@router.put("/users/{user_id}/role", response_model=UserAdminResponse)
async def update_user_role(
    user_id: int,
    role_update: UserUpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superadmin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superadmin(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.put("/causes/{cause_id}", response_model=CauseResponse)
async def update_cause(
    cause_id: int,
    cause_data: CauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superadmin(current_user)
    
    cause = db.query(Cause).filter(Cause.id == cause_id).first()
    if not cause:
        raise HTTPException(status_code=404, detail="Cause not found")
    
    for field, value in cause_data.model_dump(exclude_unset=True).items():
        setattr(cause, field, value)
    
    db.commit()
    db.refresh(cause)
    return cause


@router.delete("/causes/{cause_id}")
async def delete_cause(
    cause_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_superadmin(current_user)
    
    cause = db.query(Cause).filter(Cause.id == cause_id).first()
    if not cause:
        raise HTTPException(status_code=404, detail="Cause not found")
    
    db.delete(cause)
    db.commit()
    return {"message": "Cause deleted successfully"}
