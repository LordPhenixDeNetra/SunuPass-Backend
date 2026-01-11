from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PromoDiscountType


class PromoCodeCreate(BaseModel):
    code: str = Field(..., description="Code promo unique dans l’événement.", examples=["EARLY10"])
    discount_type: PromoDiscountType = Field(..., description="Type de réduction.")
    value: Decimal = Field(..., ge=0, description="Valeur (pourcentage ou montant).", examples=["10.00"])
    starts_at: datetime | None = Field(default=None, description="Début de validité (ISO 8601).")
    ends_at: datetime | None = Field(default=None, description="Fin de validité (ISO 8601).")
    usage_limit: int | None = Field(default=None, ge=1, description="Limite totale d’utilisations.")
    is_active: bool = Field(default=True, description="Actif/inactif.")


class PromoCodeUpdate(BaseModel):
    code: str | None = Field(default=None, description="Code promo unique dans l’événement.")
    discount_type: PromoDiscountType | None = Field(default=None, description="Type de réduction.")
    value: Decimal | None = Field(default=None, ge=0, description="Valeur (pourcentage ou montant).")
    starts_at: datetime | None = Field(default=None, description="Début de validité (ISO 8601).")
    ends_at: datetime | None = Field(default=None, description="Fin de validité (ISO 8601).")
    usage_limit: int | None = Field(default=None, ge=1, description="Limite totale d’utilisations.")
    is_active: bool | None = Field(default=None, description="Actif/inactif.")


class PromoCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evenement_id: uuid.UUID
    code: str
    discount_type: PromoDiscountType
    value: Decimal
    starts_at: datetime | None
    ends_at: datetime | None
    usage_limit: int | None
    used_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

