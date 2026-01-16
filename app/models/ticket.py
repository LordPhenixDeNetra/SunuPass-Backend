from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TicketStatus


billet_sessions = Table(
    "billet_sessions",
    Base.metadata,
    Column("billet_id", ForeignKey("billets.id", ondelete="CASCADE"), primary_key=True),
    Column("session_id", ForeignKey("event_sessions.id", ondelete="CASCADE"), primary_key=True),
)


class Billet(Base):
    __tablename__ = "billets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evenement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evenements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("utilisateurs.id"), nullable=True, index=True
    )
    guest_email: Mapped[str | None] = mapped_column(String(320))
    guest_nom_complet: Mapped[str | None] = mapped_column(String(200))
    guest_phone: Mapped[str | None] = mapped_column(String(50))
    ticket_type_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ticket_types.id"), index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    prix_initial: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    prix: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    qr_code: Mapped[str | None] = mapped_column(Text, unique=True)
    promo_code_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("promo_codes.id"), index=True)
    statut: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus, name="ticket_status"),
        default=TicketStatus.CREE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    evenement: Mapped["Evenement"] = relationship(back_populates="billets")
    participant: Mapped[Optional["Utilisateur"]] = relationship(back_populates="billets")
    paiement: Mapped[Optional["Paiement"]] = relationship(back_populates="billet", uselist=False)
    ticket_type: Mapped[Optional["TicketType"]] = relationship(back_populates="billets")
    promo_code: Mapped[Optional["PromoCode"]] = relationship(back_populates="billets")
    scans: Mapped[list["TicketScan"]] = relationship(back_populates="billet", cascade="all, delete-orphan")
    sessions: Mapped[list["EventSession"]] = relationship(
        "EventSession",
        secondary="billet_sessions",
        back_populates="billets",
    )

    @property
    def session_ids(self) -> list[uuid.UUID]:
        return [s.id for s in self.sessions]
