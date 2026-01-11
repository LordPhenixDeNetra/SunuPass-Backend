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
- `CORS_ORIGINS` (liste séparée par virgules, ex: `http://localhost:5173,http://localhost:3000`)
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

## Seed (données de démo)

```bash
python -m app.db.seed
```

Comptes créés :

- Admin: `admin@sunupass.local` / `Admin123!`
- Organisateur: `org1@sunupass.local` / `Org123!`
- Organisateur: `org2@sunupass.local` / `Org123!`
- Participants: `participant1@sunupass.local` à `participant4@sunupass.local` / `Pass123!`

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

## Endpoints (détaillés)

Base URL: `http://127.0.0.1:8000`

Docs :

- Swagger UI : `GET /docs`
- OpenAPI JSON : `GET /openapi.json`
- ReDoc : `GET /redoc`

### Root

- `GET /` : ping simple (`Hello World`)
- `GET /hello/{name}` : ping paramétré
- `GET /health` : état du service

### Auth (`/api/v1/auth`)

- `POST /api/v1/auth/register` : créer un compte
  - Body: `{ "email": "...", "password": "...", "nom_complet": "..." }`
  - Retour: utilisateur (sans mot de passe)
- `POST /api/v1/auth/login` : se connecter
  - Body: `{ "email": "...", "password": "..." }`
  - Retour: `{ "access_token": "...", "refresh_token": "..." }`
- `POST /api/v1/auth/refresh` : régénérer un couple de tokens (rotation)
  - Body: `{ "refresh_token": "..." }`
  - Retour: nouveau `{ "access_token": "...", "refresh_token": "..." }`
- `POST /api/v1/auth/logout` : invalider un refresh token
  - Body: `{ "refresh_token": "..." }`
  - Retour: `204`

### Users (`/api/v1/users`)

Authentification: `Authorization: Bearer <access_token>`

- `GET /api/v1/users/me` : récupérer son profil
- `PATCH /api/v1/users/me` : modifier son profil
  - Body: `{ "nom_complet": "..." }`
- `GET /api/v1/users` : lister les utilisateurs (ADMIN uniquement)
  - Query: `limit`, `offset`
- `GET /api/v1/users/{user_id}` : lire un utilisateur (ADMIN ou soi-même)
- `DELETE /api/v1/users/{user_id}` : supprimer un utilisateur (ADMIN uniquement)

### Events (`/api/v1/events`)

Authentification: `Authorization: Bearer <access_token>`

- `POST /api/v1/events` : créer un événement (ADMIN/ORGANISATEUR)
  - Règle: un ORGANISATEUR ne peut créer que pour lui-même (`organisateur_id == user.id`)
- `GET /api/v1/events` : lister les événements (ADMIN voit tout, ORGANISATEUR voit les siens)
  - Query: `limit`, `offset`
- `GET /api/v1/events/{event_id}` : détail d’un événement (organisateur propriétaire ou ADMIN)
- `PATCH /api/v1/events/{event_id}` : modifier un événement (organisateur propriétaire ou ADMIN)
- `DELETE /api/v1/events/{event_id}` : supprimer un événement (organisateur propriétaire ou ADMIN)

### Tickets (`/api/v1/tickets`)

Authentification: `Authorization: Bearer <access_token>`

- `POST /api/v1/tickets` : créer un billet (ADMIN ou le participant lui-même)
- `GET /api/v1/tickets` : lister les billets
  - ADMIN: peut filtrer par `participant_id` / `evenement_id`
  - PARTICIPANT/ORGANISATEUR: ne voit que ses propres billets
- `GET /api/v1/tickets/{ticket_id}` : lire un billet (ADMIN ou propriétaire)
- `PATCH /api/v1/tickets/{ticket_id}` : modifier un billet (ADMIN uniquement)
- `DELETE /api/v1/tickets/{ticket_id}` : supprimer un billet (ADMIN uniquement)

### Payments (`/api/v1/payments`)

Authentification: `Authorization: Bearer <access_token>`

- `POST /api/v1/payments` : créer un paiement (ADMIN uniquement)
- `GET /api/v1/payments` : lister les paiements (ADMIN uniquement)
  - Query: `limit`, `offset`, `billet_id`
- `GET /api/v1/payments/{payment_id}` : lire un paiement (ADMIN uniquement)
- `PATCH /api/v1/payments/{payment_id}` : modifier un paiement (ADMIN uniquement)
- `DELETE /api/v1/payments/{payment_id}` : supprimer un paiement (ADMIN uniquement)

### Rapport de tests

- Le runner génère un rapport complet dans : [endpoint_tests.md](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/reports/endpoint_tests.md)
- Commande: `python scripts/endpoint_test_runner.py`

## Structure du projet

- Entrée app FastAPI : [app/main.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/main.py)
- Point d’entrée ASGI : [main.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/main.py)
- Routes v1 : [router.py](file:///n:/OneDrive%20-%20Universit%C3%A9%20Cheikh%20Anta%20DIOP%20de%20DAKAR/PycharmProjects/SunuPass/app/api/v1/router.py)



<!-- uvicorn main:app --reload -->
