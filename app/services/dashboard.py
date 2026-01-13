from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.enums import PaymentStatus, TicketStatus
from app.models.event import Evenement
from app.models.payment import Paiement
from app.models.ticket import Billet
from app.models.ticket_scan import TicketScan
from app.models.ticket_type import TicketType


def _period_day(d: date) -> date:
    return d


def _period_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _period_month(d: date) -> date:
    return date(d.year, d.month, 1)


def _build_sales_series(
    *,
    ticket_created_dates: list[date],
    payment_success_items: list[tuple[date, Decimal]],
    period_fn,
) -> list[dict[str, object]]:
    buckets: dict[date, dict[str, object]] = {}

    def _get_bucket(d: date) -> dict[str, object]:
        key = period_fn(d)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {
                "period_start": key.isoformat(),
                "tickets_created": 0,
                "payments_success": 0,
                "revenue_success": Decimal("0"),
            }
            buckets[key] = bucket
        return bucket

    for d in ticket_created_dates:
        bucket = _get_bucket(d)
        bucket["tickets_created"] = int(bucket["tickets_created"]) + 1

    for d, amount in payment_success_items:
        bucket = _get_bucket(d)
        bucket["payments_success"] = int(bucket["payments_success"]) + 1
        bucket["revenue_success"] = Decimal(str(bucket["revenue_success"])) + Decimal(str(amount))

    return [buckets[k] for k in sorted(buckets.keys())]


def event_dashboard(db: Session, *, evenement_id: uuid.UUID) -> dict[str, object]:
    evenement = db.get(Evenement, evenement_id)
    if evenement is None:
        raise ValueError("Event not found")

    tickets_total = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id)
    ).scalar_one()
    tickets_active = db.execute(
        select(func.count())
        .select_from(Billet)
        .where(Billet.evenement_id == evenement_id, Billet.statut != TicketStatus.ANNULE)
    ).scalar_one()
    tickets_paid = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id, Billet.statut == TicketStatus.PAYE)
    ).scalar_one()
    tickets_used = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id, Billet.statut == TicketStatus.UTILISE)
    ).scalar_one()
    tickets_cancelled = db.execute(
        select(func.count()).select_from(Billet).where(Billet.evenement_id == evenement_id, Billet.statut == TicketStatus.ANNULE)
    ).scalar_one()
    tickets_guest = db.execute(
        select(func.count())
        .select_from(Billet)
        .where(Billet.evenement_id == evenement_id, Billet.participant_id.is_(None), Billet.statut != TicketStatus.ANNULE)
    ).scalar_one()
    participants_unique = db.execute(
        select(func.count(func.distinct(Billet.participant_id)))
        .select_from(Billet)
        .where(Billet.evenement_id == evenement_id, Billet.participant_id.is_not(None), Billet.statut != TicketStatus.ANNULE)
    ).scalar_one()
    scans_total = db.execute(
        select(func.count())
        .select_from(TicketScan)
        .join(Billet, Billet.id == TicketScan.billet_id)
        .where(Billet.evenement_id == evenement_id)
    ).scalar_one()

    payments_pending = db.execute(
        select(func.count())
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.EN_ATTENTE)
    ).scalar_one()
    payments_success = db.execute(
        select(func.count())
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.SUCCES)
    ).scalar_one()
    payments_failed = db.execute(
        select(func.count())
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.ECHEC)
    ).scalar_one()
    payments_refunded = db.execute(
        select(func.count())
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.REMBOURSE)
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

    type_stmt = (
        select(
            TicketType.id,
            TicketType.code,
            TicketType.label,
            TicketType.quota,
            func.count(Billet.id),
            func.sum(case((Billet.statut != TicketStatus.ANNULE, 1), else_=0)),
            func.sum(case((Billet.statut == TicketStatus.PAYE, 1), else_=0)),
            func.sum(case((Billet.statut == TicketStatus.UTILISE, 1), else_=0)),
            func.sum(case((Billet.statut == TicketStatus.ANNULE, 1), else_=0)),
            func.coalesce(func.sum(case((Paiement.statut == PaymentStatus.SUCCES, Paiement.montant), else_=0)), 0),
        )
        .select_from(TicketType)
        .join(Billet, Billet.ticket_type_id == TicketType.id, isouter=True)
        .join(Paiement, Paiement.billet_id == Billet.id, isouter=True)
        .where(TicketType.evenement_id == evenement_id)
        .group_by(TicketType.id, TicketType.code, TicketType.label, TicketType.quota)
        .order_by(TicketType.created_at.asc())
    )
    type_rows = db.execute(type_stmt).all()

    custom_stmt = (
        select(
            Billet.type,
            func.count(Billet.id),
            func.sum(case((Billet.statut != TicketStatus.ANNULE, 1), else_=0)),
            func.sum(case((Billet.statut == TicketStatus.PAYE, 1), else_=0)),
            func.sum(case((Billet.statut == TicketStatus.UTILISE, 1), else_=0)),
            func.sum(case((Billet.statut == TicketStatus.ANNULE, 1), else_=0)),
            func.coalesce(func.sum(case((Paiement.statut == PaymentStatus.SUCCES, Paiement.montant), else_=0)), 0),
        )
        .select_from(Billet)
        .join(Paiement, Paiement.billet_id == Billet.id, isouter=True)
        .where(Billet.evenement_id == evenement_id, Billet.ticket_type_id.is_(None))
        .group_by(Billet.type)
        .order_by(Billet.type.asc())
    )
    custom_rows = db.execute(custom_stmt).all()

    by_ticket_type: list[dict[str, object]] = []
    for (
        ticket_type_id,
        code,
        label,
        quota,
        total,
        active,
        paid,
        used,
        cancelled,
        revenue,
    ) in type_rows:
        by_ticket_type.append(
            {
                "ticket_type_id": ticket_type_id,
                "code": code,
                "label": label,
                "quota": int(quota),
                "tickets_total": int(total),
                "tickets_active": int(active or 0),
                "tickets_paid": int(paid or 0),
                "tickets_used": int(used or 0),
                "tickets_cancelled": int(cancelled or 0),
                "revenue_success": Decimal(str(revenue)),
            }
        )

    for code, total, active, paid, used, cancelled, revenue in custom_rows:
        by_ticket_type.append(
            {
                "ticket_type_id": None,
                "code": str(code),
                "label": None,
                "quota": None,
                "tickets_total": int(total),
                "tickets_active": int(active or 0),
                "tickets_paid": int(paid or 0),
                "tickets_used": int(used or 0),
                "tickets_cancelled": int(cancelled or 0),
                "revenue_success": Decimal(str(revenue)),
            }
        )

    remaining = max(int(evenement.capacite) - int(tickets_active), 0)
    usage_rate = Decimal("0")
    if int(evenement.capacite) > 0:
        usage_rate = (Decimal(int(tickets_active)) / Decimal(int(evenement.capacite))).quantize(Decimal("0.0001"))

    ticket_created_dates = [
        dt.date()
        for dt in db.execute(
            select(Billet.created_at).select_from(Billet).where(Billet.evenement_id == evenement_id)
        ).scalars()
        if dt is not None
    ]

    payment_success_items: list[tuple[date, Decimal]] = []
    payment_rows = db.execute(
        select(Paiement.date_paiement, Paiement.created_at, Paiement.montant)
        .select_from(Paiement)
        .join(Billet, Billet.id == Paiement.billet_id)
        .where(Billet.evenement_id == evenement_id, Paiement.statut == PaymentStatus.SUCCES)
    ).all()
    for date_paiement, created_at, montant in payment_rows:
        dt = date_paiement or created_at
        if dt is None:
            continue
        payment_success_items.append((dt.date(), Decimal(str(montant))))

    sales_daily = _build_sales_series(
        ticket_created_dates=ticket_created_dates, payment_success_items=payment_success_items, period_fn=_period_day
    )
    sales_weekly = _build_sales_series(
        ticket_created_dates=ticket_created_dates, payment_success_items=payment_success_items, period_fn=_period_week
    )
    sales_monthly = _build_sales_series(
        ticket_created_dates=ticket_created_dates, payment_success_items=payment_success_items, period_fn=_period_month
    )

    return {
        "evenement_id": evenement_id,
        "capacite": int(evenement.capacite),
        "tickets_active": int(tickets_active),
        "capacity_remaining": int(remaining),
        "capacity_usage_rate": usage_rate,
        "tickets_total": int(tickets_total),
        "tickets_paid": int(tickets_paid),
        "tickets_used": int(tickets_used),
        "tickets_cancelled": int(tickets_cancelled),
        "tickets_guest": int(tickets_guest),
        "participants_unique": int(participants_unique),
        "scans_total": int(scans_total),
        "payments_pending": int(payments_pending),
        "payments_success": int(payments_success),
        "payments_failed": int(payments_failed),
        "payments_refunded": int(payments_refunded),
        "revenue_success": Decimal(str(revenue_success)),
        "revenue_refunded": Decimal(str(revenue_refunded)),
        "by_ticket_type": by_ticket_type,
        "sales_daily": sales_daily,
        "sales_weekly": sales_weekly,
        "sales_monthly": sales_monthly,
    }
