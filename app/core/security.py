from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, subject: str, jti: str, expires_days: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=expires_days or settings.refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def decode_token_subject(token: str) -> str | None:
    payload = decode_token(token)
    if payload is None:
        return None
    sub = payload.get("sub")
    if not isinstance(sub, str):
        return None
    return sub


def new_jti() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
