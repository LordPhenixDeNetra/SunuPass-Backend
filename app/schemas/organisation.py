from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrganisationCreate(BaseModel):
    nom_organisation: str = Field(..., description="Nom de l'organisation.", examples=["SunuPass SARL"])
    nb_employes_min: int = Field(..., ge=0, description="Nombre minimum d'employés.", examples=[5])
    nb_employes_max: int = Field(..., ge=0, description="Nombre maximum d'employés.", examples=[25])
    pays_code: str = Field(..., min_length=3, max_length=3, description="Code ISO alpha-3 du pays.", examples=["SEN"])
    email: str = Field(..., description="Email de contact.", examples=["contact@sunupass.sn"])
    telephone: str = Field(..., description="Téléphone de contact.", examples=["+221771234567"])

    @model_validator(mode="after")
    def _check_nb_employes_range(self) -> "OrganisationCreate":
        if self.nb_employes_min > self.nb_employes_max:
            raise ValueError("nb_employes_min must be <= nb_employes_max")
        return self


class OrganisationUpdate(BaseModel):
    nom_organisation: str | None = Field(default=None, description="Nom de l'organisation.")
    nb_employes_min: int | None = Field(default=None, ge=0, description="Nombre minimum d'employés.")
    nb_employes_max: int | None = Field(default=None, ge=0, description="Nombre maximum d'employés.")
    pays_code: str | None = Field(default=None, min_length=3, max_length=3, description="Code ISO alpha-3 du pays.")
    email: str | None = Field(default=None, description="Email de contact.")
    telephone: str | None = Field(default=None, description="Téléphone de contact.")

    @model_validator(mode="after")
    def _check_nb_employes_range(self) -> "OrganisationUpdate":
        if self.nb_employes_min is None and self.nb_employes_max is None:
            return self
        if self.nb_employes_min is None or self.nb_employes_max is None:
            return self
        if self.nb_employes_min > self.nb_employes_max:
            raise ValueError("nb_employes_min must be <= nb_employes_max")
        return self


class OrganisationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nom_organisation: str
    nb_employes_min: int
    nb_employes_max: int
    pays_code: str
    email: str
    telephone: str

