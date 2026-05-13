from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from cloud_backend.core.config import get_settings
from cloud_backend.db.session import get_db
from cloud_backend.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)
from cloud_backend.services.auth_service import (
    authenticate_user,
    issue_token_pair,
    refresh_access_token,
    register_user,
    revoke_refresh_token,
)
from cloud_backend.api.deps import get_current_user
from cloud_backend.models.user import User


router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=TokenPairResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, payload.username, payload.email, payload.password)
    access, refresh = issue_token_pair(db, user)
    return TokenPairResponse(
        access_token=access,
        refresh_token=refresh,
        access_expires_in_seconds=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenPairResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.username, payload.password)
    access, refresh = issue_token_pair(db, user)
    return TokenPairResponse(
        access_token=access,
        refresh_token=refresh,
        access_expires_in_seconds=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    access_token = refresh_access_token(db, payload.refresh_token)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "access_expires_in_seconds": settings.access_token_expire_minutes * 60,
    }


@router.post("/logout")
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(db, payload.refresh_token)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
