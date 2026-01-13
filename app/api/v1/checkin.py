from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_users
from app.api.openapi_responses import AUTHZ_ERRORS
from app.db.session import get_db
from app.models.event import evenement_agents
from app.models.user import Admin, Agent, Utilisateur
from app.schemas.checkin import TicketScanRequest, TicketScanResponse
from app.services.checkin import validate_and_checkin
from app.services.notifications import create_notification

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.post(
    "/scan",
    response_model=TicketScanResponse,
    summary="Scanner un QR code (check-in)",
    responses=AUTHZ_ERRORS,
)
def scan_qr(
    payload: TicketScanRequest,
    db: Session = Depends(get_db),
    agent: Utilisateur = Depends(require_users(Admin, Agent)),
) -> TicketScanResponse:
    if payload.evenement_id is not None and isinstance(agent, Agent):
        stmt = select(evenement_agents.c.agent_id).where(
            evenement_agents.c.evenement_id == payload.evenement_id,
            evenement_agents.c.agent_id == agent.id,
        )
        if db.execute(stmt).first() is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    result, ticket, scanned_at = validate_and_checkin(
        db,
        qr_code=payload.qr_code,
        agent_id=agent.id,
        evenement_id=payload.evenement_id,
    )
    if result == "OK" and ticket is not None:
        create_notification(
            db,
            user_id=ticket.participant_id,
            type_="TICKET_USED",
            title="Entrée validée",
            body=f"Votre billet {ticket.type} a été validé à l’entrée.",
        )
    return TicketScanResponse(
        result=result,
        billet_id=None if ticket is None else ticket.id,
        ticket_status=None if ticket is None else str(ticket.statut),
        scanned_at=scanned_at,
    )
