from httpx import AsyncClient

STUDENT = {
    "email": "student@test.com",
    "password": "password123",
    "role": "student",
    "full_name": "Test Student",
    "matric_no": "MAT001",
}

PROFESSOR = {
    "email": "prof@test.com",
    "password": "password123",
    "role": "professor",
    "full_name": "Test Professor",
}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_get_profile_student(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    token = reg.json()["token"]

    res = await client.get("/users/me", headers=auth_header(token))
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == STUDENT["email"]
    assert data["role"] == "student"
    assert data["matric_no"] == STUDENT["matric_no"]
    assert data["full_name"] == STUDENT["full_name"]


async def test_get_profile_professor(client: AsyncClient):
    reg = await client.post("/auth/register", json=PROFESSOR)
    token = reg.json()["token"]

    res = await client.get("/users/me", headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["role"] == "professor"


async def test_get_profile_unauthenticated(client: AsyncClient):
    res = await client.get("/users/me")
    assert res.status_code == 401


async def test_update_profile_full_name(client: AsyncClient):
    reg = await client.post("/auth/register", json=PROFESSOR)
    token = reg.json()["token"]

    res = await client.put("/users/me", json={"full_name": "Updated Name"}, headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["full_name"] == "Updated Name"


async def test_update_profile_no_change(client: AsyncClient):
    reg = await client.post("/auth/register", json=PROFESSOR)
    token = reg.json()["token"]

    res = await client.put("/users/me", json={}, headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["full_name"] == PROFESSOR["full_name"]
