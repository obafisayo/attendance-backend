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


async def test_register_student(client: AsyncClient):
    res = await client.post("/auth/register", json=STUDENT)
    assert res.status_code == 201
    data = res.json()
    assert data["token"]
    assert data["refreshToken"]
    assert data["user"]["role"] == "student"
    assert data["user"]["email"] == STUDENT["email"]


async def test_register_professor(client: AsyncClient):
    res = await client.post("/auth/register", json=PROFESSOR)
    assert res.status_code == 201
    data = res.json()
    assert data["token"]
    assert data["user"]["role"] == "professor"


async def test_duplicate_email_returns_409(client: AsyncClient):
    await client.post("/auth/register", json=STUDENT)
    res = await client.post("/auth/register", json={**STUDENT, "matric_no": "MAT002"})
    assert res.status_code == 409


async def test_student_missing_matric_no_returns_422(client: AsyncClient):
    res = await client.post("/auth/register", json={**STUDENT, "matric_no": None})
    assert res.status_code == 422


async def test_password_too_short_returns_422(client: AsyncClient):
    res = await client.post("/auth/register", json={**PROFESSOR, "password": "short1"})
    assert res.status_code == 422


async def test_password_no_digit_returns_422(client: AsyncClient):
    res = await client.post("/auth/register", json={**PROFESSOR, "password": "passwordonly"})
    assert res.status_code == 422


async def test_login_success(client: AsyncClient):
    await client.post("/auth/register", json=STUDENT)
    res = await client.post("/auth/login", json={
        "email": STUDENT["email"],
        "password": STUDENT["password"],
        "role": "student",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["token"]
    assert data["user"]["email"] == STUDENT["email"]


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json=STUDENT)
    res = await client.post("/auth/login", json={
        "email": STUDENT["email"],
        "password": "wrongpassword1",
        "role": "student",
    })
    assert res.status_code == 401


async def test_login_wrong_role(client: AsyncClient):
    await client.post("/auth/register", json=STUDENT)
    res = await client.post("/auth/login", json={
        "email": STUDENT["email"],
        "password": STUDENT["password"],
        "role": "professor",
    })
    assert res.status_code == 401


async def test_account_lockout(client: AsyncClient):
    await client.post("/auth/register", json=STUDENT)
    for _ in range(5):
        await client.post("/auth/login", json={
            "email": STUDENT["email"], "password": "wrongpass1", "role": "student"
        })
    res = await client.post("/auth/login", json={
        "email": STUDENT["email"], "password": "wrongpass1", "role": "student"
    })
    assert res.status_code == 429


async def test_refresh_valid_token(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    refresh_token = reg.json()["refreshToken"]
    res = await client.post("/auth/refresh", json={"refreshToken": refresh_token})
    assert res.status_code == 200
    data = res.json()
    assert data["token"]
    assert data["refreshToken"]


async def test_refresh_rotates_old_token(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    old_refresh = reg.json()["refreshToken"]
    await client.post("/auth/refresh", json={"refreshToken": old_refresh})
    # old refresh token should now be blocked
    res = await client.post("/auth/refresh", json={"refreshToken": old_refresh})
    assert res.status_code == 401


async def test_refresh_invalid_token(client: AsyncClient):
    res = await client.post("/auth/refresh", json={"refreshToken": "not.a.valid.token"})
    assert res.status_code == 401


async def test_logout_blocks_token(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/auth/logout", headers=headers)

    res = await client.get("/users/me", headers=headers)
    assert res.status_code == 401


async def test_change_password(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    token = reg.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/auth/change-password", json={
        "old_password": STUDENT["password"],
        "new_password": "newpassword99",
    }, headers=headers)
    assert res.status_code == 204

    login_res = await client.post("/auth/login", json={
        "email": STUDENT["email"], "password": "newpassword99", "role": "student"
    })
    assert login_res.status_code == 200


async def test_change_password_wrong_old(client: AsyncClient):
    reg = await client.post("/auth/register", json=STUDENT)
    token = reg.json()["token"]
    res = await client.post("/auth/change-password", json={
        "old_password": "wrongpass1",
        "new_password": "newpassword99",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
