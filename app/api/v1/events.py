from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EvenementCreate, EvenementRead
from app.services.events import create_evenement, get_evenement, list_evenements

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EvenementRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EvenementCreate, db: Session = Depends(get_db)) -> EvenementRead:
    return create_evenement(db, payload)


@router.get("", response_model=list[EvenementRead])
def list_events(
    limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
) -> list[EvenementRead]:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    return list_evenements(db, limit=limit, offset=offset)


@router.get("/{event_id}", response_model=EvenementRead)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)) -> EvenementRead:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return evenement

