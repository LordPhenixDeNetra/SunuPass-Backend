from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.openapi_responses import AUTHZ_ERRORS
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import Utilisateur
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
    agent: Utilisateur = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
) -> TicketScanResponse:
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

