from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EventStatus


class Evenement(Base):
    __tablename__ = "evenements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organisateur_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False)
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    date_debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lieu: Mapped[str | None] = mapped_column(String(150))
    capacite: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus, name="event_status"),
        default=EventStatus.BROUILLON,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organisateur: Mapped["Utilisateur"] = relationship(back_populates="evenements")
    billets: Mapped[list["Billet"]] = relationship(back_populates="evenement")
