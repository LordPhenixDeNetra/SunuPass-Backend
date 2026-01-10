from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import events

router = APIRouter()
router.include_router(events.router)
