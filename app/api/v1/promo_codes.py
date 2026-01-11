from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.event import Evenement
from app.models.promo_code import PromoCode
from app.models.user import Utilisateur
from app.schemas.promo import PromoCodeCreate, PromoCodeRead, PromoCodeUpdate
from app.services.promo_codes import (
    create_promo_code,
    delete_promo_code,
    get_promo_code,
    list_promo_codes,
    update_promo_code,
)

router = APIRouter(prefix="/events/{event_id}/promo-codes", tags=["promo-codes"])


def _get_event(db: Session, event_id: uuid.UUID) -> Evenement:
    evt = db.get(Evenement, event_id)
    if evt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return evt


def _require_owner_or_admin(user: Utilisateur, evt: Evenement) -> None:
    if user.role != UserRole.ADMIN and evt.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get(
    "",
    response_model=list[PromoCodeRead],
    summary="Lister les codes promo",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def list_promos(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> list[PromoCode]:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    return list_promo_codes(db, evenement_id=event_id)


@router.post(
    "",
    response_model=PromoCodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un code promo",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def create_promo(
    event_id: uuid.UUID,
    payload: PromoCodeCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> PromoCode:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    try:
        return create_promo_code(db, evenement_id=event_id, payload=payload)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid promo code")


@router.patch(
    "/{promo_code_id}",
    response_model=PromoCodeRead,
    summary="Modifier un code promo",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_promo(
    event_id: uuid.UUID,
    promo_code_id: uuid.UUID,
    payload: PromoCodeUpdate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> PromoCode:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    row = get_promo_code(db, promo_code_id)
    if row is None or row.evenement_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")
    return update_promo_code(db, row, payload)


@router.delete(
    "/{promo_code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un code promo",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def remove_promo(
    event_id: uuid.UUID,
    promo_code_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.ORGANISATEUR)),
) -> None:
    evt = _get_event(db, event_id)
    _require_owner_or_admin(user, evt)
    row = get_promo_code(db, promo_code_id)
    if row is None or row.evenement_id != event_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")
    delete_promo_code(db, row)
