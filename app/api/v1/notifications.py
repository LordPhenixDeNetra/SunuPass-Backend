from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import Utilisateur
from app.schemas.notification import NotificationMarkRead, NotificationRead
from app.services.notifications import get_notification, list_notifications_paginated, mark_notification_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=list[NotificationRead],
    summary="Lister mes notifications",
    responses=AUTHZ_ERRORS,
)
def list_my_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> list[Notification]:
    items, _total = list_notifications_paginated(db, user_id=user.id, limit=limit, offset=offset)
    return items


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Marquer une notification comme lue",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def mark_read(
    notification_id: uuid.UUID,
    payload: NotificationMarkRead,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Notification:
    row = get_notification(db, notification_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return mark_notification_read(db, row, is_read=payload.is_read)

