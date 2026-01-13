from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.user import Admin, Utilisateur
from app.schemas.pagination import Page
from app.schemas.ticket import BilletCreate, BilletRead, BilletUpdate
from app.services.tickets import (
    create_billet,
    delete_billet,
    get_billet,
    list_billets_paginated,
    update_billet,
)

router = APIRouter(prefix="/tickets", tags=["tickets"], dependencies=[Depends(get_current_user)])


@router.post(
    "",
    response_model=BilletRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un billet",
    description="Crée un billet (ADMIN ou le participant lui-même).",
    responses=AUTHZ_ERRORS,
)
def create_ticket(
    payload: BilletCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> BilletRead:
    if not isinstance(user, Admin) and payload.participant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        return create_billet(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=Page[BilletRead],
    summary="Lister les billets",
    description="Liste paginée. ADMIN peut filtrer, sinon retour uniquement sur ses billets.",
    responses=AUTHZ_ERRORS,
)
def list_tickets(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    evenement_id: uuid.UUID | None = Query(None, description="Filtrer par événement (ADMIN)"),
    participant_id: uuid.UUID | None = Query(None, description="Filtrer par participant (ADMIN)"),
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Page[BilletRead]:
    if not isinstance(user, Admin):
        participant_id = user.id
    items, total = list_billets_paginated(
        db, limit=limit, offset=offset, evenement_id=evenement_id, participant_id=participant_id
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{ticket_id}",
    response_model=BilletRead,
    summary="Lire un billet",
    description="Retourne un billet (ADMIN ou propriétaire).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> BilletRead:
    billet = get_billet(db, ticket_id)
    if billet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if not isinstance(user, Admin) and billet.participant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return billet


@router.patch(
    "/{ticket_id}",
    response_model=BilletRead,
    summary="Modifier un billet",
    description="Modifie un billet (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_ticket(
    ticket_id: uuid.UUID,
    payload: BilletUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> BilletRead:
    billet = get_billet(db, ticket_id)
    if billet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return update_billet(db, billet, payload)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un billet",
    description="Supprime un billet (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def remove_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    billet = get_billet(db, ticket_id)
    if billet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    delete_billet(db, billet)
