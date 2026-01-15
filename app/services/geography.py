from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.geography import AdministrativeLevel, AdministrativeUnit, Country
from app.schemas.geography import (
    AdministrativeLevelCreate,
    AdministrativeLevelUpdate,
    AdministrativeUnitCreate,
    AdministrativeUnitUpdate,
    CountryCreate,
    CountryUpdate,
)
from app.services.pagination import paginate


def create_country(db: Session, payload: CountryCreate) -> Country:
    country = Country(**payload.model_dump())
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def get_country(db: Session, country_code: str) -> Country | None:
    return db.get(Country, country_code)


def list_countries_paginated(db: Session, *, limit: int = 50, offset: int = 0) -> tuple[list[Country], int]:
    stmt = select(Country).order_by(Country.name.asc())
    return paginate(db, stmt, limit=limit, offset=offset)


def update_country(db: Session, country: Country, payload: CountryUpdate) -> Country:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(country, key, value)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def delete_country(db: Session, country: Country) -> None:
    db.delete(country)
    db.commit()


def create_administrative_level(db: Session, payload: AdministrativeLevelCreate) -> AdministrativeLevel:
    level = AdministrativeLevel(**payload.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


def get_administrative_level(db: Session, level_id: uuid.UUID) -> AdministrativeLevel | None:
    return db.get(AdministrativeLevel, level_id)


def list_administrative_levels_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    country_code: str | None = None,
) -> tuple[list[AdministrativeLevel], int]:
    stmt = select(AdministrativeLevel).order_by(AdministrativeLevel.level_order.asc())
    if country_code is not None:
        stmt = stmt.where(AdministrativeLevel.country_code == country_code)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_administrative_level(
    db: Session,
    level: AdministrativeLevel,
    payload: AdministrativeLevelUpdate,
) -> AdministrativeLevel:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(level, key, value)
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


def delete_administrative_level(db: Session, level: AdministrativeLevel) -> None:
    db.delete(level)
    db.commit()


def create_administrative_unit(db: Session, payload: AdministrativeUnitCreate) -> AdministrativeUnit:
    unit = AdministrativeUnit(**payload.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def get_administrative_unit(db: Session, unit_id: uuid.UUID) -> AdministrativeUnit | None:
    return db.get(AdministrativeUnit, unit_id)


def list_administrative_units_paginated(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    level_id: uuid.UUID | None = None,
    parent_id: uuid.UUID | None = None,
) -> tuple[list[AdministrativeUnit], int]:
    stmt = select(AdministrativeUnit).order_by(AdministrativeUnit.name.asc())
    if level_id is not None:
        stmt = stmt.where(AdministrativeUnit.level_id == level_id)
    if parent_id is not None:
        stmt = stmt.where(AdministrativeUnit.parent_id == parent_id)
    return paginate(db, stmt, limit=limit, offset=offset)


def update_administrative_unit(
    db: Session,
    unit: AdministrativeUnit,
    payload: AdministrativeUnitUpdate,
) -> AdministrativeUnit:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(unit, key, value)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def delete_administrative_unit(db: Session, unit: AdministrativeUnit) -> None:
    db.delete(unit)
    db.commit()

