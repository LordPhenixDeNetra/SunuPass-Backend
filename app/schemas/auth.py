from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="JWT d’accès à mettre dans Authorization: Bearer <token>.")
    refresh_token: str | None = Field(
        default=None,
        description="JWT de refresh utilisé pour obtenir un nouveau couple de tokens.",
    )
    token_type: str = Field(default="bearer", description="Type du token pour l’en-tête Authorization.")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email de connexion.", examples=["admin@sunupass.local"])
    password: str = Field(..., description="Mot de passe en clair (sera vérifié côté API).", examples=["Admin123!"])


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token obtenu au login.")
