# CLAUDE.md — Attendance Backend

## How to use this file

**For Claude:** Read this entire file before touching any code. It tells you exactly what is done, what is not, and which files are frozen. Do not explore the codebase to re-derive what is already documented here — that wastes tokens. Most importantly: **never re-implement something listed under "What is already done".** When a task is marked complete below, treat every file it touched as finished and reviewed. Do not rewrite, refactor, or second-guess merged work unless the user explicitly asks.

**For team members:** This is your onboarding doc. Read it before writing a single line. It tells you which files belong to your task, which files to never touch, and the order PRs must be merged in. Two minutes here saves hours of merge conflicts.

**Keeping this file current:** When a task is merged, update the status table in "The 5 backend tasks" section from `pending` to `done` and move its files into the "What is already done" section. This is what prevents Claude from re-implementing work that already exists in the codebase.

---

## What this project is

A FastAPI backend for a **BLE (Bluetooth Low Energy) + facial recognition attendance system** built for a university setting. Students mark attendance by being physically near the professor's device (BLE proximity) + optional face verification. Professors manage courses, sessions, and can export attendance records.

The mobile app (separate repo) broadcasts a BLE payload containing a session ID (`s`), rotating token ID (`t`), timestamp (`ts`), and a truncated SHA256 signature (`sig`). The backend validates the signature using a shared `ENCRYPTION_KEY` that must match `EXPO_PUBLIC_ENCRYPTION_KEY` in the mobile app `.env`.

---

## Tech stack

- **FastAPI** with async/await throughout
- **PostgreSQL 16** — primary database
- **SQLAlchemy 2 (asyncpg)** — ORM, all queries are async
- **Alembic** — migrations (sync driver, strips `+asyncpg` for migration runs)
- **python-jose** — JWT (HS256)
- **passlib/bcrypt** — password hashing
- **Pydantic v2** — all schemas use `model_config = {"from_attributes": True}`
- **pytest + pytest-asyncio + httpx** — testing

---

## Repository layout

```
app/
  main.py              # App entry point, CORS, rate limiter, router registration
  config.py            # Pydantic-settings — reads from .env
  database.py          # Async engine, AsyncSessionLocal, Base, get_db()
  core/
    security.py        # COMPLETE — JWT helpers, BLE signature, token blocklist (block/check)
    dependencies.py    # COMPLETE — require_professor, require_student, get_current_user_id
                       #            (all three check token blocklist via DB)
  models/              # COMPLETE — do not modify without a migration
    user.py            # User (id, email, matric_no, password_hash, role, full_name,
                       #        failed_login_attempts, locked_until)
    course.py          # Course, Enrollment (student↔course many-to-many)
    session.py         # Session, SessionToken (BLE token rotation rows)
    attendance.py      # Attendance (UniqueConstraint on session_id+student_id)
    blocklist.py       # TokenBlocklist (jti PK, expires_at, blocked_at)
  schemas/             # COMPLETE — Pydantic v2 request/response shapes
    auth.py            # RegisterRequest (password validator), LoginRequest, AuthResponse,
                       #   RefreshRequest/Response, ChangePasswordRequest
    session.py         # CreateSessionRequest, SessionTokenRequest, SessionOut, SessionTokenOut
    attendance.py      # MarkAttendanceRequest/Response (incl. not_enrolled error),
                       #   StudentHistoryResponse, SessionAttendanceResponse
    course.py          # CourseOut, CourseListResponse, CreateCourseRequest, UpdateCourseRequest,
                       #   StudentStatsRecord, CourseStatsResponse, BulkEnrollResponse
    user.py            # ProfileResponse, UpdateProfileRequest
  routers/             # COMPLETE — all endpoints wired up
    auth.py            # register, login (rate-limited), logout, refresh, change-password
    sessions.py        # create, list, get, register-token, end
    attendance.py      # mark, student-history
    courses.py         # CRUD, enroll, bulk-enroll, remove-student, stats, export
    enrollments.py     # student self-enroll, unenroll
    users.py           # get/update profile
    dashboard.py       # professor summary
    ml.py              # stub (not yet implemented)
  services/            # COMPLETE (except ML)
    auth.py            # create_user, authenticate_user (lockout logic), build_token_pair,
                       #   change_password
    session.py         # get_session, create_session, register_token, end_session
    attendance.py      # mark_attendance (7 steps incl. enrollment check),
                       #   get_student_history, get_session_attendance
    course.py          # create_course, get_course_by_id, update_course, delete_course,
                       #   enroll_student_by_identifier, bulk_enroll_students,
                       #   remove_student, get_course_stats,
                       #   get_courses_for_professor, get_courses_for_student,
                       #   export_course_attendance
    face.py            # stub (ML — not yet implemented)
  ml/
    face_recognition.py  # FaceRecognitionModel stub — ML deps not yet installed
alembic/
  env.py               # Configured — strips +asyncpg, imports all models
  versions/
    0001_initial_schema.py       # Initial tables + enums
    0002_security_improvements.py  # token_blocklist table + lockout columns on users
tests/
  conftest.py          # Test DB setup, clean_tables + client fixtures
  test_auth.py         # 16 passing tests (register, login, lockout, refresh rotation,
                       #   logout blocklist, change-password)
  test_sessions.py     # 11 passing tests
  test_attendance.py   # 8 passing tests (incl. not_enrolled guard)
  test_courses.py      # 8 passing tests (incl. CSV/XLSX export)
  test_users.py        # 5 passing tests
  test_enrollments.py  # 6 passing tests
  test_dashboard.py    # 3 passing tests
```

---

## What is already done (do not rewrite)

- All SQLAlchemy models with relationships, FK constraints, and the `UniqueConstraint("session_id", "student_id")` on attendance
- `core/security.py` — full JWT + BLE signature logic + token blocklist (`block_token`, `is_token_blocked`)
- `core/dependencies.py` — all three auth dependency functions (each checks token blocklist via DB)
- All Pydantic schemas
- Alembic migrations `0001_initial_schema.py` and `0002_security_improvements.py`
- `docker-compose.yml` (postgres port **5433**, api), `Dockerfile`
- `tests/conftest.py` — test DB setup, `clean_tables` fixture, `client` and `db` fixtures

**Task 1 — Auth (done):**
- `app/services/auth.py` — `create_user()` (duplicate email/matric 409, student matric 422, bcrypt hash, password policy enforced by schema), `authenticate_user()` (lockout after 5 failures for 15 min, 429 response), `change_password()`
- `app/routers/auth.py` — `POST /auth/register`, `POST /auth/login` (rate-limited 20/min), `POST /auth/logout` (real token revocation), `POST /auth/refresh` (rotation — old token revoked, blocklist check before issuing new), `POST /auth/change-password`
- `tests/test_auth.py` — 16 passing tests

**Task 2 — Sessions (done):**
- `app/services/session.py` — `get_session()`, `create_session()` (409 on duplicate active), `register_token()` (BLE sig validation, expires_at = now+25s), `end_session()`
- `app/routers/sessions.py` — POST create, GET list, GET detail, POST token, POST end — all with ownership guards. Note: `SessionOut` has camelCase fields → use `_to_session_out()` helper
- `app/services/attendance.py` — `get_session_attendance()` (needed by sessions router)
- `tests/test_sessions.py` — 11 passing tests

**Task 3 — Attendance (done):**
- `app/services/attendance.py` — `mark_attendance()` (7 steps: freshness, session active, token valid, BLE sig, **enrollment check**, duplicate, insert + token.used=True), `get_student_history()` (filterable)
- `app/routers/attendance.py` — `POST /attendance`, `GET /attendance/me`
- `tests/test_attendance.py` — 8 passing tests

**Task 4 — Courses (done):**
- `app/services/course.py` — full CRUD, `enroll_student_by_identifier()` (by email or matric), `bulk_enroll_students()`, `remove_student()`, `get_course_stats()`, `export_course_attendance()` (CSV + XLSX, date-filterable)
- `app/routers/courses.py` — POST/GET/PUT/DELETE /courses, POST enroll, POST enroll/bulk (CSV upload), DELETE student, GET stats, GET export
- `requirements.txt` — added `openpyxl>=3.1.0`, `slowapi>=0.1.9`
- `tests/test_courses.py` — 8 passing tests

**Beyond original tasks — Security & UX improvements (all done):**
- `app/models/blocklist.py` + migration `0002` — JTI-based token blocklist table
- `app/models/user.py` — added `failed_login_attempts`, `locked_until` columns (migration `0002`)
- `app/schemas/auth.py` — `ChangePasswordRequest`; `RegisterRequest` password validator (8+ chars, 1+ digit)
- `app/routers/users.py` + `app/schemas/user.py` — `GET /users/me`, `PUT /users/me`
- `app/routers/enrollments.py` — `POST /enrollments` (student self-enroll), `DELETE /enrollments/{course_id}`
- `app/routers/dashboard.py` — `GET /dashboard/summary` (professor: total courses, sessions this month, total students)
- `app/main.py` — slowapi rate limiter wired, CORS locked in production
- `tests/test_users.py`, `tests/test_enrollments.py`, `tests/test_dashboard.py` — all passing

---

## Shared files — do not modify without team coordination

| File | Rule |
|---|---|
| `app/models/*.py` | Any change needs a new Alembic migration. Discuss first. |
| `app/core/security.py` | Frozen. BLE logic matches mobile app — do not change signature format. |
| `app/core/dependencies.py` | Frozen. |
| `app/database.py` | Frozen. |
| `alembic/env.py` | Frozen. |
| `requirements.txt` | Coordinate before adding deps — Task 5 (ML) will touch this file. |

---

## Task status

| Task | Status |
|---|---|
| 1. Auth | `done` |
| 2. Sessions | `done` |
| 3. Attendance | `done` |
| 4. Courses + Enrollments + Dashboard + Users | `done` |
| 5. ML/Face | `pending` |

> **Claude instruction:** Tasks 1–4 are complete. Do not reopen, rewrite, or re-examine their files unless the user explicitly says something is broken.

---

### Task 5 — `feat/ml` (lowest priority, not yet started)

**Files:**
- `requirements.txt` — uncomment the ML block (`deepface`, `tensorflow`, `opencv-python`, `numpy`, `pillow`)
- `app/ml/face_recognition.py` — implement `FaceRecognitionModel` (load model once as singleton, `extract_embedding()`, `compare()`)
- `app/services/face.py` — implement `extract_embedding()`, `compare_embeddings()`, `verify_student_face()`
- `app/models/user.py` — uncomment `face_embedding = Column(LargeBinary, nullable=True)`
- Run `alembic revision --autogenerate -m "add face_embedding to users"` and commit the generated file
- `app/routers/ml.py` — implement `/ml/face/enroll` and `/ml/face/verify`

---

## Frontend / mobile integration points

- **Auth flow** — `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`. Store `token` (access, 15 min) and `refreshToken` (7 days). Auto-refresh when 401 is returned.
- **Logout** — `POST /auth/logout` with Bearer token. Token is immediately revoked server-side.
- **Professor flow** — create course → enroll students (self-enroll or professor-enroll) → start session (`POST /sessions`) → broadcast BLE → register rotating tokens (`POST /sessions/{id}/token` every ~20 s) → end session → view stats (`GET /courses/{id}/stats`) → export attendance
- **Student flow** — enroll in courses (`POST /enrollments`) → scan BLE → parse payload (`s`, `t`, `ts`, `sig`) → `POST /attendance` → show result (`success`, `error`). Student must be enrolled before attendance can be marked.
- **BLE signature** — mobile must compute `SHA256(JSON.stringify({s,t,ts}) + ENCRYPTION_KEY).slice(0,10)` where JSON key order is insertion order `{s, t, ts}`. This must match `verify_ble_signature()` in `core/security.py` exactly. **Do not change either side without updating both.**
- **Attendance export** — `GET /courses/{id}/attendance/export?format=csv` or `?format=xlsx` with optional `from_date` / `to_date` query params (ISO date strings). Professor only.
- **Dashboard** — `GET /dashboard/summary` — professor-only summary card data.

---

## Local dev

```bash
cp .env.example .env          # credentials match docker-compose defaults
docker compose up db -d       # start postgres on host port 5433
pip install -r requirements.txt
alembic upgrade head           # run both migrations
uvicorn app.main:app --reload  # http://localhost:8000/docs
```

---

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://attendance:attendance@localhost:5433/attendance_db` (host port 5433) |
| `SECRET_KEY` | JWT signing key — keep secret, use a random 32-byte hex string in production |
| `ENCRYPTION_KEY` | Must match `EXPO_PUBLIC_ENCRYPTION_KEY` in mobile app |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `ALGORITHM` | HS256 |
| `ENVIRONMENT` | `development` (CORS open) or `production` (CORS locked to `_PROD_ORIGINS` in main.py) |
