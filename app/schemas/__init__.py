from __future__ import annotations

from app.schemas.event import EvenementCreate, EvenementRead, EvenementUpdate
from app.schemas.auth import LoginRequest, Token
from app.schemas.pagination import Page
from app.schemas.payment import PaiementCreate, PaiementRead, PaiementUpdate
from app.schemas.ticket import BilletCreate, BilletRead, BilletUpdate
from app.schemas.user import UtilisateurCreate, UtilisateurRead, UtilisateurRegister, UtilisateurUpdate

__all__ = [
    "BilletCreate",
    "BilletRead",
    "BilletUpdate",
    "EvenementCreate",
    "EvenementRead",
    "EvenementUpdate",
    "LoginRequest",
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
