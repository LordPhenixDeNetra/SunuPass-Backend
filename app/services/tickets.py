from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import PromoDiscountType
from app.models.event import Evenement
from app.models.promo_code import PromoCode
from app.models.ticket import Billet
from app.models.ticket_type import TicketType
from app.schemas.ticket import BilletCreate, BilletGuestPurchase, BilletUpdate
from app.services.notifications import create_notification
from app.services.promo_codes import get_promo_code_by_code
from app.services.pagination import paginate


def create_billet(db: Session, payload: BilletCreate) -> Billet:
    evenement = db.get(Evenement, payload.evenement_id)
    if evenement is None:
        raise ValueError("Event not found")

    now = datetime.now(timezone.utc)

    current_count = db.execute(
        select(func.count()).select_from(Billet).where(
            Billet.evenement_id == payload.evenement_id,
            Billet.statut != "ANNULE",
        )
    ).scalar_one()
    if int(current_count) >= evenement.capacite:
        raise ValueError("Event capacity reached")

    ticket_type: TicketType | None = None
    if payload.ticket_type_id is not None:
        ticket_type = db.get(TicketType, payload.ticket_type_id)
        if ticket_type is None or ticket_type.evenement_id != payload.evenement_id or not ticket_type.is_active:
            raise ValueError("Invalid ticket type")
        if ticket_type.sales_start is not None and now < ticket_type.sales_start:
            raise ValueError("Ticket sales not started")
        if ticket_type.sales_end is not None and now > ticket_type.sales_end:
            raise ValueError("Ticket sales ended")
        if ticket_type.quota > 0:
            used = db.execute(
                select(func.count()).select_from(Billet).where(
                    Billet.evenement_id == payload.evenement_id,
                    Billet.ticket_type_id == ticket_type.id,
                    Billet.statut != "ANNULE",
                )
            ).scalar_one()
            if int(used) >= ticket_type.quota:
                raise ValueError("Ticket type quota reached")

    if ticket_type is None:
        if payload.type is None or payload.prix is None:
            raise ValueError("type and prix are required when ticket_type_id is not provided")
        type_code = payload.type
        base_price = payload.prix
        ticket_type_id = None
    else:
        type_code = ticket_type.code
        base_price = ticket_type.prix
        ticket_type_id = ticket_type.id

    promo: PromoCode | None = None
    final_price = Decimal(str(base_price))
    if payload.promo_code:
        promo = get_promo_code_by_code(db, evenement_id=payload.evenement_id, code=payload.promo_code)
        if promo is None or not promo.is_active:
            raise ValueError("Invalid promo code")
        if promo.starts_at is not None and now < promo.starts_at:
            raise ValueError("Promo code not started")
        if promo.ends_at is not None and now > promo.ends_at:
            raise ValueError("Promo code expired")
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            raise ValueError("Promo code limit reached")

        if promo.discount_type == PromoDiscountType.PERCENT:
            final_price = (final_price * (Decimal("100") - promo.value) / Decimal("100")).quantize(Decimal("0.01"))
        else:
            final_price = (final_price - promo.value).quantize(Decimal("0.01"))
        if final_price < 0:
            final_price = Decimal("0.00")

        promo.used_count += 1
        db.add(promo)

    qr_code = payload.qr_code or f"QR-{uuid.uuid4()}"

    ticket = Billet(
        evenement_id=payload.evenement_id,
        participant_id=payload.participant_id,
        guest_email=None,
        guest_nom_complet=None,
        guest_phone=None,
        ticket_type_id=ticket_type_id,
        type=type_code,
        prix_initial=Decimal(str(base_price)),
        prix=final_price,
        qr_code=qr_code,
        promo_code_id=None if promo is None else promo.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    if ticket.participant_id is not None:
        create_notification(
            db,
            user_id=ticket.participant_id,
            type_="TICKET_CREATED",
            title="Billet créé",
            body=f"Votre billet {ticket.type} a été créé pour l’événement {evenement.titre}.",
        )
    return ticket


def create_billet_guest(db: Session, payload: BilletGuestPurchase) -> Billet:
    evenement = db.get(Evenement, payload.evenement_id)
    if evenement is None:
        raise ValueError("Event not found")

    now = datetime.now(timezone.utc)

    current_count = db.execute(
        select(func.count()).select_from(Billet).where(
            Billet.evenement_id == payload.evenement_id,
            Billet.statut != "ANNULE",
        )
    ).scalar_one()
    if int(current_count) >= evenement.capacite:
        raise ValueError("Event capacity reached")

    ticket_type: TicketType | None = None
    if payload.ticket_type_id is not None:
        ticket_type = db.get(TicketType, payload.ticket_type_id)
        if ticket_type is None or ticket_type.evenement_id != payload.evenement_id or not ticket_type.is_active:
            raise ValueError("Invalid ticket type")
        if ticket_type.sales_start is not None and now < ticket_type.sales_start:
            raise ValueError("Ticket sales not started")
        if ticket_type.sales_end is not None and now > ticket_type.sales_end:
            raise ValueError("Ticket sales ended")
        if ticket_type.quota > 0:
            used = db.execute(
                select(func.count()).select_from(Billet).where(
                    Billet.evenement_id == payload.evenement_id,
                    Billet.ticket_type_id == ticket_type.id,
                    Billet.statut != "ANNULE",
                )
            ).scalar_one()
            if int(used) >= ticket_type.quota:
                raise ValueError("Ticket type quota reached")

    if ticket_type is None:
        if payload.type is None or payload.prix is None:
            raise ValueError("type and prix are required when ticket_type_id is not provided")
        type_code = payload.type
        base_price = payload.prix
        ticket_type_id = None
    else:
        type_code = ticket_type.code
        base_price = ticket_type.prix
        ticket_type_id = ticket_type.id

    promo: PromoCode | None = None
    final_price = Decimal(str(base_price))
    if payload.promo_code:
        promo = get_promo_code_by_code(db, evenement_id=payload.evenement_id, code=payload.promo_code)
        if promo is None or not promo.is_active:
            raise ValueError("Invalid promo code")
        if promo.starts_at is not None and now < promo.starts_at:
            raise ValueError("Promo code not started")
        if promo.ends_at is not None and now > promo.ends_at:
            raise ValueError("Promo code expired")
        if promo.usage_limit is not None and promo.used_count >= promo.usage_limit:
            raise ValueError("Promo code limit reached")

        if promo.discount_type == PromoDiscountType.PERCENT:
            final_price = (final_price * (Decimal("100") - promo.value) / Decimal("100")).quantize(Decimal("0.01"))
        else:
            final_price = (final_price - promo.value).quantize(Decimal("0.01"))
        if final_price < 0:
            final_price = Decimal("0.00")

        promo.used_count += 1
        db.add(promo)

    qr_code = f"QR-{uuid.uuid4()}"

    ticket = Billet(
        evenement_id=payload.evenement_id,
        participant_id=None,
        guest_email=payload.guest_email,
        guest_nom_complet=payload.guest_nom_complet,
        guest_phone=payload.guest_phone,
        ticket_type_id=ticket_type_id,
        type=type_code,
        prix_initial=Decimal(str(base_price)),
        prix=final_price,
        qr_code=qr_code,
        promo_code_id=None if promo is None else promo.id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_billet(db: Session, billet_id: uuid.UUID) -> Billet | None:
    return db.get(Billet, billet_id)


def list_billets_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    evenement_id: uuid.UUID | None = None,
    participant_id: uuid.UUID | None = None,
) -> tuple[list[Billet], int]:
    stmt = select(Billet).order_by(Billet.created_at.desc())
    if evenement_id is not None:
        stmt = stmt.where(Billet.evenement_id == evenement_id)
    if participant_id is not None:
        stmt = stmt.where(Billet.participant_id == participant_id)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_billet(db: Session, billet: Billet, payload: BilletUpdate) -> Billet:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(billet, key, value)
    db.add(billet)
    db.commit()
    db.refresh(billet)
    return billet


def delete_billet(db: Session, billet: Billet) -> None:
    db.delete(billet)
    db.commit()
