from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TicketScanRequest(BaseModel):
    qr_code: str = Field(..., description="Valeur du QR code.", examples=["QR-..."])
    evenement_id: uuid.UUID | None = Field(default=None, description="Optionnel: vérifier l’événement.")


class TicketScanResponse(BaseModel):
    result: str
    billet_id: uuid.UUID | None
    ticket_status: str | None
    scanned_at: datetime | None

