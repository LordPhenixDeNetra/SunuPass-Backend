from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketStatus


class BilletCreate(BaseModel):
    evenement_id: uuid.UUID = Field(..., description="ID de l’événement.")
    participant_id: uuid.UUID = Field(..., description="ID du participant (utilisateur).")
    type: str = Field(..., description="Type de billet (ex: STANDARD, VIP).", examples=["STANDARD"])
    prix: Decimal = Field(..., ge=0, description="Prix du billet.", examples=["5000.00"])
    qr_code: str | None = Field(default=None, description="Code QR du billet (optionnel).")


class BilletUpdate(BaseModel):
    type: str | None = Field(default=None, description="Type de billet.")
    prix: Decimal | None = Field(default=None, ge=0, description="Prix du billet.")
    qr_code: str | None = Field(default=None, description="Code QR du billet.")
    statut: TicketStatus | None = Field(default=None, description="Statut du billet.")


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
