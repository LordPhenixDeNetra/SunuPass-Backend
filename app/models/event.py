from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EventStatus


evenement_agents = Table(
    "evenement_agents",
    Base.metadata,
    Column("evenement_id", ForeignKey("evenements.id", ondelete="CASCADE"), primary_key=True),
    Column("agent_id", ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
)


class Evenement(Base):
    __tablename__ = "evenements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organisateur_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("utilisateurs.id"), nullable=False, index=True
    )
    titre: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    date_debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lieu: Mapped[str | None] = mapped_column(String(150))
    capacite: Mapped[int] = mapped_column(Integer, nullable=False)
    branding_logo_url: Mapped[str | None] = mapped_column(String(500))
    branding_primary_color: Mapped[str | None] = mapped_column(String(20))
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
    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        secondary="evenement_agents",
        back_populates="evenements_assignes",
    )
    billets: Mapped[list["Billet"]] = relationship(back_populates="evenement", cascade="all, delete-orphan")
    ticket_types: Mapped[list["TicketType"]] = relationship(back_populates="evenement", cascade="all, delete-orphan")
    promo_codes: Mapped[list["PromoCode"]] = relationship(back_populates="evenement", cascade="all, delete-orphan")
    sessions: Mapped[list["EventSession"]] = relationship(
        back_populates="evenement",
        cascade="all, delete-orphan",
        order_by="EventSession.starts_at.asc()",
    )


class EventSession(Base):
    __tablename__ = "event_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evenement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evenements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(100))
    day_index: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    evenement: Mapped["Evenement"] = relationship(back_populates="sessions")
    billets: Mapped[list["Billet"]] = relationship(
        "Billet",
        secondary="billet_sessions",
        back_populates="sessions",
    )

    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="ck_event_sessions_ends_after_starts"),
    )
