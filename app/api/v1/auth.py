from __future__ import annotations

from json import JSONDecodeError

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.api.openapi_responses import RESPONSES_401, RESPONSES_422, RESPONSES_500
from app.db.session import get_db
from app.core.security import decode_token
from app.schemas.auth import FirebaseLoginRequest, LoginRequest, RefreshRequest, Token
from app.schemas.user import UtilisateurRead, UtilisateurRegister
from app.services.auth import authenticate_firebase_user, authenticate_user, issue_token_pair_for_user, register_user
from app.services.refresh_tokens import (
    get_refresh_token_by_jti,
    revoke_refresh_token,
    verify_refresh_token_row,
)
from app.services.users import get_utilisateur_by_email
from fastapi.security import OAuth2PasswordRequestForm

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
    summary="Se connecter (JSON ou Form)",
    description="Retourne un access token et un refresh token via JSON ou form-urlencoded.",
    responses={401: RESPONSES_401, 422: RESPONSES_422, 500: RESPONSES_500},
)
async def login(request: Request, db: Session = Depends(get_db)) -> Token:
    content_type = (request.headers.get("content-type") or "").lower()
    try:
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            email = form.get("email") or form.get("username")
            password = form.get("password")
            payload = LoginRequest(email=email, password=password)
        else:
            data = await request.json()
            payload = LoginRequest(**data)
    except (ValidationError, TypeError) as e:
        errors = e.errors() if isinstance(e, ValidationError) else []
        raise RequestValidationError(errors) from e
    except JSONDecodeError as e:
        raise RequestValidationError(
            [
                {
                    "loc": ("body",),
                    "msg": "Invalid JSON",
                    "type": "value_error.jsondecode",
                }
            ]
        ) from e

    user = authenticate_user(db, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, refresh_token = issue_token_pair_for_user(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/token",
    response_model=Token,
    summary="Se connecter (OAuth2 Form)",
    description="Endpoint compatible OAuth2 (form-data) pour Swagger UI.",
    responses={401: RESPONSES_401, 422: RESPONSES_422, 500: RESPONSES_500},
)
def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    # OAuth2 spec uses 'username', we map it to email
    payload = LoginRequest(email=form_data.username, password=form_data.password)
    user = authenticate_user(db, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, refresh_token = issue_token_pair_for_user(db, user)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/firebase",
    response_model=Token,
    summary="Se connecter via Firebase",
    description="Valide un Firebase ID token et renvoie un couple access/refresh.",
    responses={401: RESPONSES_401, 422: RESPONSES_422, 500: RESPONSES_500},
)
def login_firebase(payload: FirebaseLoginRequest, db: Session = Depends(get_db)) -> Token:
    try:
        user = authenticate_firebase_user(db, id_token=payload.id_token)
    except ValueError as e:
        detail = str(e) or "Invalid Firebase token"
        if detail == "Firebase auth disabled" or detail == "Firebase auth not available":
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
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
