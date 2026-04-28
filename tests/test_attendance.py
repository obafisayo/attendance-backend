import uuid
from datetime import datetime, timezone, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.course import Course
from app.models.session import SessionToken


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


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def setup_session_with_token(client: AsyncClient, db: AsyncSession) -> tuple[str, str, str]:
    """Returns: (student_token, session_id, token_id)"""
    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions",
        json={"courseId": str(course.id)},
        headers=auth_header(prof_token),
    )
    session_id = sess_res.json()["id"]

    t = "tok001"
    await client.post(
        f"/sessions/{session_id}/token",
        json={"t": t},
        headers=auth_header(prof_token),
    )

    student_token, _ = await register_and_login(client, STUDENT)
    return student_token, session_id, t


# --- tests ---


async def test_mark_attendance_success(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t = await setup_session_with_token(client, db)

    res = await client.post(
        "/attendance",
        json={"token": t},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["markedAt"] is not None


async def test_expired_token(client: AsyncClient, db: AsyncSession):
    """Token found in DB but expires_at is in the past → invalid_token."""
    student_token, session_id, t = await setup_session_with_token(client, db)

    # Expire the token directly
    await db.execute(
        update(SessionToken)
        .where(SessionToken.token_id == t)
        .values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    )
    await db.commit()

    res = await client.post(
        "/attendance",
        json={"token": t},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "invalid_token"


async def test_inactive_session(client: AsyncClient, db: AsyncSession):
    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(prof_token)
    )
    session_id = sess_res.json()["id"]

    t = "tok001"
    await client.post(
        f"/sessions/{session_id}/token",
        json={"t": t},
        headers=auth_header(prof_token),
    )
    await client.post(f"/sessions/{session_id}/end", headers=auth_header(prof_token))

    student_token, _ = await register_and_login(client, STUDENT)
    res = await client.post(
        "/attendance",
        json={"token": t},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "session_ended"


async def test_invalid_token(client: AsyncClient, db: AsyncSession):
    student_token, session_id, _ = await setup_session_with_token(client, db)

    res = await client.post(
        "/attendance",
        json={"token": "nonexistent"},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "invalid_token"


async def test_used_token(client: AsyncClient, db: AsyncSession):
    """Token already used → invalid_token."""
    student_token, session_id, t = await setup_session_with_token(client, db)

    await db.execute(
        update(SessionToken)
        .where(SessionToken.token_id == t)
        .values(used=True)
    )
    await db.commit()

    res = await client.post(
        "/attendance",
        json={"token": t},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "invalid_token"


async def test_duplicate_mark(client: AsyncClient, db: AsyncSession):
    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post(
        "/sessions", json={"courseId": str(course.id)}, headers=auth_header(prof_token)
    )
    session_id = sess_res.json()["id"]

    # Register first token, mark attendance
    t1 = "tok001"
    await client.post(f"/sessions/{session_id}/token", json={"t": t1}, headers=auth_header(prof_token))
    student_token, _ = await register_and_login(client, STUDENT)
    res = await client.post("/attendance", json={"token": t1}, headers=auth_header(student_token))
    assert res.json()["success"] is True

    # Register a second fresh token — should get already_marked
    t2 = "tok002"
    await client.post(f"/sessions/{session_id}/token", json={"t": t2}, headers=auth_header(prof_token))
    res = await client.post("/attendance", json={"token": t2}, headers=auth_header(student_token))
    assert res.status_code == 200
    assert res.json()["error"] == "already_marked"


async def test_get_student_history(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t = await setup_session_with_token(client, db)

    await client.post(
        "/attendance",
        json={"token": t},
        headers=auth_header(student_token),
    )

    res = await client.get("/attendance/me", headers=auth_header(student_token))
    assert res.status_code == 200
    data = res.json()
    assert len(data["records"]) == 1
    assert data["records"][0]["course_code"] == "CSC401"


async def test_get_history_filtered_by_course_id(client: AsyncClient, db: AsyncSession):
    student_token, session_id, t = await setup_session_with_token(client, db)

    await client.post(
        "/attendance",
        json={"token": t},
        headers=auth_header(student_token),
    )

    # filter by a random course_id — should return 0 records
    res = await client.get(
        f"/attendance/me?course_id={uuid.uuid4()}",
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert len(res.json()["records"]) == 0

    # no filter — should return 1 record
    res = await client.get("/attendance/me", headers=auth_header(student_token))
    assert res.status_code == 200
    assert len(res.json()["records"]) == 1
