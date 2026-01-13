from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_users
from app.api.openapi_responses import AUTHZ_ERRORS, RESPONSES_404
from app.db.session import get_db
from app.models.event import evenement_agents
from app.models.user import Admin, Agent, Organisateur, Utilisateur
from app.schemas.event import EvenementCreate, EvenementRead, EvenementUpdate
from app.schemas.pagination import Page
from app.schemas.user import UtilisateurRead
from app.services.events import (
    create_evenement,
    delete_evenement,
    get_evenement,
    list_evenements_paginated,
    update_evenement,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EvenementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un événement",
    description="Crée un événement (ADMIN/ORGANISATEUR). Un organisateur ne peut créer que pour lui-même.",
    responses=AUTHZ_ERRORS,
)
def create_event(
    payload: EvenementCreate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> EvenementRead:
    if not isinstance(user, Admin) and payload.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return create_evenement(db, payload)


@router.get(
    "",
    response_model=Page[EvenementRead],
    summary="Lister les événements",
    description="Liste paginée. ADMIN voit tout, ORGANISATEUR voit uniquement ses événements.",
    responses=AUTHZ_ERRORS,
)
def list_events(
    limit: int = Query(50, ge=1, le=200, description="Taille de page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> Page[EvenementRead]:
    organisateur_id = user.id if isinstance(user, Organisateur) else None
    items, total = list_evenements_paginated(
        db, limit=limit, offset=offset, organisateur_id=organisateur_id
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{event_id}",
    response_model=EvenementRead,
    summary="Lire un événement",
    description="Retourne un événement. Un organisateur ne peut accéder qu’à ses événements.",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(get_current_user),
) -> EvenementRead:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if isinstance(user, Organisateur) and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return evenement


@router.patch(
    "/{event_id}",
    response_model=EvenementRead,
    summary="Modifier un événement",
    description="Modifie un événement (organisateur propriétaire ou ADMIN).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def patch_event(
    event_id: uuid.UUID,
    payload: EvenementUpdate,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> EvenementRead:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if isinstance(user, Organisateur) and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return update_evenement(db, evenement, payload)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un événement",
    description="Supprime un événement (organisateur propriétaire ou ADMIN).",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def remove_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> None:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if isinstance(user, Organisateur) and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    delete_evenement(db, evenement)


@router.get(
    "/{event_id}/agents",
    response_model=list[UtilisateurRead],
    summary="Lister les agents d’un événement",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def list_event_agents(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> list[Utilisateur]:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not isinstance(user, Admin) and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    stmt = (
        select(Agent)
        .join(evenement_agents, evenement_agents.c.agent_id == Agent.id)
        .where(evenement_agents.c.evenement_id == event_id)
        .order_by(Agent.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


@router.put(
    "/{event_id}/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Assigner un agent à un événement",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def assign_agent_to_event(
    event_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> None:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not isinstance(user, Admin) and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    agent = db.get(Utilisateur, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not isinstance(agent, Agent):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an agent")

    if agent not in evenement.agents:
        evenement.agents.append(agent)
        db.add(evenement)
        db.commit()


@router.delete(
    "/{event_id}/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Retirer un agent d’un événement",
    responses={**AUTHZ_ERRORS, 404: RESPONSES_404},
)
def unassign_agent_from_event(
    event_id: uuid.UUID,
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Utilisateur = Depends(require_users(Admin, Organisateur)),
) -> None:
    evenement = get_evenement(db, event_id)
    if evenement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    if not isinstance(user, Admin) and evenement.organisateur_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    agent = db.get(Utilisateur, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not isinstance(agent, Agent):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an agent")

    if agent in evenement.agents:
        evenement.agents.remove(agent)
        db.add(evenement)
        db.commit()
