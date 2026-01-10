from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Billet
from app.schemas.ticket import BilletCreate, BilletUpdate
from app.services.pagination import paginate


def create_billet(db: Session, payload: BilletCreate) -> Billet:
    ticket = Billet(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_billet(db: Session, billet_id: uuid.UUID) -> Billet | None:
    return db.get(Billet, billet_id)


def list_billets_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    evenement_id: uuid.UUID | None = None,
    participant_id: uuid.UUID | None = None,
) -> tuple[list[Billet], int]:
    stmt = select(Billet).order_by(Billet.created_at.desc())
    if evenement_id is not None:
        stmt = stmt.where(Billet.evenement_id == evenement_id)
    if participant_id is not None:
        stmt = stmt.where(Billet.participant_id == participant_id)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_billet(db: Session, billet: Billet, payload: BilletUpdate) -> Billet:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(billet, key, value)
    db.add(billet)
    db.commit()
    db.refresh(billet)
    return billet


def delete_billet(db: Session, billet: Billet) -> None:
    db.delete(billet)
    db.commit()

