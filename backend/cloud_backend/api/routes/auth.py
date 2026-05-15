from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx
import json

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


# OAuth Login URLs
@router.get("/oauth/google")
def google_login():
    """Redirect to Google OAuth consent screen"""
    if not settings.google_client_id:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}&"
        f"redirect_uri={settings.google_redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    return {"auth_url": auth_url}


@router.get("/oauth/facebook")
def facebook_login():
    """Redirect to Facebook OAuth consent screen"""
    if not settings.facebook_client_id:
        raise HTTPException(status_code=400, detail="Facebook OAuth not configured")
    
    auth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={settings.facebook_client_id}&"
        f"redirect_uri={settings.facebook_redirect_uri}&"
        f"scope=email,public_profile&"
        f"response_type=code"
    )
    return {"auth_url": auth_url}


@router.get("/oauth/github")
def github_login():
    """Redirect to GitHub OAuth consent screen"""
    if not settings.github_client_id:
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")
    
    auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.github_client_id}&"
        f"redirect_uri={settings.github_redirect_uri}&"
        f"scope=read:user%20user:email"
    )
    return {"auth_url": auth_url}


# OAuth Callbacks
@router.get("/callback/google")
async def google_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token from Google")
        
        tokens = token_response.json()
        access_token = tokens["access_token"]
        
        # Get user info
        user_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        user_info = user_response.json()
        email = user_info.get("email")
        username = user_info.get("email", "").split("@")[0]
        name = user_info.get("name", username)
        
        # Create or get user
        from cloud_backend.models.user import User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = register_user(db, username, email, "oauth_google_user")
        
        access_tkn, refresh_tkn = issue_token_pair(db, user)
        return {
            "access_token": access_tkn,
            "refresh_token": refresh_tkn,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }


@router.get("/callback/facebook")
async def facebook_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Handle Facebook OAuth callback"""
    if not settings.facebook_client_id or not settings.facebook_client_secret:
        raise HTTPException(status_code=400, detail="Facebook OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_response = await client.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "code": code,
                "client_id": settings.facebook_client_id,
                "client_secret": settings.facebook_client_secret,
                "redirect_uri": settings.facebook_redirect_uri,
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token from Facebook")
        
        tokens = token_response.json()
        access_token = tokens["access_token"]
        
        # Get user info
        user_response = await client.get(
            "https://graph.facebook.com/v18.0/me",
            params={"access_token": access_token, "fields": "id,name,email"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from Facebook")
        
        user_info = user_response.json()
        email = user_info.get("email", f"fb_{user_info.get('id')}@facebook.local")
        username = user_info.get("name", "").replace(" ", "_").lower() or f"fb_{user_info.get('id')}"
        
        # Create or get user
        from cloud_backend.models.user import User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = register_user(db, username, email, "oauth_facebook_user")
        
        access_tkn, refresh_tkn = issue_token_pair(db, user)
        return {
            "access_token": access_tkn,
            "refresh_token": refresh_tkn,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }


@router.get("/callback/github")
async def github_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback"""
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=400, detail="GitHub OAuth not configured")
    
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "code": code,
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "redirect_uri": settings.github_redirect_uri,
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get token from GitHub")
        
        tokens = token_response.json()
        access_token = tokens["access_token"]
        
        # Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info from GitHub")
        
        user_info = user_response.json()
        username = user_info.get("login", "")
        
        # Get email if not public
        email = user_info.get("email")
        if not email:
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if emails_response.status_code == 200:
                emails = emails_response.json()
                primary_email = next((e for e in emails if e.get("primary")), emails[0])
                email = primary_email.get("email")
        
        if not email:
            email = f"gh_{username}@github.local"
        
        # Create or get user
        from cloud_backend.models.user import User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = register_user(db, username, email, "oauth_github_user")
        
        access_tkn, refresh_tkn = issue_token_pair(db, user)
        return {
            "access_token": access_tkn,
            "refresh_token": refresh_tkn,
            "user": {"id": user.id, "username": user.username, "email": user.email},
        }
