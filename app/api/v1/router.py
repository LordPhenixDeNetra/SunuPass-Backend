from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    checkin,
    dashboard,
    events,
    exports,
    geography,
    organisations,
    payments,
    promo_codes,
    public_tickets,
    ticket_types,
    tickets,
    users,
    notifications,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(events.router)
router.include_router(users.router)
router.include_router(tickets.router)
router.include_router(payments.router)
router.include_router(ticket_types.router)
router.include_router(promo_codes.router)
router.include_router(checkin.router)
router.include_router(dashboard.router)
router.include_router(exports.router)
router.include_router(notifications.router)
router.include_router(public_tickets.router)
router.include_router(geography.router)
router.include_router(organisations.router)
