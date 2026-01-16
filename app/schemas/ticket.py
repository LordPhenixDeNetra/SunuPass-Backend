from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TicketStatus


class BilletCreate(BaseModel):
    evenement_id: uuid.UUID = Field(..., description="ID de l’événement.")
    participant_id: uuid.UUID = Field(..., description="ID du participant (utilisateur).")
    ticket_type_id: uuid.UUID | None = Field(default=None, description="ID du type de billet (recommandé).")
    type: str | None = Field(default=None, description="Type de billet (ex: STANDARD, VIP).", examples=["STANDARD"])
    prix: Decimal | None = Field(default=None, ge=0, description="Prix du billet.", examples=["5000.00"])
    promo_code: str | None = Field(default=None, description="Code promo à appliquer (optionnel).", examples=["EARLY10"])
    qr_code: str | None = Field(default=None, description="Code QR du billet (optionnel).")
    session_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Optionnel: sessions (jours/créneaux) achetées. Par défaut: toutes les sessions de l’événement.",
    )


class BilletGuestPurchase(BaseModel):
    evenement_id: uuid.UUID = Field(..., description="ID de l’événement.")
    ticket_type_id: uuid.UUID | None = Field(default=None, description="ID du type de billet (recommandé).")
    type: str | None = Field(default=None, description="Type de billet (ex: STANDARD, VIP).", examples=["STANDARD"])
    prix: Decimal | None = Field(default=None, ge=0, description="Prix du billet.", examples=["5000.00"])
    promo_code: str | None = Field(default=None, description="Code promo à appliquer (optionnel).", examples=["EARLY10"])
    guest_email: str = Field(..., description="Email du participant invité.", examples=["invite@example.com"])
    guest_nom_complet: str | None = Field(default=None, description="Nom complet de l’invité.", examples=["Awa Diop"])
    guest_phone: str | None = Field(default=None, description="Téléphone de l’invité.", examples=["+221770000000"])
    session_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Optionnel: sessions (jours/créneaux) achetées. Par défaut: toutes les sessions de l’événement.",
    )


class BilletUpdate(BaseModel):
    ticket_type_id: uuid.UUID | None = Field(default=None, description="ID du type de billet.")
    type: str | None = Field(default=None, description="Type de billet.")
    prix: Decimal | None = Field(default=None, ge=0, description="Prix du billet.")
    qr_code: str | None = Field(default=None, description="Code QR du billet.")
    statut: TicketStatus | None = Field(default=None, description="Statut du billet.")


class BilletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evenement_id: uuid.UUID
    participant_id: uuid.UUID | None
    guest_email: str | None
    guest_nom_complet: str | None
    guest_phone: str | None
    ticket_type_id: uuid.UUID | None
    type: str
    prix_initial: Decimal | None
    prix: Decimal
    qr_code: str | None
    promo_code_id: uuid.UUID | None
    statut: TicketStatus
    session_ids: list[uuid.UUID]
    created_at: datetime
    updated_at: datetime
