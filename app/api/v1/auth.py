from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.openapi_responses import RESPONSES_401, RESPONSES_422, RESPONSES_500
from app.db.session import get_db
from app.core.security import decode_token
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.schemas.user import UtilisateurRead, UtilisateurRegister
from app.services.auth import authenticate_user, issue_token_pair_for_user, register_user
from app.services.refresh_tokens import (
    get_refresh_token_by_jti,
    revoke_refresh_token,
    verify_refresh_token_row,
)
from app.services.users import get_utilisateur_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UtilisateurRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte",
    description="Crée un nouvel utilisateur avec mot de passe hashé.",
    responses={400: {"description": "Email déjà enregistré."}, 422: RESPONSES_422, 500: RESPONSES_500},
)
def register(payload: UtilisateurRegister, db: Session = Depends(get_db)) -> UtilisateurRead:
    existing = get_utilisateur_by_email(db, payload.email)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = register_user(db, payload)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Se connecter",
    description="Retourne un access token et un refresh token.",
    responses={401: RESPONSES_401, 422: RESPONSES_422, 500: RESPONSES_500},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, refresh_token = issue_token_pair_for_user(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rafraîchir les tokens",
    description="Effectue la rotation du refresh token et renvoie un nouveau couple de tokens.",
    responses={401: RESPONSES_401, 422: RESPONSES_422, 500: RESPONSES_500},
)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> Token:
    decoded = decode_token(payload.refresh_token)
    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    jti = decoded.get("jti")
    sub = decoded.get("sub")
    if not isinstance(jti, str) or not isinstance(sub, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    row = get_refresh_token_by_jti(db, jti)
    if row is None or not verify_refresh_token_row(row, payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    revoke_refresh_token(db, row)
    user = row.user
    access_token, refresh_token = issue_token_pair_for_user(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Se déconnecter",
    description="Révoque le refresh token fourni (si valide).",
    responses={422: RESPONSES_422, 500: RESPONSES_500},
)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    decoded = decode_token(payload.refresh_token)
    if decoded is None or decoded.get("type") != "refresh":
        return
    jti = decoded.get("jti")
    if not isinstance(jti, str):
        return
    row = get_refresh_token_by_jti(db, jti)
    if row is None:
        return
    if verify_refresh_token_row(row, payload.refresh_token):
        revoke_refresh_token(db, row)
