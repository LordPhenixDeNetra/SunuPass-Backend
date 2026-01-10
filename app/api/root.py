from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["root"], summary="Ping", description="Retourne un message simple pour vérifier que l’API répond.")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@router.get(
    "/hello/{name}",
    tags=["root"],
    summary="Ping paramétré",
    description="Retourne un message personnalisé pour vérifier le routage.",
)
async def say_hello(name: str) -> dict[str, str]:
    return {"message": f"Hello {name}"}


@router.get(
    "/health",
    tags=["root"],
    summary="Healthcheck",
    description="Retourne l’état du service (utile pour le monitoring).",
)
async def health() -> dict[str, str]:
    return {"status": "ok"}
