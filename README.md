# Attendance Backend

FastAPI backend for a **BLE-based + facial recognition attendance system** built for a university setting. Students mark attendance by being physically near the professor's device (BLE proximity). Professors manage courses, sessions, enrollments, and can export attendance records.

---

## Tech stack

- **FastAPI** — async API framework
- **PostgreSQL 16** — primary database
- **SQLAlchemy 2 (asyncpg)** — async ORM
- **Alembic** — database migrations
- **python-jose** — JWT (HS256) with JTI-based token blocklist
- **passlib/bcrypt** — password hashing
- **slowapi** — rate limiting
- **openpyxl** — XLSX export

---

## API overview

### Auth — `/auth`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register (student or professor). Students require `matric_no`. Password must be 8+ chars with at least one digit. |
| POST | `/auth/login` | Login. Returns access + refresh tokens. Locks account for 15 min after 5 failed attempts. Rate-limited: 20/min. |
| POST | `/auth/logout` | Revoke access token (token blocklist). |
| POST | `/auth/refresh` | Exchange refresh token for a new pair (old refresh token is revoked). |
| POST | `/auth/change-password` | Change password (requires current password). |

### User Profile — `/users`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/users/me` | Get own profile. |
| PUT | `/users/me` | Update `full_name`. |

### Courses — `/courses`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/courses` | Create a course (professor only). |
| GET | `/courses` | List courses. Professors see their own; students see enrolled courses. |
| GET | `/courses/{id}` | Get course detail. |
| PUT | `/courses/{id}` | Update course name/code (owning professor only). |
| DELETE | `/courses/{id}` | Delete course (only if no sessions exist). |
| POST | `/courses/{id}/enroll` | Enroll a student by email or matric number (professor only). |
| POST | `/courses/{id}/enroll/bulk` | Bulk enroll via CSV file upload (professor only). |
| DELETE | `/courses/{id}/students/{student_id}` | Remove a student from a course. |
| GET | `/courses/{id}/stats` | Per-student attendance % (professor only). |
| GET | `/courses/{id}/attendance/export` | Export attendance as CSV or XLSX (`?format=csv` or `?format=xlsx`, optional `from_date`/`to_date`). |

### Enrollments — `/enrollments`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/enrollments` | Student self-enroll in a course. |
| DELETE | `/enrollments/{course_id}` | Student unenroll from a course. |

### Sessions — `/sessions`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions` | Start an attendance session for a course (professor only). 409 if active session exists. |
| GET | `/sessions` | List all sessions for the professor. |
| GET | `/sessions/{id}` | Get session detail + attendance records. |
| POST | `/sessions/{id}/token` | Register a rotating BLE token (validates BLE signature, expires in 25 s). |
| POST | `/sessions/{id}/end` | End session. |

### Attendance — `/attendance`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/attendance` | Mark attendance. Validates freshness, session status, BLE token, signature, enrollment, and deduplication. Always returns 200 with `success` + optional `error` field. |
| GET | `/attendance/me` | Student's own attendance history. Optional `?course_id=`, `?from_date=`, `?to_date=`. |

### Dashboard — `/dashboard`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/summary` | Professor summary: total courses, sessions this month, total enrolled students. |

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check → `{"status": "ok"}` |

---

## Attendance error codes

`POST /attendance` always returns HTTP 200. Check the `error` field:

| Error | Meaning |
|-------|---------|
| `stale_token` | Timestamp is older than 30 s |
| `session_ended` | Session is no longer active |
| `invalid_token` | BLE token not found or expired |
| `invalid_signature` | SHA256 sig mismatch |
| `not_enrolled` | Student is not enrolled in the course |
| `already_marked` | Attendance already recorded for this session |

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

`.env.example` defaults are wired to the Docker Compose database. Change `SECRET_KEY` and `ENCRYPTION_KEY` for local dev:

```
DATABASE_URL=postgresql+asyncpg://attendance:attendance@localhost:5433/attendance_db
SECRET_KEY=change-me-locally
ENCRYPTION_KEY=change-me-locally
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
ENVIRONMENT=development
```

> `ENCRYPTION_KEY` must match `EXPO_PUBLIC_ENCRYPTION_KEY` in the mobile app `.env` for BLE signature verification to work.

> The Docker Compose database runs on host port **5433** (not 5432) to avoid conflicts with a local PostgreSQL installation.

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

API: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## Running with Docker (full stack)

```bash
docker compose up --build
```

This starts both the database (port 5433) and the API (port 8000).

---

## Running tests

```bash
pytest
```

Tests use an isolated in-memory-equivalent test database (separate from your dev DB). Each test function gets a clean slate via table truncation.

---

## Deployment

**Recommended: Railway or Render** — both support FastAPI + PostgreSQL natively with zero configuration overhead.

### Railway (easiest)

1. Push your code to GitHub.
2. Create a new Railway project → **Deploy from GitHub repo**.
3. Add a **PostgreSQL** service from the Railway dashboard.
4. Set these environment variables in Railway:
   - `DATABASE_URL` — copy from Railway's PostgreSQL plugin (change `postgresql://` to `postgresql+asyncpg://`)
   - `SECRET_KEY` — generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ENCRYPTION_KEY` — must match mobile app
   - `ENVIRONMENT=production`
   - `ACCESS_TOKEN_EXPIRE_MINUTES=15`
   - `REFRESH_TOKEN_EXPIRE_DAYS=7`
   - `ALGORITHM=HS256`
5. Railway auto-detects the `Dockerfile` and builds it.
6. After deploy, run the migration via Railway's **shell** tab: `alembic upgrade head`

### Render

1. Push to GitHub.
2. New **Web Service** → connect your repo → Runtime: **Docker**.
3. Add a **PostgreSQL** database from Render dashboard.
4. Set the same environment variables as above (use Render's internal DB URL).
5. Add a **Deploy Hook** or use Render's start command to run `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Before going live

- Add your production domain to `_PROD_ORIGINS` in `app/main.py`.
- Use strong, randomly-generated `SECRET_KEY` and `ENCRYPTION_KEY`.
- Set `ENVIRONMENT=production` to lock CORS to your allowed origins.

---

## BLE signature format

The mobile app must compute:

```js
SHA256(JSON.stringify({s, t, ts}) + ENCRYPTION_KEY).slice(0, 10)
```

Key insertion order must be `{s, t, ts}`. This must match `verify_ble_signature()` in `app/core/security.py` exactly — do not change either side without updating both.

---

## Project structure

```
app/
  main.py              # App entry point, CORS, rate limiter, router registration
  config.py            # Settings loaded from .env
  database.py          # Async SQLAlchemy engine + session
  core/
    security.py        # JWT helpers, BLE signature verifier, token blocklist
    dependencies.py    # FastAPI auth dependencies (require_professor, require_student)
  models/              # SQLAlchemy ORM models
    user.py            # User (id, email, matric_no, password_hash, role, full_name, lockout fields)
    course.py          # Course, Enrollment
    session.py         # Session, SessionToken (BLE rotation)
    attendance.py      # Attendance (unique per session+student)
    blocklist.py       # TokenBlocklist (JTI-based revocation)
  schemas/             # Pydantic v2 request/response schemas
  routers/             # API route handlers
  services/            # Business logic
  ml/                  # Face recognition stub (not yet active)
alembic/
  versions/
    0001_initial_schema.py   # Initial tables + enums
    0002_security_improvements.py  # token_blocklist table + lockout columns
tests/
  conftest.py          # Test DB setup, fixtures
  test_auth.py
  test_sessions.py
  test_attendance.py
  test_courses.py
  test_users.py
  test_enrollments.py
  test_dashboard.py
```

---

## Contributing

Before opening a PR:
1. `uvicorn app.main:app --reload` — confirm the server starts
2. Hit your endpoint via `/docs`
3. `pytest` — no regressions
