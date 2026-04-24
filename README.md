# Attendance Backend

FastAPI backend for the BLE-based attendance system. Handles authentication, session management, attendance marking, and facial recognition (ML stub — to be wired up later).

---

## Tech stack

- **FastAPI** — async API framework
- **PostgreSQL** — primary database
- **SQLAlchemy 2 (async)** — ORM
- **Alembic** — database migrations
- **python-jose** — JWT tokens
- **passlib/bcrypt** — password hashing

---

## Local setup

### Prerequisites

- Python 3.12+
- Docker + Docker Compose

### 1. Clone and enter the repo

```bash
git clone https://github.com/ATtPOrg/attendance-backend.git
cd attendance-backend
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

The defaults in `.env.example` are wired to the Docker Compose database — you only need to change `SECRET_KEY` and `ENCRYPTION_KEY` for local dev:

```
DATABASE_URL=postgresql+asyncpg://attendance:attendance@localhost:5432/attendance_db
SECRET_KEY=change-me-locally
ENCRYPTION_KEY=change-me-locally
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
ENVIRONMENT=development
```

> `ENCRYPTION_KEY` must match `EXPO_PUBLIC_ENCRYPTION_KEY` in the mobile app `.env` for BLE signature verification to work.

### 3. Start the database

```bash
docker compose up db -d
```

### 4. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

API is now running at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## Running with Docker (full stack)

To run both the database and the API in Docker:

```bash
docker compose up --build
```

---

## Running tests

```bash
pytest
```

---

## Project structure

```
app/
  main.py              # App entry point, router registration
  config.py            # Settings loaded from .env
  database.py          # Async SQLAlchemy engine + session
  core/
    security.py        # JWT helpers, BLE signature verifier, password hashing
    dependencies.py    # FastAPI auth dependencies (require_professor, require_student)
  models/              # SQLAlchemy ORM models
  schemas/             # Pydantic v2 request/response schemas
  routers/             # API route handlers (endpoints)
  services/            # Business logic called by routers
  ml/                  # Face recognition stub (DeepFace — not yet active)
alembic/
  versions/            # Migration files
tests/                 # pytest test files
```

---

## Contributing

Each open TODO is a self-contained unit of work. See the GitHub Issues for task assignments.

Before opening a PR:
1. Make sure the server starts (`uvicorn app.main:app --reload`)
2. Hit your endpoint manually via `/docs`
3. Run `pytest` and confirm no regressions
