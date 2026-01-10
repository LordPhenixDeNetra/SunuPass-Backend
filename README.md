# SunuPass (API FastAPI)

API backend pour la gestion d’événements, billets et paiements, avec authentification JWT (access + refresh) et contrôle d’accès par rôles.

## Prérequis

- Python 3.11+
- (Optionnel) PostgreSQL si vous n’utilisez pas SQLite

## Installation

```bash
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

## Configuration

Le projet charge automatiquement un fichier `.env` (par défaut) via `ENV_FILE`.

Variables utiles (voir [.env.example](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/.env.example)) :

- `APP_NAME` (défaut: `SunuPass`)
- `DEBUG` (`true|false`)
- `DATABASE_URL` (ex: `sqlite:///./app.db` ou `postgresql+psycopg2://user:pass@host:5432/db`)
- `DB_ECHO` (`true|false`)
- `JWT_SECRET_KEY` (à changer en production)
- `JWT_ALGORITHM` (défaut: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (défaut: `60`)
- `REFRESH_TOKEN_EXPIRE_DAYS` (défaut: `30`)
- `ENV_FILE` (défaut: `.env`)

## Migrations (Alembic)

Créer/mettre à jour la base :

```bash
python -m alembic -c alembic.ini upgrade head
```

## Lancer l’API

```bash
python -m uvicorn main:app --reload
```

Endpoints de base :

- `GET /` → `{"message":"Hello World"}`
- `GET /health` → `{"status":"ok"}`
- Préfixe API v1 : `/api/v1`

## Authentification (access token + refresh token)

Le login renvoie un couple de tokens :

- `access_token` : à envoyer dans `Authorization: Bearer <token>` pour accéder aux routes protégées
- `refresh_token` : sert à régénérer un nouveau couple via rotation (l’ancien refresh token est révoqué)

Routes :

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login` → retourne `access_token` + `refresh_token`
- `POST /api/v1/auth/refresh` → rotation et renvoi d’un nouveau couple
- `POST /api/v1/auth/logout` → révoque le refresh token

Implémentation :

- JWT + hash refresh : [security.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/core/security.py)
- Stockage DB refresh : [refresh_token.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/models/refresh_token.py)

## Rôles (RBAC)

Rôles disponibles :

- `ADMIN`
- `ORGANISATEUR`
- `PARTICIPANT`

Exemples de règles appliquées :

- `payments` : admin uniquement
- `events` : admin ou organisateur (un organisateur ne voit/modifie que ses événements)
- `users` : `/me` pour l’utilisateur courant, listing global réservé admin

Référence : [enums.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/models/enums.py)

## Pagination

Les endpoints de liste renvoient une structure :

```json
{ "items": [], "total": 0, "limit": 50, "offset": 0 }
```

Schéma : [pagination.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/schemas/pagination.py)

## Structure du projet

- Entrée app FastAPI : [app/main.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/main.py)
- Point d’entrée ASGI : [main.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/main.py)
- Routes v1 : [router.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/api/v1/router.py)

