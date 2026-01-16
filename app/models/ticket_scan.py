from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TicketScan(Base):
    __tablename__ = "ticket_scans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    billet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("billets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id"), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    billet: Mapped["Billet"] = relationship(back_populates="scans")
    session: Mapped[Optional["EventSession"]] = relationship()
    agent: Mapped["Agent"] = relationship()
