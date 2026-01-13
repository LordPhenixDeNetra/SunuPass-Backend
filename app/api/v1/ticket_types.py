from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.event import Evenement
from app.models.ticket_type import TicketType
from app.models.user import Admin, Organisateur, Utilisateur
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeRead, TicketTypeUpdate
from app.services.ticket_types import (
    create_ticket_type,
    delete_ticket_type,
    get_ticket_type,
    list_ticket_types,
    update_ticket_type,
)

router = APIRouter(prefix="/events/{event_id}/ticket-types", tags=["ticket-types"])


def _get_event(db: Session, event_id: uuid.UUID) -> Evenement:
    evt = db.get(Evenement, event_id)
    if evt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return evt


def _require_owner_or_admin(user: Utilisateur, evt: Evenement) -> None:
    if not isinstance(user, Admin) and evt.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get(
    "",
    response_model=list[TicketTypeRead],
    summary="Lister les types de billets",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def list_types(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> list[TicketType]:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    return list_ticket_types(db, evenement_id=event_id)


@router.post(
    "",
    response_model=TicketTypeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un type de billet",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def create_type(
    event_id: uuid.UUID,
    payload: TicketTypeCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> TicketType:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    try:
        return create_ticket_type(db, evenement_id=event_id, payload=payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ticket type")


@router.patch(
    "/{ticket_type_id}",
    response_model=TicketTypeRead,
    summary="Modifier un type de billet",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_type(
    event_id: uuid.UUID,
    ticket_type_id: uuid.UUID,
    payload: TicketTypeUpdate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> TicketType:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    row = get_ticket_type(db, ticket_type_id)
    if row is None or row.evenement_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket type not found")
    return update_ticket_type(db, row, payload)


@router.delete(
    "/{ticket_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un type de billet",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def remove_type(
    event_id: uuid.UUID,
    ticket_type_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> None:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    row = get_ticket_type(db, ticket_type_id)
    if row is None or row.evenement_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket type not found")
    delete_ticket_type(db, row)
