from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Paiement
from app.schemas.payment import PaiementCreate, PaiementUpdate
from app.services.pagination import paginate


def create_paiement(db: Session, payload: PaiementCreate) -> Paiement:
    paiement = Paiement(**payload.model_dump())
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement


def get_paiement(db: Session, paiement_id: uuid.UUID) -> Paiement | None:
    return db.get(Paiement, paiement_id)


def get_paiement_by_billet(db: Session, billet_id: uuid.UUID) -> Paiement | None:
    stmt = select(Paiement).where(Paiement.billet_id == billet_id)
    return db.execute(stmt).scalar_one_or_none()


def list_paiements_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    billet_id: uuid.UUID | None = None,
) -> tuple[list[Paiement], int]:
    stmt = select(Paiement).order_by(Paiement.date_paiement.desc().nullslast())
    if billet_id is not None:
        stmt = stmt.where(Paiement.billet_id == billet_id)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_paiement(db: Session, paiement: Paiement, payload: PaiementUpdate) -> Paiement:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(paiement, key, value)
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement


def delete_paiement(db: Session, paiement: Paiement) -> None:
    db.delete(paiement)
    db.commit()

