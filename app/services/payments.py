from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PaymentStatus, TicketStatus
from app.models.payment import Paiement
from app.models.ticket import Billet
from app.schemas.payment import PaiementCreate, PaiementUpdate
from app.services.notifications import create_notification
from app.services.pagination import paginate


def create_paiement(db: Session, payload: PaiementCreate) -> Paiement:
    paiement = Paiement(**payload.model_dump())
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement


def get_paiement(db: Session, paiement_id: uuid.UUID) -> Paiement | None:
    return db.get(Paiement, paiement_id)


def get_paiement_by_billet(db: Session, billet_id: uuid.UUID) -> Paiement | None:
    stmt = select(Paiement).where(Paiement.billet_id == billet_id)
    return db.execute(stmt).scalar_one_or_none()


def list_paiements_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    billet_id: uuid.UUID | None = None,
) -> tuple[list[Paiement], int]:
    stmt = select(Paiement).order_by(Paiement.date_paiement.desc().nullslast())
    if billet_id is not None:
        stmt = stmt.where(Paiement.billet_id == billet_id)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_paiement(db: Session, paiement: Paiement, payload: PaiementUpdate) -> Paiement:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(paiement, key, value)
    billet = db.get(Billet, paiement.billet_id)
    if billet is not None and "statut" in data:
        if paiement.statut == PaymentStatus.SUCCES:
            billet.statut = TicketStatus.PAYE
            db.add(billet)
            if billet.participant_id is not None:
                create_notification(
                    db,
                    user_id=billet.participant_id,
                    type_="PAYMENT_SUCCESS",
                    title="Paiement confirmé",
                    body=f"Votre paiement pour le billet {billet.type} est confirmé.",
                )
        elif paiement.statut == PaymentStatus.REMBOURSE:
            billet.statut = TicketStatus.ANNULE
            db.add(billet)
            if billet.participant_id is not None:
                create_notification(
                    db,
                    user_id=billet.participant_id,
                    type_="PAYMENT_REFUNDED",
                    title="Paiement remboursé",
                    body=f"Votre paiement pour le billet {billet.type} a été remboursé.",
                )
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement


def refund_paiement(db: Session, paiement: Paiement) -> Paiement:
    payload = PaiementUpdate(statut=PaymentStatus.REMBOURSE, date_paiement=datetime.now(timezone.utc))
    return update_paiement(db, paiement, payload)


def delete_paiement(db: Session, paiement: Paiement) -> None:
    db.delete(paiement)
    db.commit()
