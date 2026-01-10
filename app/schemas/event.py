from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EventStatus


class EvenementCreate(BaseModel):
    organisateur_id: uuid.UUID
    titre: str
    description: str | None = None
    date_debut: datetime
    lieu: str | None = None
    capacite: int


class EvenementUpdate(BaseModel):
    organisateur_id: uuid.UUID | None = None
    titre: str | None = None
    description: str | None = None
    date_debut: datetime | None = None
    lieu: str | None = None
    capacite: int | None = None
    statut: EventStatus | None = None


class EvenementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisateur_id: uuid.UUID
    titre: str
    description: str | None
    date_debut: datetime
    lieu: str | None
    capacite: int
    statut: EventStatus
    created_at: datetime
