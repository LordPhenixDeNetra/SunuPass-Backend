from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ORGANISATEUR = "ORGANISATEUR"
    PARTICIPANT = "PARTICIPANT"
    AGENT = "AGENT"


class EventStatus(str, enum.Enum):
    BROUILLON = "BROUILLON"
    PUBLIE = "PUBLIE"
    TERMINE = "TERMINE"


class TicketStatus(str, enum.Enum):
    CREE = "CREE"
    PAYE = "PAYE"
    UTILISE = "UTILISE"
    ANNULE = "ANNULE"


class PaymentStatus(str, enum.Enum):
    EN_ATTENTE = "EN_ATTENTE"
    SUCCES = "SUCCES"
    ECHEC = "ECHEC"
    REMBOURSE = "REMBOURSE"


class PromoDiscountType(str, enum.Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
