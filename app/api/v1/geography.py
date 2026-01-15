from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.user import Admin, Utilisateur
from app.schemas.geography import (
    AdministrativeLevelCreate,
    AdministrativeLevelRead,
    AdministrativeLevelUpdate,
    AdministrativeUnitCreate,
    AdministrativeUnitRead,
    AdministrativeUnitUpdate,
    CountryCreate,
    CountryRead,
    CountryUpdate,
)
from app.schemas.pagination import Page
from app.services.geography import (
    create_administrative_level,
    create_administrative_unit,
    create_country,
    delete_administrative_level,
    delete_administrative_unit,
    delete_country,
    get_administrative_level,
    get_administrative_unit,
    get_country,
    list_administrative_levels_paginated,
    list_administrative_units_paginated,
    list_countries_paginated,
    update_administrative_level,
    update_administrative_unit,
    update_country,
)

router = APIRouter(prefix="/geography", tags=["geography"])


@router.get(
    "/countries",
    response_model=Page[CountryRead],
    summary="Lister les pays",
)
def list_countries(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    db: Session = Depends(get_db),
) -> Page[CountryRead]:
    items, total = list_countries_paginated(db, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/countries/{country_code}",
    response_model=CountryRead,
    summary="Lire un pays",
    responses={404: RESPONSES_404},
)
def read_country(country_code: str, db: Session = Depends(get_db)) -> CountryRead:
    country = get_country(db, country_code)
    if country is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Country not found")
    return country


@router.post(
    "/countries",
    response_model=CountryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un pays",
    responses=AUTHZ_ERRORS,
)
def create_country_endpoint(
    payload: CountryCreate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> CountryRead:
    return create_country(db, payload)


@router.patch(
    "/countries/{country_code}",
    response_model=CountryRead,
    summary="Modifier un pays",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_country(
    country_code: str,
    payload: CountryUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> CountryRead:
    country = get_country(db, country_code)
    if country is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Country not found")
    return update_country(db, country, payload)


@router.delete(
    "/countries/{country_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un pays",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def delete_country_endpoint(
    country_code: str,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    country = get_country(db, country_code)
    if country is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Country not found")
    delete_country(db, country)


@router.get(
    "/administrative-levels",
    response_model=Page[AdministrativeLevelRead],
    summary="Lister les niveaux administratifs",
)
def list_levels(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    country_code: str | None = Query(default=None, description="Filtrer par code pays (ISO alpha-3)"),
    db: Session = Depends(get_db),
) -> Page[AdministrativeLevelRead]:
    items, total = list_administrative_levels_paginated(
        db,
        limit=limit,
        offset=offset,
        country_code=country_code,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/administrative-levels/{level_id}",
    response_model=AdministrativeLevelRead,
    summary="Lire un niveau administratif",
    responses={404: RESPONSES_404},
)
def read_level(level_id: uuid.UUID, db: Session = Depends(get_db)) -> AdministrativeLevelRead:
    level = get_administrative_level(db, level_id)
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrative level not found")
    return level


@router.post(
    "/administrative-levels",
    response_model=AdministrativeLevelRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un niveau administratif",
    responses=AUTHZ_ERRORS,
)
def create_level_endpoint(
    payload: AdministrativeLevelCreate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> AdministrativeLevelRead:
    return create_administrative_level(db, payload)


@router.patch(
    "/administrative-levels/{level_id}",
    response_model=AdministrativeLevelRead,
    summary="Modifier un niveau administratif",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_level(
    level_id: uuid.UUID,
    payload: AdministrativeLevelUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> AdministrativeLevelRead:
    level = get_administrative_level(db, level_id)
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrative level not found")
    return update_administrative_level(db, level, payload)


@router.delete(
    "/administrative-levels/{level_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un niveau administratif",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def delete_level_endpoint(
    level_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    level = get_administrative_level(db, level_id)
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrative level not found")
    delete_administrative_level(db, level)


@router.get(
    "/administrative-units",
    response_model=Page[AdministrativeUnitRead],
    summary="Lister les unités administratives",
)
def list_units(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    level_id: uuid.UUID | None = Query(default=None, description="Filtrer par niveau administratif"),
    parent_id: uuid.UUID | None = Query(default=None, description="Filtrer par parent"),
    db: Session = Depends(get_db),
) -> Page[AdministrativeUnitRead]:
    items, total = list_administrative_units_paginated(
        db,
        limit=limit,
        offset=offset,
        level_id=level_id,
        parent_id=parent_id,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/administrative-units/{unit_id}",
    response_model=AdministrativeUnitRead,
    summary="Lire une unité administrative",
    responses={404: RESPONSES_404},
)
def read_unit(unit_id: uuid.UUID, db: Session = Depends(get_db)) -> AdministrativeUnitRead:
    unit = get_administrative_unit(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrative unit not found")
    return unit


@router.post(
    "/administrative-units",
    response_model=AdministrativeUnitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une unité administrative",
    responses=AUTHZ_ERRORS,
)
def create_unit_endpoint(
    payload: AdministrativeUnitCreate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> AdministrativeUnitRead:
    return create_administrative_unit(db, payload)


@router.patch(
    "/administrative-units/{unit_id}",
    response_model=AdministrativeUnitRead,
    summary="Modifier une unité administrative",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_unit(
    unit_id: uuid.UUID,
    payload: AdministrativeUnitUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> AdministrativeUnitRead:
    unit = get_administrative_unit(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrative unit not found")
    return update_administrative_unit(db, unit, payload)


@router.delete(
    "/administrative-units/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une unité administrative",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def delete_unit_endpoint(
    unit_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    unit = get_administrative_unit(db, unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrative unit not found")
    delete_administrative_unit(db, unit)

