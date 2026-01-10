from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TicketStatus


class Billet(Base):
    __tablename__ = "billets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evenement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evenements.id"), nullable=False)
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    prix: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    qr_code: Mapped[str | None] = mapped_column(Text, unique=True)
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
    participant: Mapped["Utilisateur"] = relationship(back_populates="billets")
    paiement: Mapped[Optional["Paiement"]] = relationship(back_populates="billet", uselist=False)
