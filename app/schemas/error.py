from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str = Field(..., description="Code d’erreur stable pour le frontend.")
    message: str = Field(..., description="Message lisible décrivant l’erreur.")
    details: Any | None = Field(default=None, description="Détails additionnels (optionnel).")
    request_id: str | None = Field(default=None, description="Identifiant de requête si disponible.")

