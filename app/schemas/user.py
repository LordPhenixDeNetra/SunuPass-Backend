from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UtilisateurCreate(BaseModel):
    email: str = Field(..., description="Email unique de l’utilisateur.", examples=["participant1@sunupass.local"])
    nom_complet: str | None = Field(default=None, description="Nom complet affiché.")
    role: UserRole = Field(default=UserRole.PARTICIPANT, description="Rôle de l’utilisateur.")


class UtilisateurRegister(BaseModel):
    email: str = Field(..., description="Email unique de l’utilisateur.", examples=["test@sunupass.local"])
    password: str = Field(..., description="Mot de passe en clair (sera hashé côté API).", examples=["Test123!"])
    nom_complet: str | None = Field(default=None, description="Nom complet affiché.")


class UtilisateurUpdate(BaseModel):
    nom_complet: str | None = Field(default=None, description="Nom complet affiché.")
    role: UserRole | None = Field(default=None, description="Rôle (ADMIN uniquement).")
    is_active: bool | None = Field(default=None, description="Activation du compte (ADMIN uniquement).")


class UtilisateurRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str = Field(..., description="Email de l’utilisateur.")
    nom_complet: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
