from __future__ import annotations

from app.schemas.event import EvenementCreate, EvenementRead, EvenementUpdate
from app.schemas.auth import LoginRequest, Token
from app.schemas.geography import (
    AdministrativeLevelCreate,
    AdministrativeLevelRead,
    AdministrativeLevelUpdate,
    AdministrativeUnitCreate,
    AdministrativeUnitRead,
    AdministrativeUnitUpdate,
    CountryCreate,
    CountryRead,
    CountryUpdate,
)
from app.schemas.organisation import OrganisationCreate, OrganisationRead, OrganisationUpdate
from app.schemas.pagination import Page
from app.schemas.payment import PaiementCreate, PaiementRead, PaiementUpdate
from app.schemas.ticket import BilletCreate, BilletRead, BilletUpdate
from app.schemas.user import UtilisateurCreate, UtilisateurRead, UtilisateurRegister, UtilisateurUpdate

__all__ = [
    "AdministrativeLevelCreate",
    "AdministrativeLevelRead",
    "AdministrativeLevelUpdate",
    "AdministrativeUnitCreate",
    "AdministrativeUnitRead",
    "AdministrativeUnitUpdate",
    "BilletCreate",
    "BilletRead",
    "BilletUpdate",
    "CountryCreate",
    "CountryRead",
    "CountryUpdate",
    "EvenementCreate",
    "EvenementRead",
    "EvenementUpdate",
    "LoginRequest",
    "OrganisationCreate",
    "OrganisationRead",
    "OrganisationUpdate",
    "Page",
    "PaiementCreate",
    "PaiementRead",
    "PaiementUpdate",
    "Token",
    "UtilisateurCreate",
    "UtilisateurRead",
    "UtilisateurRegister",
    "UtilisateurUpdate",
]
