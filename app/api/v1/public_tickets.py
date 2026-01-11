from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.openapi_responses import AUTH_ERRORS
from app.db.session import get_db
from app.schemas.ticket import BilletGuestPurchase, BilletRead
from app.services.tickets import create_billet_guest

router = APIRouter(prefix="/public", tags=["public"])


@router.post(
    "/tickets/purchase",
    response_model=BilletRead,
    status_code=status.HTTP_201_CREATED,
    summary="Acheter un billet sans compte",
    responses=AUTH_ERRORS,
)
def purchase_ticket_guest(
    payload: BilletGuestPurchase,
    db: Session = Depends(get_db),
) -> BilletRead:
    try:
        return create_billet_guest(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

