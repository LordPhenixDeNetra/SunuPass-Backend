from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CountryCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, description="Code ISO alpha-3 du pays.", examples=["SEN"])
    name: str = Field(..., description="Nom du pays.", examples=["Sénégal"])
    calling_code: str = Field(..., description="Indicatif téléphonique du pays.", examples=["+221"])
    flag_svg: str | None = Field(default=None, description="SVG du drapeau (markup).")


class CountryUpdate(BaseModel):
    name: str | None = Field(default=None, description="Nom du pays.")
    calling_code: str | None = Field(default=None, description="Indicatif téléphonique du pays.")
    flag_svg: str | None = Field(default=None, description="SVG du drapeau (markup).")


class CountryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    calling_code: str
    flag_svg: str | None


class AdministrativeLevelCreate(BaseModel):
    name: str = Field(..., description="Nom du niveau administratif.", examples=["Région"])
    level_order: int = Field(..., ge=1, description="Ordre du niveau dans la hiérarchie (1 = plus grand).", examples=[1])
    country_code: str = Field(..., min_length=3, max_length=3, description="Code ISO alpha-3 du pays.", examples=["SEN"])


class AdministrativeLevelUpdate(BaseModel):
    name: str | None = Field(default=None, description="Nom du niveau administratif.")
    level_order: int | None = Field(default=None, ge=1, description="Ordre du niveau dans la hiérarchie (1 = plus grand).")


class AdministrativeLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    level_order: int
    country_code: str


class AdministrativeUnitCreate(BaseModel):
    name: str = Field(..., description="Nom officiel de l'unité administrative.", examples=["Commune Médina"])
    code: str | None = Field(default=None, description="Code administratif officiel.")
    latitude: Decimal | None = Field(default=None, description="Latitude GPS.")
    longitude: Decimal | None = Field(default=None, description="Longitude GPS.")
    level_id: uuid.UUID = Field(..., description="ID du niveau administratif.")
    parent_id: uuid.UUID | None = Field(default=None, description="ID de l'unité administrative parente.")


class AdministrativeUnitUpdate(BaseModel):
    name: str | None = Field(default=None, description="Nom officiel de l'unité administrative.")
    code: str | None = Field(default=None, description="Code administratif officiel.")
    latitude: Decimal | None = Field(default=None, description="Latitude GPS.")
    longitude: Decimal | None = Field(default=None, description="Longitude GPS.")
    level_id: uuid.UUID | None = Field(default=None, description="ID du niveau administratif.")
    parent_id: uuid.UUID | None = Field(default=None, description="ID de l'unité administrative parente.")


class AdministrativeUnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    level_id: uuid.UUID
    parent_id: uuid.UUID | None
