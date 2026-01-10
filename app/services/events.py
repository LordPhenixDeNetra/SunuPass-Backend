from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Evenement
from app.schemas.event import EvenementCreate, EvenementUpdate
from app.services.pagination import paginate


def create_evenement(db: Session, payload: EvenementCreate) -> Evenement:
    evenement = Evenement(**payload.model_dump())
    db.add(evenement)
    db.commit()
    db.refresh(evenement)
    return evenement


def get_evenement(db: Session, evenement_id: uuid.UUID) -> Evenement | None:
    return db.get(Evenement, evenement_id)


def list_evenements_paginated(
    db: Session, *, limit: int = 50, offset: int = 0, organisateur_id: uuid.UUID | None = None
) -> tuple[list[Evenement], int]:
    stmt = select(Evenement).order_by(Evenement.created_at.desc())
    if organisateur_id is not None:
        stmt = stmt.where(Evenement.organisateur_id == organisateur_id)
    return paginate(db, stmt, limit=limit, offset=offset)


def list_evenements(db: Session, limit: int = 50, offset: int = 0) -> list[Evenement]:
    items, _total = list_evenements_paginated(db, limit=limit, offset=offset)
    return items


def update_evenement(db: Session, evenement: Evenement, payload: EvenementUpdate) -> Evenement:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(evenement, key, value)
    db.add(evenement)
    db.commit()
    db.refresh(evenement)
    return evenement


def delete_evenement(db: Session, evenement: Evenement) -> None:
    db.delete(evenement)
    db.commit()
