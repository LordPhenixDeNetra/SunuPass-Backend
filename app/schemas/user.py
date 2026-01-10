from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UtilisateurCreate(BaseModel):
    email: str
    nom_complet: str | None = None
    role: UserRole = UserRole.PARTICIPANT


class UtilisateurUpdate(BaseModel):
    nom_complet: str | None = None
    role: UserRole | None = None


class UtilisateurRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    nom_complet: str | None
    role: UserRole
    created_at: datetime

