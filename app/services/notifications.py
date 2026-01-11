from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.pagination import paginate


def create_notification(
    db: Session,
    *,
    user_id: uuid.UUID,
    type_: str,
    title: str,
    body: str,
) -> Notification:
    row = Notification(user_id=user_id, type=type_, title=title, body=body, is_read=False)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_notifications_paginated(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
    return paginate(db, stmt, limit=limit, offset=offset)


def get_notification(db: Session, notification_id: uuid.UUID) -> Notification | None:
    return db.get(Notification, notification_id)


def mark_notification_read(db: Session, row: Notification, *, is_read: bool = True) -> Notification:
    row.is_read = is_read
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

