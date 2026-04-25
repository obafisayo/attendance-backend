import hashlib
import json
import time
import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.course import Course, Enrollment
from app.models.session import Session


# --- helpers ---

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


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def ble_sig(session_id: str, t: str, ts: int) -> str:
    payload = json.dumps({"s": session_id, "t": t, "ts": ts}, separators=(",", ":"))
    return hashlib.sha256((payload + settings.ENCRYPTION_KEY).encode()).hexdigest()[:10]


async def create_course(db: AsyncSession, professor_id: str, code: str = "CSC401") -> Course:
    course = Course(
        code=code,
        name="Mobile Development",
        professor_id=uuid.UUID(professor_id),
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def enroll_student(db: AsyncSession, student_id: str, course_id: uuid.UUID):
    enrollment = Enrollment(student_id=uuid.UUID(student_id), course_id=course_id)
    db.add(enrollment)
    await db.commit()


async def setup_attendance(client: AsyncClient, db: AsyncSession) -> tuple[str, str, str]:
    """Creates professor, course, session, token, student, and marks attendance.
    Returns: (prof_token, student_token, course_id)"""
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

    student_token, student_id = await register_and_login(client, STUDENT)
    await enroll_student(db, student_id, course.id)

    ts2 = int(time.time() * 1000)
    await client.post(
        "/attendance",
        json={"s": session_id, "t": t, "ts": ts2, "sig": ble_sig(session_id, t, ts2)},
        headers=auth_header(student_token),
    )

    return prof_token, student_token, str(course.id)


# --- tests ---


async def test_list_courses_as_professor(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    await create_course(db, prof_id)

    res = await client.get("/courses", headers=auth_header(token))
    assert res.status_code == 200
    data = res.json()
    assert len(data["courses"]) == 1
    assert data["courses"][0]["code"] == "CSC401"


async def test_list_courses_professor_student_count(client: AsyncClient, db: AsyncSession):
    token, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    _, student_id = await register_and_login(client, STUDENT)
    await enroll_student(db, student_id, course.id)

    res = await client.get("/courses", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["courses"][0]["studentCount"] == 1


async def test_list_courses_as_student(client: AsyncClient, db: AsyncSession):
    _, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    student_token, student_id = await register_and_login(client, STUDENT)
    await enroll_student(db, student_id, course.id)

    res = await client.get("/courses", headers=auth_header(student_token))
    assert res.status_code == 200
    data = res.json()
    assert len(data["courses"]) == 1
    assert data["courses"][0]["code"] == "CSC401"


async def test_list_courses_student_sees_only_enrolled(client: AsyncClient, db: AsyncSession):
    _, prof_id = await register_and_login(client, PROFESSOR)
    await create_course(db, prof_id, code="CSC401")
    course2 = await create_course(db, prof_id, code="CSC402")

    student_token, student_id = await register_and_login(client, STUDENT)
    await enroll_student(db, student_id, course2.id)

    res = await client.get("/courses", headers=auth_header(student_token))
    assert res.status_code == 200
    courses = res.json()["courses"]
    assert len(courses) == 1
    assert courses[0]["code"] == "CSC402"


async def test_export_csv(client: AsyncClient, db: AsyncSession):
    prof_token, _, course_id = await setup_attendance(client, db)

    res = await client.get(
        f"/courses/{course_id}/attendance/export?format=csv",
        headers=auth_header(prof_token),
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'filename="attendance_' in res.headers["content-disposition"]

    lines = res.text.strip().splitlines()
    assert lines[0] == "Student Name,Matric No,Session Date,Marked At"
    assert len(lines) == 2  # header + 1 record
    assert "Test Student" in lines[1]
    assert "MAT001" in lines[1]


async def test_export_xlsx(client: AsyncClient, db: AsyncSession):
    prof_token, _, course_id = await setup_attendance(client, db)

    res = await client.get(
        f"/courses/{course_id}/attendance/export?format=xlsx",
        headers=auth_header(prof_token),
    )
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["content-type"]
    assert ".xlsx" in res.headers["content-disposition"]


async def test_export_wrong_owner(client: AsyncClient, db: AsyncSession):
    _, prof_id = await register_and_login(client, PROFESSOR)
    course = await create_course(db, prof_id)

    token2, _ = await register_and_login(client, PROFESSOR_2)
    res = await client.get(
        f"/courses/{course.id}/attendance/export?format=csv",
        headers=auth_header(token2),
    )
    assert res.status_code == 403


async def test_export_course_not_found(client: AsyncClient, db: AsyncSession):
    token, _ = await register_and_login(client, PROFESSOR)
    res = await client.get(
        f"/courses/{uuid.uuid4()}/attendance/export?format=csv",
        headers=auth_header(token),
    )
    assert res.status_code == 404
