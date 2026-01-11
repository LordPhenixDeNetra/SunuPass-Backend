from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket_type import TicketType
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate


def create_ticket_type(db: Session, *, evenement_id: uuid.UUID, payload: TicketTypeCreate) -> TicketType:
    row = TicketType(evenement_id=evenement_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_ticket_type(db: Session, ticket_type_id: uuid.UUID) -> TicketType | None:
    return db.get(TicketType, ticket_type_id)


def list_ticket_types(db: Session, *, evenement_id: uuid.UUID) -> list[TicketType]:
    stmt = select(TicketType).where(TicketType.evenement_id == evenement_id).order_by(TicketType.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def update_ticket_type(db: Session, row: TicketType, payload: TicketTypeUpdate) -> TicketType:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_ticket_type(db: Session, row: TicketType) -> None:
    db.delete(row)
    db.commit()

