from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TicketScan(Base):
    __tablename__ = "ticket_scans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    billet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("billets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("utilisateurs.id"), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    billet: Mapped["Billet"] = relationship(back_populates="scans")
    agent: Mapped["Utilisateur"] = relationship()
