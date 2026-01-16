from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Evenement, EventSession
from app.schemas.event import EvenementCreate, EvenementUpdate, EventSessionCreate, EventSessionUpdate
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


def create_event_session(db: Session, *, evenement: Evenement, payload: EventSessionCreate) -> EventSession:
    if payload.ends_at <= payload.starts_at:
        raise ValueError("ends_at must be greater than starts_at")
    session = EventSession(evenement_id=evenement.id, **payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_event_sessions(db: Session, *, evenement_id: uuid.UUID) -> list[EventSession]:
    stmt = (
        select(EventSession)
        .where(EventSession.evenement_id == evenement_id)
        .order_by(EventSession.starts_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_event_session(db: Session, session_id: uuid.UUID) -> EventSession | None:
    return db.get(EventSession, session_id)


def update_event_session(db: Session, session: EventSession, payload: EventSessionUpdate) -> EventSession:
    data = payload.model_dump(exclude_unset=True)
    if "starts_at" in data or "ends_at" in data:
        starts_at = data.get("starts_at", session.starts_at)
        ends_at = data.get("ends_at", session.ends_at)
        if ends_at <= starts_at:
            raise ValueError("ends_at must be greater than starts_at")
    for key, value in data.items():
        setattr(session, key, value)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_event_session(db: Session, session: EventSession) -> None:
    db.delete(session)
    db.commit()
