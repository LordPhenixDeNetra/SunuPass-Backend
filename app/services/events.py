from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.event import Evenement
from app.schemas.event import EvenementCreate


def create_evenement(db: Session, payload: EvenementCreate) -> Evenement:
    evenement = Evenement(**payload.model_dump())
    db.add(evenement)
    db.commit()
    db.refresh(evenement)
    return evenement


def get_evenement(db: Session, evenement_id: uuid.UUID) -> Evenement | None:
    return db.get(Evenement, evenement_id)


def list_evenements(db: Session, limit: int = 50, offset: int = 0) -> list[Evenement]:
    return (
        db.query(Evenement)
        .order_by(Evenement.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

