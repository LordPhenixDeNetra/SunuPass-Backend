from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.user import Admin, Utilisateur
from app.schemas.pagination import Page
from app.schemas.payment import PaiementCreate, PaiementRead, PaiementUpdate
from app.services.payments import (
    create_paiement,
    delete_paiement,
    get_paiement,
    refund_paiement,
    list_paiements_paginated,
    update_paiement,
)

router = APIRouter(prefix="/payments", tags=["payments"], dependencies=[Depends(get_current_user)])


@router.post(
    "",
    response_model=PaiementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un paiement",
    description="Crée un paiement pour un billet (ADMIN uniquement).",
    responses=AUTHZ_ERRORS,
)
def create_payment(
    payload: PaiementCreate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> PaiementRead:
    return create_paiement(db, payload)


@router.get(
    "",
    response_model=Page[PaiementRead],
    summary="Lister les paiements",
    description="Liste paginée des paiements (ADMIN uniquement).",
    responses=AUTHZ_ERRORS,
)
def list_payments(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    billet_id: uuid.UUID | None = Query(None, description="Filtrer par billet"),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> Page[PaiementRead]:
    items, total = list_paiements_paginated(db, limit=limit, offset=offset, billet_id=billet_id)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{payment_id}",
    response_model=PaiementRead,
    summary="Lire un paiement",
    description="Retourne un paiement (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def get_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> PaiementRead:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return paiement


@router.patch(
    "/{payment_id}",
    response_model=PaiementRead,
    summary="Modifier un paiement",
    description="Modifie un paiement (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_payment(
    payment_id: uuid.UUID,
    payload: PaiementUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> PaiementRead:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return update_paiement(db, paiement, payload)


@router.post(
    "/{payment_id}/refund",
    response_model=PaiementRead,
    summary="Rembourser un paiement",
    description="Déclenche le remboursement d'un paiement (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def refund_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> PaiementRead:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return refund_paiement(db, paiement)


@router.delete(
    "/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un paiement",
    description="Supprime un paiement (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def remove_payment(
    payment_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    paiement = get_paiement(db, payment_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    delete_paiement(db, paiement)
