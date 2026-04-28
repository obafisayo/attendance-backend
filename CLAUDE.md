# CLAUDE.md — Attendance Backend

## How to use this file

**For Claude:** Read this entire file before touching any code. It tells you exactly what is done, what is not, and which files are frozen. Do not explore the codebase to re-derive what is already documented here — that wastes tokens. Most importantly: **never re-implement something listed under "What is already done".** When a task is marked complete below, treat every file it touched as finished and reviewed. Do not rewrite, refactor, or second-guess merged work unless the user explicitly asks.

**For team members:** This is your onboarding doc. Read it before writing a single line. It tells you which files belong to your task, which files to never touch, and the order PRs must be merged in. Two minutes here saves hours of merge conflicts.

**Keeping this file current:** When a task is merged, update the status table in "The 5 backend tasks" section from `pending` to `done` and move its files into the "What is already done" section. This is what prevents Claude from re-implementing work that already exists in the codebase.

---

## What this project is

A FastAPI backend for a **BLE (Bluetooth Low Energy) attendance system** built for a university setting. Students mark attendance by being physically near the professor's device (BLE proximity). Professors manage courses, sessions, and can export attendance records.

The mobile app broadcasts a **6-character token** (first 6 chars of a UUID, e.g. `a3f9c1`) over BLE. The backend receives `POST /attendance` with `{ "token": "a3f9c1" }`, looks up the `SessionToken` row, checks expiry and the `used` flag, then records attendance. No signature or timestamp fields are involved — the simplified BLE flow removed them.

---

## Tech stack

- **FastAPI** with async/await throughout
- **MySQL** — primary database (switched from PostgreSQL on `feat-backend-upgrade`)
- **SQLAlchemy 2 (aiomysql + PyMySQL)** — ORM, all queries are async; migrations use sync PyMySQL driver
- **Alembic** — migrations (sync driver, strips `+aiomysql` for migration runs)
- **python-jose** — JWT (HS256)
- **passlib/bcrypt** — password hashing
- **slowapi** — rate limiting (login endpoint: 10/minute)
- **Pydantic v2** — all schemas use `model_config = {"from_attributes": True}`
- **pytest + pytest-asyncio + httpx** — testing

---

## Repository layout

```
app/
  main.py              # App entry point, CORS, rate limiter, router registration
  config.py            # Pydantic-settings — reads from .env
  database.py          # Async engine (aiomysql), AsyncSessionLocal, Base, get_db()
  core/
    security.py        # COMPLETE — hash_password, verify_password, create_access_token,
                       #            create_refresh_token, decode_token, verify_ble_signature,
                       #            is_token_blocked(), block_token()
    dependencies.py    # COMPLETE — require_professor, require_student, get_current_user_id
                       #            (all three check token blocklist before returning)
  models/              # COMPLETE — do not modify without a migration
    user.py            # User (id, email, matric_no, password_hash, role, full_name,
                       #       failed_login_attempts, locked_until)
    course.py          # Course, Enrollment (student↔course many-to-many)
    session.py         # Session, SessionToken (BLE token rotation rows)
    attendance.py      # Attendance (UniqueConstraint on session_id+student_id)
    blocklist.py       # TokenBlocklist (jti, expires_at, blocked_at)
  schemas/             # COMPLETE — Pydantic v2 request/response shapes
    auth.py            # RegisterRequest, LoginRequest, AuthResponse, RefreshRequest/Response,
                       #   ChangePasswordRequest, UserOut
    session.py         # CreateSessionRequest, SessionTokenRequest, SessionOut, SessionTokenOut
    attendance.py      # MarkAttendanceRequest/Response, StudentHistoryResponse, SessionAttendanceResponse
    course.py          # CourseOut, CourseListResponse, CreateCourseRequest, UpdateCourseRequest,
                       #   StudentStatsRecord, CourseStatsResponse
    user.py            # ProfileResponse, UpdateProfileRequest
  routers/             # COMPLETE — all implemented
    auth.py            # register, login (rate-limited), logout (blocks token), refresh, change-password
    sessions.py        # list, create, get, register-token, end, get-attendance
    attendance.py      # mark attendance, student history
    courses.py         # list, create, get, update, delete, list-sessions, enroll, remove-student,
                       #   stats, export-attendance (CSV/XLSX)
    users.py           # GET /users/me, PUT /users/me
    dashboard.py       # GET /dashboard/summary (professor only)
    ml.py              # stub — not yet implemented
  services/            # COMPLETE except face.py
    auth.py            # create_user, authenticate_user (with lockout), build_token_pair, change_password
    session.py         # create_session, get_session, register_token, end_session
    attendance.py      # mark_attendance, get_student_history, get_session_attendance
    course.py          # get_courses_for_professor, get_courses_for_student, create_course,
                       #   update_course, delete_course, get_course_by_id, enroll_student,
                       #   remove_student, get_course_stats, export_course_attendance
    face.py            # All TODO (ML stub)
  ml/
    face_recognition.py  # FaceRecognitionModel stub — ML deps not yet installed
alembic/
  env.py               # Configured — strips +aiomysql, imports all models
  versions/
    0001_initial_schema.py  # All 6 tables + enums — run this first
    0002_security_improvements.py  # adds failed_login_attempts, locked_until, token_blocklist
tests/
  test_auth.py         # passing
  test_sessions.py     # passing
  test_attendance.py   # passing
  test_courses.py      # passing
```

---

## What is already done (do not rewrite)

- All SQLAlchemy models with relationships, FK constraints, and the `UniqueConstraint("session_id", "student_id")` on attendance
- `core/security.py` — full JWT, BLE signature, token blocklist logic (`is_token_blocked`, `block_token`)
- `core/dependencies.py` — all three auth dependency functions, each checks the token blocklist
- All Pydantic schemas
- Alembic migrations `0001_initial_schema.py` and `0002_security_improvements.py`
- `docker-compose.yml` (MySQL + api), `Dockerfile`, `README.md`
- `tests/conftest.py` — test DB setup, `clean_tables` fixture, `client` fixture (HTTPX AsyncClient with DB override)

**Task 1 — Auth (merged PR #1, enhanced on feat-backend-upgrade):**
- `app/services/auth.py` — `create_user()` (duplicate email/matric 409, student matric 422, bcrypt hash), `authenticate_user()` (lockout after 5 failed attempts → 429, 15-min window), `build_token_pair()`, `change_password()`
- `app/routers/auth.py` — `POST /auth/register`, `POST /auth/login` (rate-limited 10/min), `POST /auth/logout` (blocks token in blocklist), `POST /auth/refresh` (invalidates old refresh token + issues new pair), `POST /auth/change-password`
- `tests/test_auth.py` — passing

**Task 2 — Sessions (merged, expanded on feat-backend-upgrade):**
- `app/services/session.py` — `get_session()`, `create_session()` (409 on duplicate active), `register_token()` (takes 6-char `t` token, expires_at = now+25s), `end_session()`
- `app/routers/sessions.py` — `GET /sessions` (list all for professor), `POST /sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/token`, `POST /sessions/{id}/end`, `GET /sessions/{id}/attendance`. All endpoints use `_to_session_out()` helper (camelCase fields don't auto-map)
- `tests/test_sessions.py` — passing

**Task 3 — Attendance (merged):**
- `app/services/attendance.py` — `mark_attendance()` (all 6 steps: freshness, session active, token valid, BLE sig, duplicate, insert + token.used=True), `get_student_history()` (filterable by course_id, from_date, to_date), `get_session_attendance()`
- `app/routers/attendance.py` — `POST /attendance` (student auth), `GET /attendance/me` (student history with optional filters)
- `tests/test_attendance.py` — passing

**Task 4 — Courses (merged, greatly expanded on feat-backend-upgrade):**
- `app/services/course.py` — `get_courses_for_professor()`, `get_courses_for_student()`, `export_course_attendance()`, `create_course()`, `update_course()`, `delete_course()`, `get_course_by_id()`, `enroll_student()` (by email or matric_no), `remove_student()`, `get_course_stats()` (per-student attendance percentage)
- `app/routers/courses.py` — full CRUD (`GET/POST /courses`, `GET/PUT/DELETE /courses/{id}`), `GET /courses/{id}/sessions`, `POST /courses/{id}/enroll`, `DELETE /courses/{id}/students/{student_id}`, `GET /courses/{id}/stats`, `GET /courses/{id}/attendance/export` (CSV + XLSX)
- `requirements.txt` — `openpyxl>=3.1.0`, `slowapi>=0.1.9`
- `tests/test_courses.py` — passing

**feat-backend-upgrade — Security & profile additions:**
- `app/models/blocklist.py` — `TokenBlocklist` model (jti primary key, expires_at, blocked_at)
- `app/models/user.py` — added `failed_login_attempts` (Integer) and `locked_until` (DateTime) columns
- `alembic/versions/0002_security_improvements.py` — migration adding both columns + `token_blocklist` table
- `app/routers/users.py` — `GET /users/me`, `PUT /users/me` (update full_name and/or password)
- `app/routers/dashboard.py` — `GET /dashboard/summary` (professor only: total_courses, sessions_this_month, total_students)
- `app/schemas/user.py` — `ProfileResponse`, `UpdateProfileRequest`

---

## Shared files — do not modify without team coordination

| File | Rule |
|---|---|
| `app/models/*.py` | Any change needs a new Alembic migration. Discuss first. |
| `app/core/security.py` | Do not change `verify_ble_signature()` — signature format must match the mobile app exactly. |
| `app/core/dependencies.py` | Coordinate before changing — all routers depend on these. |
| `app/database.py` | Frozen. |
| `alembic/env.py` | Frozen. |
| `requirements.txt` | Coordinate before adding deps — Task 5 (ML) still touches this file. |

---

## Task status

**Status key:** `pending` = not started | `in progress` = branch open | `done` = merged/complete — do not re-implement

| Task | Status |
|---|---|
| 1. Auth | `done` |
| 2. Sessions | `done` |
| 3. Attendance | `done` |
| 4. Courses | `done` |
| 5. Backend upgrade (security, profiles, dashboard, MySQL) | `done` (on `feat-backend-upgrade`, pending merge) |
| 6. ML/Face | `pending` |

> **Claude instruction:** If a task above shows `done`, its files are complete. Do not reopen, rewrite, or re-examine them unless the user explicitly says something is broken.

---

### Task 6 — ML/Face (`feat/ml`, lowest priority)

**Files:**
- `requirements.txt` — uncomment the ML block (`deepface`, `tensorflow`, `opencv-python`, `numpy`, `pillow`)
- `app/ml/face_recognition.py` — implement `FaceRecognitionModel` (singleton, `extract_embedding()`, `compare()`)
- `app/services/face.py` — implement `extract_embedding()`, `compare_embeddings()`, `verify_student_face()`
- `app/models/user.py` — uncomment `face_embedding = Column(LargeBinary, nullable=True)`
- Run `alembic revision --autogenerate -m "add face_embedding to users"` and commit the generated file
- `app/routers/ml.py` — implement `/ml/face/enroll` and `/ml/face/verify`

---

## Frontend tasks (summary)

The frontend team consumes this API. Key integration points:

- **Auth flow** — `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/change-password`. Store `token` (access) and `refreshToken`. Access token expires in 15 min; auto-refresh using `refreshToken` (7 days). Login is rate-limited to 10/minute per IP.
- **Professor flow** — create course (`POST /courses`) → enroll students (`POST /courses/{id}/enroll`) → start session (`POST /sessions`) → broadcast BLE → register rotating tokens (`POST /sessions/{id}/token` every ~20s) → end session → view stats (`GET /courses/{id}/stats`) → export attendance
- **Student flow** — scan BLE → parse 6-char token → `POST /attendance` → show result (`success`, `error`)
- **Profile** — `GET /users/me`, `PUT /users/me` (update name/password)
- **Dashboard** — `GET /dashboard/summary` (professor only: total_courses, sessions_this_month, total_students)
- **Attendance mark** — `POST /attendance` with `{ "token": "a3f9c1" }`. No signature or timestamp fields. The backend finds the `SessionToken` by `token_id`, checks `expires_at` and `used`.
- **Attendance export** — `GET /courses/{id}/attendance/export?format=csv` or `?format=xlsx` with optional `from_date` / `to_date` query params (ISO date strings)

---

## Local dev

```bash
cp .env.example .env          # credentials match docker-compose defaults
docker compose up db -d       # MySQL on port 3306
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head           # creates all tables (runs 0001 + 0002)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` is required so Android devices on the same WiFi can reach the API. Set `EXPO_PUBLIC_API_URL=http://<your-wifi-ip>:8000` in the mobile `.env`. The default `127.0.0.1` bind is only reachable from the same machine.

Add Windows Firewall rules if needed (run as Administrator):
```cmd
netsh advfirewall firewall add rule name="FastAPI Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="Expo Metro" dir=in action=allow protocol=TCP localport=8081
```

---

## Environment variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `mysql+aiomysql://attendance:attendance@localhost:3307/attendance_db` |
| `SECRET_KEY` | JWT signing key — keep secret |
| `ENCRYPTION_KEY` | Must match `EXPO_PUBLIC_ENCRYPTION_KEY` in mobile app |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `ALGORITHM` | HS256 |
| `ENVIRONMENT` | `development` (CORS open) or `production` (CORS locked to `_PROD_ORIGINS` in main.py) |
