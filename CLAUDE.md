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
  main.py              # App entry point, CORS, router registration
  config.py            # Pydantic-settings — reads from .env
  database.py          # Async engine, AsyncSessionLocal, Base, get_db()
  core/
    security.py        # COMPLETE — hash_password, verify_password, create_access_token,
                       #            create_refresh_token, decode_token, verify_ble_signature
    dependencies.py    # COMPLETE — require_professor, require_student, get_current_user_id
  models/              # COMPLETE — do not modify without a migration
    user.py            # User (id, email, matric_no, password_hash, role, full_name)
    course.py          # Course, Enrollment (student↔course many-to-many)
    session.py         # Session, SessionToken (BLE token rotation rows)
    attendance.py      # Attendance (UniqueConstraint on session_id+student_id)
  schemas/             # COMPLETE — Pydantic v2 request/response shapes
    auth.py            # RegisterRequest, LoginRequest, AuthResponse, RefreshRequest/Response
    session.py         # CreateSessionRequest, SessionTokenRequest, SessionOut, SessionTokenOut
    attendance.py      # MarkAttendanceRequest/Response, StudentHistoryResponse, SessionAttendanceResponse
    course.py          # CourseOut, CourseListResponse
  routers/             # Route handlers — all raise NotImplementedError, TODOs inside
    auth.py
    sessions.py
    attendance.py
    courses.py
    ml.py
  services/            # Business logic — all raise NotImplementedError except noted
    auth.py            # build_token_pair() COMPLETE — create_user/authenticate_user TODO
    session.py         # All TODO
    attendance.py      # Freshness check (Step 1) COMPLETE — Steps 2–6 TODO
    face.py            # All TODO (ML stub)
  ml/
    face_recognition.py  # FaceRecognitionModel stub — ML deps not yet installed
alembic/
  env.py               # Configured — strips +asyncpg, imports all models
  versions/
    0001_initial_schema.py  # All 6 tables + enums — run this first
tests/
  test_auth.py         # Skeleton — test cases written as comments
  test_sessions.py     # Skeleton
  test_attendance.py   # Skeleton
```

---

## What is already done (do not rewrite)

- All SQLAlchemy models with relationships, FK constraints, and the `UniqueConstraint("session_id", "student_id")` on attendance
- `core/security.py` — full JWT and BLE signature logic
- `core/dependencies.py` — all three auth dependency functions
- All Pydantic schemas
- Alembic migration `0001_initial_schema.py`
- `docker-compose.yml` (postgres + api), `Dockerfile`, `README.md`
- `tests/conftest.py` — test DB setup, `clean_tables` fixture (truncates all tables between tests), `client` fixture (HTTPX AsyncClient with DB override)

**Task 1 — Auth (merged PR #1):**
- `app/services/auth.py` — `create_user()` (duplicate email/matric 409, student matric validation 422, bcrypt hash), `authenticate_user()` (fetch by email+role, verify password), `build_token_pair()`
- `app/routers/auth.py` — `POST /auth/register`, `POST /auth/login`, `POST /auth/logout` (no-op), `POST /auth/refresh` (decode → assert type=="refresh" → re-fetch user → new pair)
- `tests/test_auth.py` — 9 passing tests covering register, duplicate, login, wrong password/role, refresh valid/invalid

**Task 2 — Sessions (merged):**
- `app/services/session.py` — `get_session()`, `create_session()` (409 on duplicate active), `register_token()` (BLE sig validation, expires_at = now+25s), `end_session()`
- `app/routers/sessions.py` — all 4 endpoints with ownership guards. Note: `SessionOut` has camelCase fields that don't auto-map from snake_case model — use `_to_session_out()` helper to construct manually
- `app/services/attendance.py` — `get_session_attendance()` implemented here (needed by sessions router); `mark_attendance()` and `get_student_history()` still raise NotImplementedError (Task 3)
- `tests/test_sessions.py` — 11 passing tests. Tests seed Course rows directly via `db` fixture (no courses API yet). `client` and `db` fixtures share the same AsyncSession instance via pytest fixture deduplication

---

## Shared files — do not modify without team coordination

These files are shared infrastructure. Editing them risks breaking everyone:

| File | Rule |
|---|---|
| `app/models/*.py` | Any change needs a new Alembic migration. Discuss first. |
| `app/core/security.py` | Frozen. BLE logic matches mobile app — do not change signature format. |
| `app/core/dependencies.py` | Frozen. |
| `app/database.py` | Frozen. |
| `alembic/env.py` | Frozen. |
| `requirements.txt` | Coordinate before adding deps — Tasks 4 and 5 both touch this file. |

---

## The 5 backend tasks

Each task owns a router + service + test file. There is zero file overlap between tasks 1–4 by design.

**Status key:** `pending` = not started | `in progress` = branch open | `done` = merged into master — do not re-implement

| Task | Branch | Status |
|---|---|---|
| 1. Auth | `feat/auth` | `done` |
| 2. Sessions | `feat/sessions` | `done` |
| 3. Attendance | `feat/attendance` | `pending` |
| 4. Courses | `feat/courses` | `pending` |
| 5. ML/Face | `feat/ml` | `pending` |

> **Claude instruction:** If a task above shows `done`, its files are complete. Do not reopen, rewrite, or re-examine them unless the user explicitly says something is broken. Read the file to understand what was built, not to improve it.


### Task 1 — `feat/auth` (DO THIS FIRST)

Every other endpoint requires a valid JWT. Nothing else can be tested until auth is working.

**Files:**
- `app/services/auth.py` — implement `create_user()` and `authenticate_user()`
- `app/routers/auth.py` — implement register, login, refresh

**Key rules:**
- `create_user()`: check duplicate email (409), duplicate matric_no (409), matric_no required for students (422), hash with `hash_password()`, insert, commit, refresh
- `authenticate_user()`: fetch by email+role (401 if not found), `verify_password()` (401 if wrong)
- Refresh: decode token, assert `payload["type"] == "refresh"`, re-fetch user from DB, issue new pair
- `tests/test_auth.py` — fill in all test cases

---

### Task 2 — `feat/sessions` (after Task 1 merges)

**Files:**
- `app/services/session.py` — implement `create_session`, `register_token`, `end_session`, `get_session`
- `app/routers/sessions.py` — implement all 4 endpoints

**Key rules:**
- `create_session()`: 409 if an active session already exists for this course
- `register_token()`: call `verify_ble_signature(s=str(session.id), t=t, ts=ts, sig=sig)` — 400 if fails; `expires_at = now + 25s`
- `end_session()`: set `status="ended"`, `ended_at=now()`
- All endpoints: verify ownership (professor owns the course/session) — 403 if not
- `tests/test_sessions.py` — fill in all test cases

---

### Task 3 — `feat/attendance` (after Task 2 merges)

**Files:**
- `app/services/attendance.py` — implement Steps 2–6 in `mark_attendance()`, implement `get_student_history()`, `get_session_attendance()`
- `app/routers/attendance.py` — wire up both endpoints

**Validation order in `mark_attendance()` (Step 1 already done):**
1. ~~Freshness check~~ (done)
2. Fetch session by `body.s` → `session_ended` if not active
3. Fetch `SessionToken` where `token_id == body.t` → `invalid_token` if not found or expired
4. `verify_ble_signature()` → `invalid_signature` if fails
5. Check for duplicate `(session_id, student_id)` → `already_marked` if exists
6. Insert `Attendance`, set `token.used = True`, commit

**Return shape:** `MarkAttendanceResponse(success=True/False, markedAt=..., error=...)`
- `tests/test_attendance.py` — fill in all test cases

---

### Task 4 — `feat/courses` (after Task 1 merges, parallel with Tasks 2–3)

**Files:**
- `app/routers/courses.py` — implement `list_courses` and `export_attendance`
- `app/services/course.py` — create this file; `get_courses_for_professor()`, `get_courses_for_student()`, `export_course_attendance()`
- `requirements.txt` — add `openpyxl>=3.1.0`

**Key rules:**
- `list_courses`: fetch user role from DB first; professors see their own courses; students see via enrollments; include `studentCount` (count of enrollments)
- Export columns: `Student Name`, `Matric No`, `Session Date`, `Marked At`
- Return `StreamingResponse` with `Content-Disposition: attachment; filename="attendance_{course_code}.{format}"`
- Support both `csv` (stdlib `csv` module) and `xlsx` (`openpyxl`)

---

### Task 5 — `feat/ml` (anytime, lowest priority)

**Coordinate with Task 4 on `requirements.txt` — both touch it.**

**Files:**
- `requirements.txt` — uncomment the ML block (`deepface`, `tensorflow`, `opencv-python`, `numpy`, `pillow`)
- `app/ml/face_recognition.py` — implement `FaceRecognitionModel` (load model once as singleton, `extract_embedding()`, `compare()`)
- `app/services/face.py` — implement `extract_embedding()`, `compare_embeddings()`, `verify_student_face()`
- `app/models/user.py` — uncomment `face_embedding = Column(LargeBinary, nullable=True)`
- Run `alembic revision --autogenerate -m "add face_embedding to users"` and commit the generated file
- `app/routers/ml.py` — implement `/ml/face/enroll` and `/ml/face/verify`

---

## Task merge order

```
Task 1 (auth)
    └── Task 2 (sessions)
            └── Task 3 (attendance)
    └── Task 4 (courses)       ← parallel with 2 and 3
Task 5 (ml)                    ← fully independent
```

Merge Task 1 before any PR review for Tasks 2–4. Tasks 3 and 4 can merge in either order.

---

## Frontend tasks (summary)

The frontend team consumes this API. Key integration points:

- **Auth flow** — `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`. Store `token` (access) and `refreshToken`. Access token expires in 15 min; auto-refresh using `refreshToken` (7 days).
- **Professor flow** — create course → start session (`POST /sessions`) → broadcast BLE → register rotating tokens (`POST /sessions/{id}/token` every ~20s) → end session → view/export attendance
- **Student flow** — scan BLE → parse payload (`s`, `t`, `ts`, `sig`) → `POST /attendance` → show result (`success`, `error`)
- **BLE signature** — mobile must compute `SHA256(JSON.stringify({s,t,ts}) + ENCRYPTION_KEY).slice(0,10)` where JSON key order is insertion order `{s, t, ts}`. This must match `verify_ble_signature()` in `core/security.py` exactly.
- **Attendance export** — `GET /courses/{id}/attendance/export?format=csv` or `?format=xlsx` with optional `from_date` / `to_date` query params (ISO date strings)

---

## Local dev

```bash
cp .env.example .env          # credentials match docker-compose defaults
docker compose up db -d       # start postgres
pip install -r requirements.txt
alembic upgrade head           # create all tables
uvicorn app.main:app --reload  # http://localhost:8000/docs
```

---

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://attendance:attendance@localhost:5432/attendance_db` |
| `SECRET_KEY` | JWT signing key — keep secret |
| `ENCRYPTION_KEY` | Must match `EXPO_PUBLIC_ENCRYPTION_KEY` in mobile app |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `ALGORITHM` | HS256 |
| `ENVIRONMENT` | `development` or `production` |
