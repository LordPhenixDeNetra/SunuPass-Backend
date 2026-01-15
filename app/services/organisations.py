from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organisation import Organisation
from app.models.user import Organisateur, Utilisateur
from app.schemas.organisation import OrganisationCreate, OrganisationUpdate
from app.services.pagination import paginate


def create_organisation(db: Session, payload: OrganisationCreate) -> Organisation:
    organisation = Organisation(**payload.model_dump())
    db.add(organisation)
    db.commit()
    db.refresh(organisation)
    return organisation


def get_organisation(db: Session, organisation_id: uuid.UUID) -> Organisation | None:
    return db.get(Organisation, organisation_id)


def list_organisations_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    pays_code: str | None = None,
) -> tuple[list[Organisation], int]:
    stmt = select(Organisation).order_by(Organisation.nom_organisation.asc())
    if pays_code is not None:
        stmt = stmt.where(Organisation.pays_code == pays_code)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_organisation(db: Session, organisation: Organisation, payload: OrganisationUpdate) -> Organisation:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(organisation, key, value)
    db.add(organisation)
    db.commit()
    db.refresh(organisation)
    return organisation


def delete_organisation(db: Session, organisation: Organisation) -> None:
    db.delete(organisation)
    db.commit()


def assign_organisation_to_organisateur(
    db: Session,
    *,
    organisation: Organisation,
    organisateur_id: uuid.UUID,
) -> Organisateur:
    user = db.get(Utilisateur, organisateur_id)
    if user is None:
        raise ValueError("User not found")
    if not isinstance(user, Organisateur):
        raise ValueError("User is not an organisateur")
    user.organisation_id = organisation.id
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def unassign_organisation_from_organisateur(
    db: Session,
    *,
    organisateur_id: uuid.UUID,
) -> Organisateur:
    user = db.get(Utilisateur, organisateur_id)
    if user is None:
        raise ValueError("User not found")
    if not isinstance(user, Organisateur):
        raise ValueError("User is not an organisateur")
    user.organisation_id = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

