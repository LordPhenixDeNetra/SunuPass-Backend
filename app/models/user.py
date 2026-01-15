from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    nom_complet: Mapped[str | None] = mapped_column(String(150))
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.PARTICIPANT,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    evenements: Mapped[list["Evenement"]] = relationship(back_populates="organisateur")
    billets: Mapped[list["Billet"]] = relationship(back_populates="participant")

    __mapper_args__ = {
        "polymorphic_on": role,
    }


class Admin(Utilisateur):
    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True
    )
    __mapper_args__ = {"polymorphic_identity": UserRole.ADMIN}


class Organisateur(Utilisateur):
    __tablename__ = "organisateurs"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True
    )
    organisation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organisations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organisation: Mapped[Optional["Organisation"]] = relationship(back_populates="organisateurs")
    __mapper_args__ = {"polymorphic_identity": UserRole.ORGANISATEUR}


class Participant(Utilisateur):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True
    )
    __mapper_args__ = {"polymorphic_identity": UserRole.PARTICIPANT}


class Agent(Utilisateur):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("utilisateurs.id", ondelete="CASCADE"), primary_key=True
    )
    __mapper_args__ = {"polymorphic_identity": UserRole.AGENT}

    evenements_assignes: Mapped[list["Evenement"]] = relationship(
        "Evenement",
        secondary="evenement_agents",
        back_populates="agents",
    )
