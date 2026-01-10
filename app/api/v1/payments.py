from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import Utilisateur
from app.schemas.pagination import Page
from app.schemas.payment import PaiementCreate, PaiementRead, PaiementUpdate
from app.services.payments import (
    create_paiement,
    delete_paiement,
    get_paiement,
    list_paiements_paginated,
    update_paiement,
)

router = APIRouter(prefix="/payments", tags=["payments"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaiementCreate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> PaiementRead:
    return create_paiement(db, payload)


@router.get("", response_model=Page[PaiementRead])
def list_payments(
    limit: int = 50,
    offset: int = 0,
    billet_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> Page[PaiementRead]:
    items, total = list_paiements_paginated(db, limit=limit, offset=offset, billet_id=billet_id)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{payment_id}", response_model=PaiementRead)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> PaiementRead:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return paiement


@router.patch("/{payment_id}", response_model=PaiementRead)
def patch_payment(
    payment_id: uuid.UUID,
    payload: PaiementUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> PaiementRead:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return update_paiement(db, paiement, payload)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_roles(UserRole.ADMIN)),
) -> None:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    delete_paiement(db, paiement)

