from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import Utilisateur
from app.schemas.event import EvenementCreate, EvenementRead, EvenementUpdate
from app.schemas.pagination import Page
from app.services.events import (
    create_evenement,
    delete_evenement,
    get_evenement,
    list_evenements_paginated,
    update_evenement,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EvenementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un événement",
    description="Crée un événement (ADMIN/ORGANISATEUR). Un organisateur ne peut créer que pour lui-même.",
)
def create_event(
    payload: EvenementCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> EvenementRead:
    if user.role != UserRole.ADMIN and payload.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return create_evenement(db, payload)


@router.get(
    "",
    response_model=Page[EvenementRead],
    summary="Lister les événements",
    description="Liste paginée. ADMIN voit tout, ORGANISATEUR voit uniquement ses événements.",
)
def list_events(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Page[EvenementRead]:
    organisateur_id = user.id if user.role == UserRole.ORGANISATEUR else None
    items, total = list_evenements_paginated(
        db, limit=limit, offset=offset, organisateur_id=organisateur_id
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{event_id}",
    response_model=EvenementRead,
    summary="Lire un événement",
    description="Retourne un événement. Un organisateur ne peut accéder qu’à ses événements.",
)
def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> EvenementRead:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if user.role == UserRole.ORGANISATEUR and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return evenement


@router.patch(
    "/{event_id}",
    response_model=EvenementRead,
    summary="Modifier un événement",
    description="Modifie un événement (organisateur propriétaire ou ADMIN).",
)
def patch_event(
    event_id: uuid.UUID,
    payload: EvenementUpdate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> EvenementRead:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if user.role == UserRole.ORGANISATEUR and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return update_evenement(db, evenement, payload)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un événement",
    description="Supprime un événement (organisateur propriétaire ou ADMIN).",
)
def remove_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> None:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if user.role == UserRole.ORGANISATEUR and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    delete_evenement(db, evenement)
