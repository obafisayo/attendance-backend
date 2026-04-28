import hashlib
import json
import time
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.course import Course


# --- fixtures & helpers ---

PROFESSOR = {
    "email": "prof@test.com",
    "password": "password123",
    "role": "professor",
    "full_name": "Test Professor",
}

PROFESSOR_2 = {
    "email": "prof2@test.com",
    "password": "password123",
    "role": "professor",
    "full_name": "Test Professor 2",
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
    course = Course(
        code="CSC401",
        name="Mobile Development",
        professor_id=uuid.UUID(professor_id),
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


def ble_sig(session_id: str, t: str, ts: int) -> str:
    payload = json.dumps({"s": session_id, "t": t, "ts": ts}, separators=(",", ":"))
    return hashlib.sha256((payload + settings.ENCRYPTION_KEY).encode()).hexdigest()[:10]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- tests ---


async def test_create_session(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    res = await client.post(
        "/sessions",
        json={"courseId": str(course.id)},
        headers=auth_header(token),
    )
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "active"
    assert data["courseId"] == str(course.id)
    assert data["endedAt"] is None


async def test_create_session_wrong_course_owner(client: AsyncClient, db: AsyncSession):
    token1, prof1_id = await register_and_login(client, PROFESSOR)
    token2, _ = await register_and_login(client, PROFESSOR_2)
    course = await create_course(db, prof1_id)

    res = await client.post(
        "/sessions",
        json={"courseId": str(course.id)},
        headers=auth_header(token2),
    )
    assert res.status_code == 403


async def test_create_session_as_student_fails(client: AsyncClient, db: AsyncSession):
    token, _ = await register_and_login(client, STUDENT)

    res = await client.post(
        "/sessions",
        json={"courseId": str(uuid.uuid4())},
        headers=auth_header(token),
    )
    assert res.status_code == 403


async def test_duplicate_active_session(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    await client.post("/sessions", json={"courseId": str(course.id)}, headers=auth_header(token))
    res = await client.post("/sessions", json={"courseId": str(course.id)}, headers=auth_header(token))

    assert res.status_code == 409


async def test_register_token(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(token)
    )
    session_id = sess_res.json()["id"]

    t = "tok_abc123"
    ts = int(time.time() * 1000)
    sig = ble_sig(session_id, t, ts)

    res = await client.post(
        f"/sessions/{session_id}/token",
        json={"t": t, "ts": ts, "sig": sig},
        headers=auth_header(token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["tokenId"] == t
    assert "expiresAt" in data


async def test_register_token_on_nonexistent_session(client: AsyncClient, db: AsyncSession):
    token, _ = await register_and_login(client, PROFESSOR)

    res = await client.post(
        f"/sessions/{uuid.uuid4()}/token",
        json={"t": "tok_abc"},
        headers=auth_header(token),
    )
    assert res.status_code == 404


async def test_register_token_on_ended_session(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(token)
    )
    session_id = sess_res.json()["id"]
    await client.post(f"/sessions/{session_id}/end", headers=auth_header(token))

    t = "tok_abc123"
    ts = int(time.time() * 1000)
    sig = ble_sig(session_id, t, ts)

    res = await client.post(
        f"/sessions/{session_id}/token",
        json={"t": t, "ts": ts, "sig": sig},
        headers=auth_header(token),
    )
    assert res.status_code == 400


async def test_end_session(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(token)
    )
    session_id = sess_res.json()["id"]

    res = await client.post(f"/sessions/{session_id}/end", headers=auth_header(token))
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ended"
    assert data["endedAt"] is not None


async def test_end_session_wrong_owner(client: AsyncClient, db: AsyncSession):
    token1, prof1_id = await register_and_login(client, PROFESSOR)
    token2, _ = await register_and_login(client, PROFESSOR_2)
    course = await create_course(db, prof1_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(token1)
    )
    session_id = sess_res.json()["id"]

    res = await client.post(f"/sessions/{session_id}/end", headers=auth_header(token2))
    assert res.status_code == 403


async def test_get_session_attendance_empty(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(token)
    )
    session_id = sess_res.json()["id"]

    res = await client.get(f"/sessions/{session_id}/attendance", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["records"] == []


async def test_get_session_attendance_wrong_owner(client: AsyncClient, db: AsyncSession):
    token1, prof1_id = await register_and_login(client, PROFESSOR)
    token2, _ = await register_and_login(client, PROFESSOR_2)
    course = await create_course(db, prof1_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(token1)
    )
    session_id = sess_res.json()["id"]

    res = await client.get(f"/sessions/{session_id}/attendance", headers=auth_header(token2))
    assert res.status_code == 403
