from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import Utilisateur
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


@router.post("", response_model=BilletRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: BilletCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> BilletRead:
    if user.role != UserRole.ADMIN and payload.participant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return create_billet(db, payload)


@router.get("", response_model=Page[BilletRead])
def list_tickets(
    limit: int = 50,
    offset: int = 0,
    evenement_id: uuid.UUID | None = None,
    participant_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Page[BilletRead]:
    if user.role != UserRole.ADMIN:
        participant_id = user.id
    items, total = list_billets_paginated(
        db, limit=limit, offset=offset, evenement_id=evenement_id, participant_id=participant_id
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{ticket_id}", response_model=BilletRead)
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> BilletRead:
    billet = get_billet(db, ticket_id)
    if billet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if user.role != UserRole.ADMIN and billet.participant_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return billet


@router.patch("/{ticket_id}", response_model=BilletRead)
def patch_ticket(
    ticket_id: uuid.UUID,
    payload: BilletUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> BilletRead:
    billet = get_billet(db, ticket_id)
    if billet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return update_billet(db, billet, payload)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> None:
    billet = get_billet(db, ticket_id)
    if billet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    delete_billet(db, billet)

