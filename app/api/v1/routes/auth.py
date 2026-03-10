from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user_schema import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate, PasswordUpdate
from app.schemas.common import MessageResponse
from app.services.auth_service import register_user, authenticate_user, update_password, update_profile
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    user, token = register_user(db, name=data.name, email=data.email, password=data.password)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user, token = authenticate_user(db, email=data.email, password=data.password)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_profile(db, user, name=data.name, email=data.email)
    return UserResponse.model_validate(updated)


@router.put("/me/password", response_model=MessageResponse)
def change_password(
    data: PasswordUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_password(db, user, current_password=data.current_password, new_password=data.new_password)
    return MessageResponse(message="Password updated successfully")
