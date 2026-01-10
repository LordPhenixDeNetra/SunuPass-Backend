from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import Utilisateur
from app.schemas.user import UtilisateurCreate, UtilisateurUpdate
from app.services.pagination import paginate


def create_utilisateur(db: Session, payload: UtilisateurCreate) -> Utilisateur:
    user = Utilisateur(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_utilisateur(db: Session, user_id: uuid.UUID) -> Utilisateur | None:
    return db.get(Utilisateur, user_id)


def get_utilisateur_by_email(db: Session, email: str) -> Utilisateur | None:
    return db.execute(select(Utilisateur).where(Utilisateur.email == email)).scalar_one_or_none()


def list_utilisateurs_paginated(
    db: Session, *, limit: int = 50, offset: int = 0
) -> tuple[list[Utilisateur], int]:
    stmt = select(Utilisateur).order_by(Utilisateur.created_at.desc())
    return paginate(db, stmt, limit=limit, offset=offset)


def update_utilisateur(
    db: Session, user: Utilisateur, payload: UtilisateurUpdate
) -> Utilisateur:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_utilisateur(db: Session, user: Utilisateur) -> None:
    db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    db.delete(user)
    db.commit()
