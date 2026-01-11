from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.promo_code import PromoCode
from app.schemas.promo import PromoCodeCreate, PromoCodeUpdate


def create_promo_code(db: Session, *, evenement_id: uuid.UUID, payload: PromoCodeCreate) -> PromoCode:
    row = PromoCode(evenement_id=evenement_id, used_count=0, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_promo_code(db: Session, promo_code_id: uuid.UUID) -> PromoCode | None:
    return db.get(PromoCode, promo_code_id)


def get_promo_code_by_code(db: Session, *, evenement_id: uuid.UUID, code: str) -> PromoCode | None:
    stmt = select(PromoCode).where(PromoCode.evenement_id == evenement_id, PromoCode.code == code)
    return db.execute(stmt).scalar_one_or_none()


def list_promo_codes(db: Session, *, evenement_id: uuid.UUID) -> list[PromoCode]:
    stmt = select(PromoCode).where(PromoCode.evenement_id == evenement_id).order_by(PromoCode.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def update_promo_code(db: Session, row: PromoCode, payload: PromoCodeUpdate) -> PromoCode:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_promo_code(db: Session, row: PromoCode) -> None:
    db.delete(row)
    db.commit()

