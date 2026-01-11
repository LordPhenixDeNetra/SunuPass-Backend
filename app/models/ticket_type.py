from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TicketType(Base):
    __tablename__ = "ticket_types"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    evenement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evenements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(150), nullable=False)
    prix: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sales_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sales_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    evenement: Mapped["Evenement"] = relationship(back_populates="ticket_types")
    billets: Mapped[list["Billet"]] = relationship(back_populates="ticket_type")
