from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import EventSession
from app.models.ticket import Billet
from app.models.ticket_scan import TicketScan
from app.models.enums import TicketStatus


def get_ticket_by_qr(db: Session, *, qr_code: str) -> Billet | None:
    stmt = select(Billet).where(Billet.qr_code == qr_code)
    return db.execute(stmt).scalar_one_or_none()


def _infer_active_session_id(db: Session, *, evenement_id: uuid.UUID, now: datetime) -> uuid.UUID | None:
    stmt = (
        select(EventSession.id)
        .where(
            EventSession.evenement_id == evenement_id,
            EventSession.starts_at <= now,
            EventSession.ends_at >= now,
        )
        .order_by(EventSession.starts_at.desc())
        .limit(2)
    )
    rows = list(db.execute(stmt).scalars().all())
    if len(rows) != 1:
        return None
    return rows[0]


def _event_has_sessions(db: Session, *, evenement_id: uuid.UUID) -> bool:
    stmt = select(EventSession.id).where(EventSession.evenement_id == evenement_id).limit(1)
    return db.execute(stmt).first() is not None


def create_scan(
    db: Session,
    *,
    billet_id: uuid.UUID,
    agent_id: uuid.UUID,
    session_id: uuid.UUID | None,
    result: str,
) -> TicketScan:
    row = TicketScan(billet_id=billet_id, agent_id=agent_id, session_id=session_id, result=result)
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
    session_id: uuid.UUID | None = None,
) -> tuple[str, Billet | None, datetime | None, uuid.UUID | None]:
    ticket = get_ticket_by_qr(db, qr_code=qr_code)
    if ticket is None:
        return "NOT_FOUND", None, None, None

    if evenement_id is not None and ticket.evenement_id != evenement_id:
        create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=session_id, result="INVALID_EVENT")
        return "INVALID_EVENT", ticket, None, None

    if ticket.statut == TicketStatus.ANNULE:
        create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=session_id, result="CANCELLED")
        return "CANCELLED", ticket, None, None

    now = datetime.now(timezone.utc)
    event_id_to_check = ticket.evenement_id if evenement_id is None else evenement_id
    has_sessions = _event_has_sessions(db, evenement_id=event_id_to_check)
    has_entitlements = bool(ticket.session_ids)
    should_use_sessions = has_sessions or has_entitlements or session_id is not None
    used_session_id: uuid.UUID | None = None

    if should_use_sessions:
        used_session_id = session_id
        if used_session_id is None and has_sessions:
            used_session_id = _infer_active_session_id(db, evenement_id=event_id_to_check, now=now)
        if used_session_id is None:
            create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=None, result="SESSION_REQUIRED")
            return "SESSION_REQUIRED", ticket, None, None

        session = db.get(EventSession, used_session_id)
        if session is None or session.evenement_id != event_id_to_check:
            create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=used_session_id, result="INVALID_SESSION")
            return "INVALID_SESSION", ticket, None, used_session_id

        if has_entitlements and used_session_id not in ticket.session_ids:
            create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=used_session_id, result="NOT_ENTITLED")
            return "NOT_ENTITLED", ticket, None, used_session_id

        last_ok = db.execute(
            select(TicketScan.scanned_at)
            .where(
                TicketScan.billet_id == ticket.id,
                TicketScan.session_id == used_session_id,
                TicketScan.result == "OK",
            )
            .order_by(TicketScan.scanned_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if last_ok is not None:
            scan = create_scan(
                db,
                billet_id=ticket.id,
                agent_id=agent_id,
                session_id=used_session_id,
                result="ALREADY_USED",
            )
            return "ALREADY_USED", ticket, scan.scanned_at or last_ok, used_session_id

        if ticket.statut not in {TicketStatus.PAYE, TicketStatus.UTILISE}:
            create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=used_session_id, result="NOT_PAID")
            return "NOT_PAID", ticket, None, used_session_id

        scan = create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=used_session_id, result="OK")
        scan_time = scan.scanned_at or now
        return "OK", ticket, scan_time, used_session_id

    if ticket.statut != TicketStatus.PAYE:
        create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=None, result="NOT_PAID")
        return "NOT_PAID", ticket, None, None

    ticket.statut = TicketStatus.UTILISE
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    scan = create_scan(db, billet_id=ticket.id, agent_id=agent_id, session_id=None, result="OK")
    scan_time = scan.scanned_at or now
    return "OK", ticket, scan_time, None
