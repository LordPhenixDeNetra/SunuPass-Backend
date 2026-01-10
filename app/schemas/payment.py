from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import PaymentStatus


class PaiementCreate(BaseModel):
    billet_id: uuid.UUID
    montant: Decimal
    moyen: str


class PaiementUpdate(BaseModel):
    statut: PaymentStatus | None = None
    date_paiement: datetime | None = None


class PaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    billet_id: uuid.UUID
    montant: Decimal
    moyen: str
    statut: PaymentStatus
    date_paiement: datetime | None
    created_at: datetime
    updated_at: datetime
