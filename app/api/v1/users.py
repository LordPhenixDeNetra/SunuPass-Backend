from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.user import Admin, Utilisateur
from app.schemas.pagination import Page
from app.schemas.user import UtilisateurRead, UtilisateurUpdate
from app.services.users import (
    delete_utilisateur,
    get_utilisateur,
    list_utilisateurs_paginated,
    update_utilisateur,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UtilisateurRead,
    summary="Lire mon profil",
    description="Retourne le profil de l’utilisateur authentifié.",
    responses=AUTHZ_ERRORS,
)
def read_me(user: Utilisateur = Depends(get_current_user)) -> UtilisateurRead:
    return user


@router.patch(
    "/me",
    response_model=UtilisateurRead,
    summary="Mettre à jour mon profil",
    description="Met à jour les informations du profil de l’utilisateur authentifié.",
    responses=AUTHZ_ERRORS,
)
def update_me(
    payload: UtilisateurUpdate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> UtilisateurRead:
    payload = UtilisateurUpdate(nom_complet=payload.nom_complet)
    try:
        return update_utilisateur(db, user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=Page[UtilisateurRead],
    summary="Lister les utilisateurs",
    description="Liste paginée des utilisateurs (ADMIN uniquement).",
    responses=AUTHZ_ERRORS,
)
def list_users(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> Page[UtilisateurRead]:
    items, total = list_utilisateurs_paginated(db, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{user_id}",
    response_model=UtilisateurRead,
    summary="Lire un utilisateur",
    description="ADMIN peut lire tout le monde, sinon uniquement son propre utilisateur.",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def read_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
) -> UtilisateurRead:
    if not isinstance(current_user, Admin) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    user = get_utilisateur(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un utilisateur",
    description="Supprime un utilisateur (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    user = get_utilisateur(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    delete_utilisateur(db, user)
