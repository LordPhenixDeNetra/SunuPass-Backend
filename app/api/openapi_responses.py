from __future__ import annotations

from app.schemas.error import ErrorResponse

RESPONSES_401 = {"model": ErrorResponse, "description": "Non authentifié (token manquant ou invalide)."}
RESPONSES_403 = {"model": ErrorResponse, "description": "Accès interdit (rôle insuffisant)."}
RESPONSES_404 = {"model": ErrorResponse, "description": "Ressource introuvable."}
RESPONSES_409 = {"model": ErrorResponse, "description": "Conflit (ressource déjà existante)."}
RESPONSES_422 = {"model": ErrorResponse, "description": "Erreur de validation."}
RESPONSES_500 = {"model": ErrorResponse, "description": "Erreur interne."}

AUTH_ERRORS = {401: RESPONSES_401, 422: RESPONSES_422, 500: RESPONSES_500}
AUTHZ_ERRORS = {401: RESPONSES_401, 403: RESPONSES_403, 422: RESPONSES_422, 500: RESPONSES_500}

