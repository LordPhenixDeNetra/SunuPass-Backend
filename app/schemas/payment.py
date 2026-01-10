from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentStatus


class PaiementCreate(BaseModel):
    billet_id: uuid.UUID = Field(..., description="ID du billet à payer.")
    montant: Decimal = Field(..., ge=0, description="Montant du paiement.", examples=["3000.00"])
    moyen: str = Field(..., description="Moyen de paiement (ex: OM, WAVE, CASH).", examples=["OM"])


class PaiementUpdate(BaseModel):
    statut: PaymentStatus | None = Field(default=None, description="Statut du paiement.")
    date_paiement: datetime | None = Field(default=None, description="Date/heure du paiement (ISO 8601).")


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
