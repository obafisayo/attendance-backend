import hashlib
import json
import time
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.course import Course, Enrollment


# --- helpers ---

PROFESSOR = {
    "email": "prof@test.com",
    "password": "password123",
    "role": "professor",
    "full_name": "Test Professor",
}

STUDENT = {
    "email": "student@test.com",
    "password": "password123",
    "role": "student",
    "full_name": "Test Student",
    "matric_no": "MAT001",
}


async def register_and_login(client: AsyncClient, user_data: dict) -> tuple[str, str]:
    res = await client.post("/auth/register", json=user_data)
    data = res.json()
    return data["token"], data["user"]["id"]


async def create_course(db: AsyncSession, professor_id: str) -> Course:
    course = Course(code="CSC401", name="Mobile Development", professor_id=uuid.UUID(professor_id))
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def enroll_student(db: AsyncSession, student_id: str, course_id: uuid.UUID):
    db.add(Enrollment(student_id=uuid.UUID(student_id), course_id=course_id))
    await db.commit()


def ble_sig(session_id: str, t: str, ts: int) -> str:
    payload = json.dumps({"s": session_id, "t": t, "ts": ts}, separators=(",", ":"))
    return hashlib.sha256((payload + settings.ENCRYPTION_KEY).encode()).hexdigest()[:10]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def setup_session_with_token(client: AsyncClient, db: AsyncSession) -> tuple[str, str, str, int]:
    """Returns: (student_token, session_id, token_id, ts)"""
    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions",
        json={"courseId": str(course.id)},
        headers=auth_header(prof_token),
    )
    session_id = sess_res.json()["id"]

    t = "tok_abc123"
    ts = int(time.time() * 1000)
    sig = ble_sig(session_id, t, ts)
    await client.post(
        f"/sessions/{session_id}/token",
        json={"t": t, "ts": ts, "sig": sig},
        headers=auth_header(prof_token),
    )

    student_token, student_id = await register_and_login(client, STUDENT)
    await enroll_student(db, student_id, course.id)
    return student_token, session_id, t, ts


# --- tests ---


async def test_mark_attendance_success(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t, _ = await setup_session_with_token(client, db)

    ts = int(time.time() * 1000)
    res = await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts, "sig": ble_sig(session_id, t, ts)},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["markedAt"] is not None


async def test_stale_token(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t, _ = await setup_session_with_token(client, db)

    stale_ts = int(time.time() * 1000) - 60_000
    res = await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": stale_ts, "sig": ble_sig(session_id, t, stale_ts)},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "stale_token"


async def test_inactive_session(client: AsyncClient, db: AsyncSession):
    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(prof_token)
    )
    session_id = sess_res.json()["id"]

    t = "tok_abc123"
    ts = int(time.time() * 1000)
    sig = ble_sig(session_id, t, ts)
    await client.post(
        f"/sessions/{session_id}/token",
        json={"t": t, "ts": ts, "sig": sig},
        headers=auth_header(prof_token),
    )
    await client.post(f"/sessions/{session_id}/end", headers=auth_header(prof_token))

    student_token, student_id = await register_and_login(client, STUDENT)
    await enroll_student(db, student_id, course.id)

    ts2 = int(time.time() * 1000)
    res = await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts2, "sig": ble_sig(session_id, t, ts2)},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "session_ended"


async def test_invalid_token(client: AsyncClient, db: AsyncSession):
    student_token, session_id, _, _ = await setup_session_with_token(client, db)

    t = "nonexistent_token"
    ts = int(time.time() * 1000)
    res = await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts, "sig": ble_sig(session_id, t, ts)},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "invalid_token"


async def test_bad_signature(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t, _ = await setup_session_with_token(client, db)

    ts = int(time.time() * 1000)
    res = await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts, "sig": "badsig12345"},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "invalid_signature"


async def test_duplicate_mark(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t, _ = await setup_session_with_token(client, db)

    ts = int(time.time() * 1000)
    payload = {"s": session_id, "t": t, "ts": ts, "sig": ble_sig(session_id, t, ts)}
    await client.post("/attendance", json=payload, headers=auth_header(student_token))

    ts2 = int(time.time() * 1000)
    payload2 = {"s": session_id, "t": t, "ts": ts2, "sig": ble_sig(session_id, t, ts2)}
    res = await client.post("/attendance", json=payload2, headers=auth_header(student_token))
    assert res.status_code == 200
    assert res.json()["error"] == "already_marked"


async def test_get_student_history(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t, _ = await setup_session_with_token(client, db)

    ts = int(time.time() * 1000)
    await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts, "sig": ble_sig(session_id, t, ts)},
        headers=auth_header(student_token),
    )

    res = await client.get("/attendance/me", headers=auth_header(student_token))
    assert res.status_code == 200
    data = res.json()
    assert len(data["records"]) == 1
    assert data["records"][0]["course_code"] == "CSC401"


async def test_get_history_filtered_by_course_id(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t, _ = await setup_session_with_token(client, db)

    ts = int(time.time() * 1000)
    await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts, "sig": ble_sig(session_id, t, ts)},
        headers=auth_header(student_token),
    )

    res = await client.get(
        f"/attendance/me?course_id={uuid.uuid4()}",
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert len(res.json()["records"]) == 0

    res = await client.get("/attendance/me", headers=auth_header(student_token))
    assert res.status_code == 200
    assert len(res.json()["records"]) == 1
