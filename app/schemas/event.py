from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EventStatus


class EventSessionCreate(BaseModel):
    starts_at: datetime = Field(..., description="Début de session (ISO 8601).")
    ends_at: datetime = Field(..., description="Fin de session (ISO 8601).")
    label: str | None = Field(default=None, description="Libellé optionnel.")
    day_index: int | None = Field(default=None, description="Index du jour (optionnel).")


class EventSessionUpdate(BaseModel):
    starts_at: datetime | None = Field(default=None, description="Début de session (ISO 8601).")
    ends_at: datetime | None = Field(default=None, description="Fin de session (ISO 8601).")
    label: str | None = Field(default=None, description="Libellé optionnel.")
    day_index: int | None = Field(default=None, description="Index du jour (optionnel).")


class EventSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evenement_id: uuid.UUID
    starts_at: datetime
    ends_at: datetime
    label: str | None
    day_index: int | None
    created_at: datetime
    updated_at: datetime


class EvenementCreate(BaseModel):
    organisateur_id: uuid.UUID = Field(..., description="ID de l’organisateur (utilisateur).")
    titre: str = Field(..., description="Titre de l’événement.", examples=["Festival SunuPass 2026"])
    description: str | None = Field(default=None, description="Description libre.")
    date_debut: datetime = Field(..., description="Date/heure de début (ISO 8601).")
    lieu: str | None = Field(default=None, description="Lieu de l’événement.", examples=["Dakar"])
    capacite: int = Field(..., ge=1, description="Capacité maximale (nombre de places).", examples=[500])
    branding_logo_url: str | None = Field(default=None, description="URL du logo pour le branding.")
    branding_primary_color: str | None = Field(default=None, description="Couleur principale (ex: #0ea5e9).")


class EvenementUpdate(BaseModel):
    organisateur_id: uuid.UUID | None = Field(default=None, description="Nouveau propriétaire (ADMIN uniquement).")
    titre: str | None = Field(default=None, description="Titre de l’événement.")
    description: str | None = Field(default=None, description="Description libre.")
    date_debut: datetime | None = Field(default=None, description="Date/heure de début (ISO 8601).")
    lieu: str | None = Field(default=None, description="Lieu de l’événement.")
    capacite: int | None = Field(default=None, ge=1, description="Capacité maximale.")
    branding_logo_url: str | None = Field(default=None, description="URL du logo pour le branding.")
    branding_primary_color: str | None = Field(default=None, description="Couleur principale (ex: #0ea5e9).")
    statut: EventStatus | None = Field(default=None, description="Statut de publication.")


class EvenementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organisateur_id: uuid.UUID
    titre: str
    description: str | None
    date_debut: datetime
    lieu: str | None
    capacite: int
    branding_logo_url: str | None
    branding_primary_color: str | None
    statut: EventStatus
    sessions: list[EventSessionRead]
    created_at: datetime
    updated_at: datetime
