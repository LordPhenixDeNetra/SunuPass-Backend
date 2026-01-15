from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nom_organisation: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    nb_employes_min: Mapped[int] = mapped_column(Integer, nullable=False)
    nb_employes_max: Mapped[int] = mapped_column(Integer, nullable=False)
    pays_code: Mapped[str] = mapped_column(
        String(3),
        ForeignKey("countries.code", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    telephone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    organisateurs: Mapped[list["Organisateur"]] = relationship(back_populates="organisation")

    __table_args__ = (
        CheckConstraint("nb_employes_min >= 0", name="ck_organisation_nb_employes_min_nonneg"),
        CheckConstraint("nb_employes_max >= 0", name="ck_organisation_nb_employes_max_nonneg"),
        CheckConstraint("nb_employes_min <= nb_employes_max", name="ck_organisation_nb_employes_range"),
    )

