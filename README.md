# Musper Solutions Platform

Custom platform for **Musper Solutions Ltd** — a business consultancy in Kigali, Rwanda.
This repo is the Phase 1 scaffold: project structure, tooling, base UI shell, database schema,
and a working `/health` endpoint. No auth, no AI integrations, no business logic yet.

## Stack

| Layer        | Tech                                                  |
|--------------|-------------------------------------------------------|
| Frontend     | React 19 + Vite + Tailwind CSS v3 + React Router      |
| Backend      | FastAPI + SQLAlchemy 2 + Alembic                      |
| Database     | PostgreSQL 16 (via Docker Compose)                    |
| Python deps  | [uv](https://docs.astral.sh/uv/) (`pyproject.toml`)   |
| Node deps    | npm                                                   |

## Repo layout

```
.
├── frontend/             # React + Vite app
│   └── src/{components,pages,hooks,services,styles,utils}
├── backend/              # FastAPI app
│   ├── app/{api,core,models,schemas,services,db}
│   ├── alembic/          # migrations
│   └── tests/
├── docker-compose.yml    # local Postgres 16
└── README.md
```

## Brand tokens (Tailwind theme)

Configured in [frontend/tailwind.config.js](frontend/tailwind.config.js):

| Token             | Hex       |
|-------------------|-----------|
| `musper-green`    | `#1F4E3D` |
| `musper-orange`   | `#E07B1F` |
| `musper-bg`       | `#F8F8F5` |
| `musper-ink`      | `#1A1A1A` |
| `musper-muted`    | `#6B6B6B` |

Fonts: **Poppins** (display) + **Inter** (body), loaded from Google Fonts in
[frontend/src/index.css](frontend/src/index.css).

## Prerequisites

- **Node.js** ≥ 20 and **npm**
- **Docker** (or Docker Desktop) for PostgreSQL
- **uv** for Python (install once):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # then either restart your shell or:
  source $HOME/.local/bin/env
  ```
  `uv` will download and pin Python 3.11 for the backend automatically — no system Python install needed.

---

## Quick start (run everything locally)

Open **three terminals**.

### 1. Database (Postgres 16)

```bash
docker compose up -d
# wait a few seconds, then verify:
docker compose ps
```

The DB listens on `localhost:5434` (mapped to the container's 5432) with credentials
`musper / musper` and DB `musper`. Data is persisted in the named volume `musper_pgdata`.

> **Why 5434?** Ports `5432` and `5433` were already in use on the dev machine this was
> scaffolded on. If you have nothing on `5432`, you can change `5434:5432` in
> [docker-compose.yml](docker-compose.yml) back to `5432:5432` and update
> `DATABASE_URL` in `backend/.env`.

To stop: `docker compose down`. To wipe data: `docker compose down -v`.

### 2. Backend (FastAPI on :8001)

```bash
cd backend
cp .env.example .env          # first time only
uv sync                       # installs Python 3.11 + deps into ./.venv
uv run alembic upgrade head   # creates all tables
uv run uvicorn app.main:app --reload --port 8001
```

Verify:

```bash
curl http://localhost:8001/health
# → {"status":"ok","env":"development"}
```

Interactive docs: <http://localhost:8001/docs>

> Port 8001 chosen because `:8000` was in use on this dev machine. Change `--port`
> freely (and update `VITE_API_URL` in `frontend/.env.local` to match).

### 3. Frontend (Vite on :5173)

```bash
cd frontend
npm install                   # first time only
npm run dev
```

Open <http://localhost:5173> — you should see the Musper Solutions placeholder
homepage with brand colors, Navbar, and Footer.

---

## End-to-end verification checklist

- [ ] `docker compose ps` shows `musper-postgres` healthy
- [ ] `curl localhost:8001/health` returns `{"status":"ok",...}`
- [ ] `docker exec musper-postgres psql -U musper -d musper -c '\dt'` lists 7 tables
      (`users`, `clients`, `diagnostic_sessions`, `chat_messages`, `reports`,
      `ratings`, `alembic_version`)
- [ ] <http://localhost:5173> renders the homepage with Musper green/orange branding

---

## Database schema (Phase 1)

Defined as SQLAlchemy 2 models in [backend/app/models/](backend/app/models/) and
materialized by [backend/alembic/versions/0001_initial.py](backend/alembic/versions/0001_initial.py).

| Table                  | Notes                                                     |
|------------------------|-----------------------------------------------------------|
| `users`                | UUID PK · `role ∈ {advisor, client}`                      |
| `clients`              | 1-to-1 with `users` (cascade delete)                      |
| `diagnostic_sessions`  | belongs to a client · `status ∈ {pending, in_progress, completed, abandoned}` |
| `chat_messages`        | belongs to a session · `role ∈ {user, assistant}`         |
| `reports`              | belongs to a session · JSONB `scores_json`, `content_json` · `is_shared` |
| `ratings`              | belongs to a session · `score ∈ [1, 5]` (CHECK constraint)|

To add a new migration later:

```bash
cd backend
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Tests

```bash
cd backend
uv run pytest
```

## What's intentionally not here (will land in later phases)

- Phase 2 — full marketing site content
- Phase 3 — JWT auth + bcrypt password hashing
- Phase 4 — Anthropic Claude API integration for the diagnostic chat
- Phase 5+ — Cal.com, Wave, Mailchimp integrations
