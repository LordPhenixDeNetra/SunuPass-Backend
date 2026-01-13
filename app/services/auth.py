from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, new_jti, verify_password
from app.core.settings import get_settings
from app.models.user import Participant, Utilisateur
from app.schemas.auth import LoginRequest
from app.schemas.user import UtilisateurRegister
from app.services.refresh_tokens import store_refresh_token
from app.services.users import get_utilisateur_by_email


def register_user(db: Session, payload: UtilisateurRegister) -> Utilisateur:
    user = Participant(
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


@lru_cache(maxsize=1)
def _get_firebase_app():
    settings = get_settings()
    if not settings.firebase_auth_enabled:
        raise ValueError("Firebase auth disabled")

    try:
        import firebase_admin
        from firebase_admin import credentials
    except Exception as e:
        raise ValueError("Firebase auth not available") from e

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    cred = None
    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    elif settings.firebase_service_account_json:
        cred = credentials.Certificate(json.loads(settings.firebase_service_account_json))
    else:
        cred = credentials.ApplicationDefault()

    options: dict[str, object] = {}
    if settings.firebase_project_id:
        options["projectId"] = settings.firebase_project_id

    if options:
        return firebase_admin.initialize_app(cred, options=options)
    return firebase_admin.initialize_app(cred)


def verify_firebase_id_token(id_token: str) -> dict[str, object]:
    try:
        from firebase_admin import auth as firebase_auth
    except Exception as e:
        raise ValueError("Firebase auth not available") from e

    app = _get_firebase_app()
    try:
        decoded = firebase_auth.verify_id_token(id_token, app=app, check_revoked=True)
    except Exception as e:
        raise ValueError("Invalid Firebase token") from e
    if not isinstance(decoded, dict):
        raise ValueError("Invalid Firebase token")
    return decoded


def authenticate_firebase_user(db: Session, *, id_token: str) -> Utilisateur:
    decoded = verify_firebase_id_token(id_token)
    email = decoded.get("email")
    if not isinstance(email, str) or not email.strip():
        raise ValueError("Firebase token has no email")
    email_verified = decoded.get("email_verified")
    if email_verified is False:
        raise ValueError("Email not verified")

    nom_complet = decoded.get("name")
    if not isinstance(nom_complet, str):
        nom_complet = None

    user = get_utilisateur_by_email(db, email.strip().lower())
    if user is None:
        user = Participant(email=email.strip().lower(), nom_complet=nom_complet, hashed_password=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    if not user.is_active:
        raise ValueError("Inactive user")

    if nom_complet and user.nom_complet != nom_complet:
        user.nom_complet = nom_complet
        db.commit()
        db.refresh(user)

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
