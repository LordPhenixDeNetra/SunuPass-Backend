from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.user import Admin, Organisateur, Utilisateur
from app.schemas.organisation import OrganisationCreate, OrganisationRead, OrganisationUpdate
from app.schemas.pagination import Page
from app.schemas.user import UtilisateurRead
from app.services.organisations import (
    assign_organisation_to_organisateur,
    create_organisation,
    delete_organisation,
    get_organisation,
    list_organisations_paginated,
    unassign_organisation_from_organisateur,
    update_organisation,
)

router = APIRouter(prefix="/organisations", tags=["organisations"])


@router.post(
    "",
    response_model=OrganisationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une organisation",
    description="Crée une organisation (ADMIN uniquement).",
    responses=AUTHZ_ERRORS,
)
def create_organisation_endpoint(
    payload: OrganisationCreate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> OrganisationRead:
    return create_organisation(db, payload)


@router.get(
    "",
    response_model=Page[OrganisationRead],
    summary="Lister les organisations",
    description="Liste paginée des organisations (ADMIN uniquement).",
    responses=AUTHZ_ERRORS,
)
def list_organisations(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    pays_code: str | None = Query(default=None, description="Filtrer par code pays (ISO alpha-3)"),
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> Page[OrganisationRead]:
    items, total = list_organisations_paginated(db, limit=limit, offset=offset, pays_code=pays_code)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/me",
    response_model=OrganisationRead,
    summary="Lire mon organisation",
    description="Retourne l’organisation associée à l’organisateur connecté.",
    responses=AUTHZ_ERRORS,
)
def read_my_organisation(
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Organisateur)),
) -> OrganisationRead:
    if user.organisation_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    organisation = get_organisation(db, user.organisation_id)
    if organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    return organisation


@router.get(
    "/{organisation_id}",
    response_model=OrganisationRead,
    summary="Lire une organisation",
    description="Retourne une organisation par id. Un organisateur ne peut lire que sa propre organisation.",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def read_organisation(
    organisation_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> OrganisationRead:
    organisation = get_organisation(db, organisation_id)
    if organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    if isinstance(user, Organisateur) and user.organisation_id != organisation_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return organisation


@router.patch(
    "/{organisation_id}",
    response_model=OrganisationRead,
    summary="Modifier une organisation",
    description="Met à jour une organisation (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_organisation(
    organisation_id: uuid.UUID,
    payload: OrganisationUpdate,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> OrganisationRead:
    organisation = get_organisation(db, organisation_id)
    if organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    return update_organisation(db, organisation, payload)


@router.delete(
    "/{organisation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une organisation",
    description="Supprime une organisation (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def delete_organisation_endpoint(
    organisation_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> None:
    organisation = get_organisation(db, organisation_id)
    if organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    delete_organisation(db, organisation)


@router.put(
    "/{organisation_id}/organisateurs/{organisateur_id}",
    response_model=UtilisateurRead,
    summary="Assigner une organisation à un organisateur",
    description="Associe un organisateur à une organisation (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def assign_to_organisateur(
    organisation_id: uuid.UUID,
    organisateur_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> UtilisateurRead:
    organisation = get_organisation(db, organisation_id)
    if organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation not found")
    try:
        return assign_organisation_to_organisateur(db, organisation=organisation, organisateur_id=organisateur_id)
    except ValueError as e:
        detail = str(e)
        if detail == "User not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.delete(
    "/organisateurs/{organisateur_id}",
    response_model=UtilisateurRead,
    summary="Désassigner l'organisation d'un organisateur",
    description="Retire l’association entre un organisateur et son organisation (ADMIN uniquement).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def unassign_from_organisateur(
    organisateur_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Utilisateur = Depends(require_users(Admin)),
) -> UtilisateurRead:
    try:
        return unassign_organisation_from_organisateur(db, organisateur_id=organisateur_id)
    except ValueError as e:
        detail = str(e)
        if detail == "User not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
