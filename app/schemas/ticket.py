from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import TicketStatus


class BilletCreate(BaseModel):
    evenement_id: uuid.UUID
    participant_id: uuid.UUID
    type: str
    prix: Decimal
    qr_code: str | None = None


class BilletUpdate(BaseModel):
    type: str | None = None
    prix: Decimal | None = None
    qr_code: str | None = None
    statut: TicketStatus | None = None


class BilletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evenement_id: uuid.UUID
    participant_id: uuid.UUID
    type: str
    prix: Decimal
    qr_code: str | None
    statut: TicketStatus
    created_at: datetime
    updated_at: datetime
