from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TicketTypeCreate(BaseModel):
    code: str = Field(..., description="Code court unique dans l’événement.", examples=["VIP"])
    label: str = Field(..., description="Nom affiché.", examples=["Pass VIP"])
    prix: Decimal = Field(..., ge=0, description="Prix du type de billet.", examples=["15000.00"])
    quota: int = Field(..., ge=0, description="Quota maximum (0 = illimité).", examples=[100])
    sales_start: datetime | None = Field(default=None, description="Début de vente (ISO 8601).")
    sales_end: datetime | None = Field(default=None, description="Fin de vente (ISO 8601).")
    is_active: bool = Field(default=True, description="Actif/inactif.")


class TicketTypeUpdate(BaseModel):
    code: str | None = Field(default=None, description="Code court unique dans l’événement.")
    label: str | None = Field(default=None, description="Nom affiché.")
    prix: Decimal | None = Field(default=None, ge=0, description="Prix du type de billet.")
    quota: int | None = Field(default=None, ge=0, description="Quota maximum (0 = illimité).")
    sales_start: datetime | None = Field(default=None, description="Début de vente (ISO 8601).")
    sales_end: datetime | None = Field(default=None, description="Fin de vente (ISO 8601).")
    is_active: bool | None = Field(default=None, description="Actif/inactif.")


class TicketTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evenement_id: uuid.UUID
    code: str
    label: str
    prix: Decimal
    quota: int
    sales_start: datetime | None
    sales_end: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

