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

