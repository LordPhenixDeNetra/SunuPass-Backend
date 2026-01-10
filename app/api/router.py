from __future__ import annotations

from fastapi import APIRouter

from app.api import root
from app.api.v1 import router as v1

api_router = APIRouter()
api_router.include_router(root.router)
api_router.include_router(v1.router, prefix="/api/v1")

