from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.event import Evenement
from app.models.user import Admin, Utilisateur
from app.schemas.dashboard import EventDashboard
from app.services.dashboard import event_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/events/{event_id}",
    response_model=EventDashboard,
    summary="Dashboard événement",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def get_event_dashboard(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> EventDashboard:
    evt = db.get(Evenement, event_id)
    if evt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not isinstance(user, Admin) and evt.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return EventDashboard(**event_dashboard(db, evenement_id=event_id))
