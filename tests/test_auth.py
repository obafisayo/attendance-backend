import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_register_student():
    # TODO: POST /auth/register with student payload
    # TODO: assert 201, token present, role == "student"
    pass


@pytest.mark.asyncio
async def test_register_professor():
    # TODO: POST /auth/register with professor payload
    # TODO: assert 201, token present, role == "professor"
    pass


@pytest.mark.asyncio
async def test_login_success():
    # TODO: register user then POST /auth/login
    # TODO: assert 200, token returned
    pass


@pytest.mark.asyncio
async def test_login_wrong_password():
    # TODO: POST /auth/login with bad password
    # TODO: assert 401
    pass


@pytest.mark.asyncio
async def test_login_wrong_role():
    # TODO: register as student, login with role="professor"
    # TODO: assert 401
    pass
