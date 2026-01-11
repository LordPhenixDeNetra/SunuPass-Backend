from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken


def store_refresh_token(
    db: Session,
    *,
    user_id,
    jti: str,
    refresh_token: str,
    expires_at,
) -> RefreshToken:
    row = RefreshToken(
        user_id=user_id,
        jti=jti,
        token_hash=hash_token(refresh_token),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_refresh_token_by_jti(db: Session, jti: str) -> RefreshToken | None:
    return db.execute(select(RefreshToken).where(RefreshToken.jti == jti)).scalar_one_or_none()


def verify_refresh_token_row(row: RefreshToken, refresh_token: str) -> bool:
    expires_at = row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if row.revoked:
        return False
    if expires_at <= datetime.now(timezone.utc):
        return False
    return row.token_hash == hash_token(refresh_token)


def revoke_refresh_token(db: Session, row: RefreshToken) -> None:
    row.revoked = True
    db.add(row)
    db.commit()
