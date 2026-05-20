# Badiboss Pay

Plateforme de paiement SaaS fintech pour centraliser les paiements des applications Badiboss.

## Architecture

- `app/`: backend FastAPI modulaire (API, core, DB, modèles, services, middleware, intégrations)
- `frontend/`: dashboard admin React + Vite + TypeScript + Tailwind
- `alembic/`: gestion de migrations SQLAlchemy

## Backend stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic Settings
- JWT Auth

## Demarrage backend

1. Creer et activer un environnement virtuel Python.
2. Installer les dependances:
   - `pip install -r requirements.txt`
3. Copier `.env.example` vers `.env` et configurer Railway PostgreSQL + SerdiPay.
4. Lancer l'API:
   - `uvicorn main:app --reload`

## Endpoints principaux

- `POST /auth/login`
- `POST /payments/create`
- `POST /payments/status`
- `POST /subscriptions/pay`
- `GET /transactions`
- `GET /apps`
- `POST /apps/create`
- `GET /analytics`
- `GET /dashboard/stats`
- `POST /webhooks/serdipay`

Compatibilite legacy preservee:

- `POST /api/test-token`
- `POST /api/test-payment`
- `POST /serdipay/callback`

## Migrations Alembic

- Generer migration:
  - `alembic revision --autogenerate -m "initial_schema"`
- Appliquer migration:
  - `alembic upgrade head`

## Frontend dashboard

1. `cd frontend`
2. `npm install`
3. `npm run dev`

Configurer l'URL API via `VITE_API_BASE_URL`.
