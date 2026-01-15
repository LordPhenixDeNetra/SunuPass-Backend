from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Country(Base):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    calling_code: Mapped[str] = mapped_column(String(10), nullable=False)
    flag_svg: Mapped[str | None] = mapped_column(Text)

    administrative_levels: Mapped[list["AdministrativeLevel"]] = relationship(
        back_populates="country",
        cascade="all, delete-orphan",
    )


class AdministrativeLevel(Base):
    __tablename__ = "administrative_levels"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    level_order: Mapped[int] = mapped_column(Integer, nullable=False)
    country_code: Mapped[str] = mapped_column(
        String(3),
        ForeignKey("countries.code", ondelete="CASCADE"),
        nullable=False,
    )

    country: Mapped["Country"] = relationship(back_populates="administrative_levels")
    units: Mapped[list["AdministrativeUnit"]] = relationship(back_populates="level")

    __table_args__ = (UniqueConstraint("country_code", "level_order", name="uq_country_level_order"),)


class AdministrativeUnit(Base):
    __tablename__ = "administrative_units"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    level_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("administrative_levels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("administrative_units.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    level: Mapped["AdministrativeLevel"] = relationship(back_populates="units")

    parent: Mapped[Optional["AdministrativeUnit"]] = relationship(
        remote_side="AdministrativeUnit.id",
        back_populates="children",
    )
    children: Mapped[list["AdministrativeUnit"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("parent_id", "name", name="uq_unit_per_parent"),)
