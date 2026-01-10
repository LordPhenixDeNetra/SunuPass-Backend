from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, new_jti, verify_password
from app.core.settings import get_settings
from app.models.user import Utilisateur
from app.schemas.auth import LoginRequest
from app.schemas.user import UtilisateurRegister
from app.services.refresh_tokens import store_refresh_token
from app.services.users import get_utilisateur_by_email


def register_user(db: Session, payload: UtilisateurRegister) -> Utilisateur:
    user = Utilisateur(
        email=payload.email,
        nom_complet=payload.nom_complet,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> Utilisateur | None:
    user = get_utilisateur_by_email(db, payload.email)
    if user is None or not user.is_active:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(payload.password, user.hashed_password):
        return None
    return user


def issue_access_token_for_user(user: Utilisateur) -> str:
    return create_access_token(subject=str(user.id))


def issue_token_pair_for_user(db: Session, user: Utilisateur) -> tuple[str, str]:
    settings = get_settings()
    jti = new_jti()
    refresh_token = create_refresh_token(subject=str(user.id), jti=jti)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    store_refresh_token(db, user_id=user.id, jti=jti, refresh_token=refresh_token, expires_at=expires_at)
    access_token = create_access_token(subject=str(user.id))
    return access_token, refresh_token
