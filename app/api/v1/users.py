from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import Utilisateur
from app.schemas.pagination import Page
from app.schemas.user import UtilisateurRead, UtilisateurUpdate
from app.services.users import (
    delete_utilisateur,
    get_utilisateur,
    list_utilisateurs_paginated,
    update_utilisateur,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UtilisateurRead)
def read_me(user: Utilisateur = Depends(get_current_user)) -> UtilisateurRead:
    return user


@router.patch("/me", response_model=UtilisateurRead)
def update_me(
    payload: UtilisateurUpdate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> UtilisateurRead:
    payload = UtilisateurUpdate(nom_complet=payload.nom_complet)
    return update_utilisateur(db, user, payload)


@router.get("", response_model=Page[UtilisateurRead])
def list_users(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> Page[UtilisateurRead]:
    items, total = list_utilisateurs_paginated(db, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UtilisateurRead)
def read_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> UtilisateurRead:
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = get_utilisateur(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> None:
    user = get_utilisateur(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    delete_utilisateur(db, user)

