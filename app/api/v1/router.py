from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, events, payments, tickets, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(events.router)
router.include_router(users.router)
router.include_router(tickets.router)
router.include_router(payments.router)
