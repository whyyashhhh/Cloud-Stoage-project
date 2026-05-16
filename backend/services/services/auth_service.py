from datetime import datetime, timedelta, timezone
import hashlib
import jwt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from cloud_backend.core.config import get_settings
from cloud_backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from cloud_backend.models.refresh_token import RefreshToken
from cloud_backend.models.user import User


settings = get_settings()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def register_user(db: Session, username: str, email: str, password: str) -> User:
    existing = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    user = User(username=username, email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")
    return user


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    payload = decode_token(refresh_token)
    jti = payload["jti"]
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    record = RefreshToken(
        user_id=user.id,
        jti=jti,
        token_hash=_hash_token(refresh_token),
        expires_at=exp,
    )
    db.add(record)
    db.commit()

    return access_token, refresh_token


def refresh_access_token(db: Session, refresh_token: str) -> str:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type")

    jti = payload.get("jti")
    subject = payload.get("sub")

    record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not record or record.revoked or record.token_hash != _hash_token(refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    return create_access_token(subject=subject)


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    try:
        payload = decode_token(refresh_token)
    except jwt.PyJWTError:
        return

    jti = payload.get("jti")
    if not jti:
        return

    record = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if record:
        record.revoked = True
        db.commit()
