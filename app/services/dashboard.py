from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PaymentStatus, TicketStatus
from app.models.payment import Paiement
from app.models.ticket import Billet


def event_dashboard(db: Session, *, evenement_id: uuid.UUID) -> dict[str, object]:
    tickets_total = db.execute(select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id)).scalar_one()
    tickets_paid = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id, Billet.statut == TicketStatus.PAYE)
    ).scalar_one()
    tickets_used = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id, Billet.statut == TicketStatus.UTILISE)
    ).scalar_one()
    tickets_cancelled = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id, Billet.statut == TicketStatus.ANNULE)
    ).scalar_one()

    payments_pending = db.execute(
        select(func.count())
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.EN_ATTENTE)
    ).scalar_one()

    revenue_success = db.execute(
        select(func.coalesce(func.sum(Paiement.montant), 0))
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.SUCCES)
    ).scalar_one()
    revenue_refunded = db.execute(
        select(func.coalesce(func.sum(Paiement.montant), 0))
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.REMBOURSE)
    ).scalar_one()

    return {
        "evenement_id": evenement_id,
        "tickets_total": int(tickets_total),
        "tickets_paid": int(tickets_paid),
        "tickets_used": int(tickets_used),
        "tickets_cancelled": int(tickets_cancelled),
        "payments_pending": int(payments_pending),
        "revenue_success": Decimal(str(revenue_success)),
        "revenue_refunded": Decimal(str(revenue_refunded)),
    }

