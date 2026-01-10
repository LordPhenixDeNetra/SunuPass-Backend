from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PaymentStatus


class Paiement(Base):
    __tablename__ = "paiements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    billet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("billets.id"), unique=True, nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    moyen: Mapped[str] = mapped_column(String(50), nullable=False)
    statut: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.EN_ATTENTE,
        nullable=False,
    )
    date_paiement: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    billet: Mapped["Billet"] = relationship(back_populates="paiement")
