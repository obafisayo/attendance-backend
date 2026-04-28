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


async def register_and_login(client: AsyncClient, user_data: dict) -> tuple[str, str]:
    res = await client.post("/auth/register", json=user_data)
    data = res.json()
    return data["token"], data["user"]["id"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_dashboard_summary_empty(client: AsyncClient):
    token, _ = await register_and_login(client, PROFESSOR)
    res = await client.get("/dashboard/summary", headers=auth_header(token))
    assert res.status_code == 200
    data = res.json()
    assert data["total_courses"] == 0
    assert data["sessions_this_month"] == 0
    assert data["total_students"] == 0


async def test_dashboard_summary_with_data(client: AsyncClient, db: AsyncSession):
    prof_token, prof_id = await register_and_login(client, PROFESSOR)

    course = Course(code="CSC401", name="Mobile Dev", professor_id=uuid.UUID(prof_id))
    db.add(course)
    await db.commit()

    _, student_id = await register_and_login(client, STUDENT)
    await client.post(
        f"/courses/{course.id}/enroll",
        json={"identifier": STUDENT["email"]},
        headers=auth_header(prof_token),
    )

    await client.post("/sessions", json={"courseId": str(course.id)}, headers=auth_header(prof_token))

    res = await client.get("/dashboard/summary", headers=auth_header(prof_token))
    assert res.status_code == 200
    data = res.json()
    assert data["total_courses"] == 1
    assert data["sessions_this_month"] == 1
    assert data["total_students"] == 1


async def test_dashboard_student_forbidden(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    token = reg.json()["token"]
    res = await client.get("/dashboard/summary", headers=auth_header(token))
    assert res.status_code == 403
