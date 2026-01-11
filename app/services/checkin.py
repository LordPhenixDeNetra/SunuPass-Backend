from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Billet
from app.models.ticket_scan import TicketScan
from app.models.enums import TicketStatus


def get_ticket_by_qr(db: Session, *, qr_code: str) -> Billet | None:
    stmt = select(Billet).where(Billet.qr_code == qr_code)
    return db.execute(stmt).scalar_one_or_none()


def create_scan(
    db: Session,
    *,
    billet_id: uuid.UUID,
    agent_id: uuid.UUID,
    result: str,
) -> TicketScan:
    row = TicketScan(billet_id=billet_id, agent_id=agent_id, result=result)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def validate_and_checkin(
    db: Session,
    *,
    qr_code: str,
    agent_id: uuid.UUID,
    evenement_id: uuid.UUID | None = None,
) -> tuple[str, Billet | None, datetime | None]:
    ticket = get_ticket_by_qr(db, qr_code=qr_code)
    if ticket is None:
        return "NOT_FOUND", None, None

    if evenement_id is not None and ticket.evenement_id != evenement_id:
        create_scan(db, billet_id=ticket.id, agent_id=agent_id, result="INVALID_EVENT")
        return "INVALID_EVENT", ticket, None

    if ticket.statut == TicketStatus.ANNULE:
        create_scan(db, billet_id=ticket.id, agent_id=agent_id, result="CANCELLED")
        return "CANCELLED", ticket, None

    if ticket.statut == TicketStatus.UTILISE:
        scan = create_scan(db, billet_id=ticket.id, agent_id=agent_id, result="ALREADY_USED")
        return "ALREADY_USED", ticket, scan.scanned_at

    if ticket.statut != TicketStatus.PAYE:
        create_scan(db, billet_id=ticket.id, agent_id=agent_id, result="NOT_PAID")
        return "NOT_PAID", ticket, None

    ticket.statut = TicketStatus.UTILISE
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    scan = create_scan(db, billet_id=ticket.id, agent_id=agent_id, result="OK")
    if scan.scanned_at is None:
        scan_time = datetime.now(timezone.utc)
    else:
        scan_time = scan.scanned_at
    return "OK", ticket, scan_time

