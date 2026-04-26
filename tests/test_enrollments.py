import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course


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

STUDENT_2 = {
    "email": "student2@test.com",
    "password": "password123",
    "role": "student",
    "full_name": "Test Student 2",
    "matric_no": "MAT002",
}


async def register_and_login(client: AsyncClient, user_data: dict) -> tuple[str, str]:
    res = await client.post("/auth/register", json=user_data)
    data = res.json()
    return data["token"], data["user"]["id"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def create_course(db: AsyncSession, professor_id: str) -> Course:
    course = Course(code="CSC401", name="Mobile Dev", professor_id=uuid.UUID(professor_id))
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def test_student_self_enroll(client: AsyncClient, db: AsyncSession):
    _, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    student_token, _ = await register_and_login(client, STUDENT)
    res = await client.post("/enrollments", json={"course_id": str(course.id)}, headers=auth_header(student_token))
    assert res.status_code == 201
    assert res.json()["course_code"] == "CSC401"


async def test_student_cannot_enroll_twice(client: AsyncClient, db: AsyncSession):
    _, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    student_token, _ = await register_and_login(client, STUDENT)
    await client.post("/enrollments", json={"course_id": str(course.id)}, headers=auth_header(student_token))
    res = await client.post("/enrollments", json={"course_id": str(course.id)}, headers=auth_header(student_token))
    assert res.status_code == 409


async def test_student_enroll_unknown_course(client: AsyncClient, db: AsyncSession):
    student_token, _ = await register_and_login(client, STUDENT)
    res = await client.post("/enrollments", json={"course_id": str(uuid.uuid4())}, headers=auth_header(student_token))
    assert res.status_code == 404


async def test_professor_cannot_self_enroll(client: AsyncClient, db: AsyncSession):
    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    res = await client.post("/enrollments", json={"course_id": str(course.id)}, headers=auth_header(prof_token))
    assert res.status_code == 403


async def test_student_unenroll(client: AsyncClient, db: AsyncSession):
    _, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    student_token, _ = await register_and_login(client, STUDENT)
    await client.post("/enrollments", json={"course_id": str(course.id)}, headers=auth_header(student_token))
    res = await client.delete(f"/enrollments/{course.id}", headers=auth_header(student_token))
    assert res.status_code == 204


async def test_attendance_blocked_if_not_enrolled(client: AsyncClient, db: AsyncSession):
    import hashlib, json, time
    from app.config import settings

    prof_token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    sess_res = await client.post("/sessions", json={"courseId": str(course.id)}, headers=auth_header(prof_token))
    session_id = sess_res.json()["id"]

    t = "tok_abc123"
    ts = int(time.time() * 1000)
    sig = hashlib.sha256(
        (json.dumps({"s": session_id, "t": t, "ts": ts}, separators=(",", ":")) + settings.ENCRYPTION_KEY).encode()
    ).hexdigest()[:10]
    await client.post(f"/sessions/{session_id}/token", json={"t": t, "ts": ts, "sig": sig}, headers=auth_header(prof_token))

    # student is NOT enrolled
    student_token, _ = await register_and_login(client, STUDENT)
    ts2 = int(time.time() * 1000)
    sig2 = hashlib.sha256(
        (json.dumps({"s": session_id, "t": t, "ts": ts2}, separators=(",", ":")) + settings.ENCRYPTION_KEY).encode()
    ).hexdigest()[:10]
    res = await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts2, "sig": sig2},
        headers=auth_header(student_token),
    )
    assert res.status_code == 200
    assert res.json()["error"] == "not_enrolled"
