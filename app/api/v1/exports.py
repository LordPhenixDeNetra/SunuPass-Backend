from __future__ import annotations

import csv
import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.event import Evenement
from app.models.payment import Paiement
from app.models.ticket import Billet
from app.models.ticket_scan import TicketScan
from app.models.user import Admin, Utilisateur

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get(
    "/events/{event_id}/participants.csv",
    summary="Exporter les participants (CSV)",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def export_participants_csv(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Response:
    evt = db.get(Evenement, event_id)
    if evt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not isinstance(user, Admin) and evt.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    stmt = (
        select(Billet, Paiement, Utilisateur, TicketScan)
        .join(Utilisateur, Utilisateur.id == Billet.participant_id, isouter=True)
        .join(Paiement, Paiement.billet_id == Billet.id, isouter=True)
        .join(TicketScan, TicketScan.billet_id == Billet.id, isouter=True)
        .where(Billet.evenement_id == event_id)
        .order_by(Billet.created_at.asc())
    )
    rows = db.execute(stmt).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ticket_id",
            "participant_id",
            "email",
            "nom_complet",
            "type",
            "status",
            "prix",
            "payment_status",
            "payment_method",
            "scanned_at",
        ]
    )
    for billet, paiement, participant, scan in rows:
        email = billet.guest_email if participant is None else participant.email
        nom_complet = billet.guest_nom_complet if participant is None else (participant.nom_complet or "")
        participant_id = "" if participant is None else str(participant.id)
        writer.writerow(
            [
                str(billet.id),
                participant_id,
                email or "",
                nom_complet,
                billet.type,
                str(billet.statut),
                str(billet.prix),
                "" if paiement is None else str(paiement.statut),
                "" if paiement is None else paiement.moyen,
                "" if scan is None else (scan.scanned_at.isoformat() if scan.scanned_at else ""),
            ]
        )

    filename = f"participants-{event_id}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
