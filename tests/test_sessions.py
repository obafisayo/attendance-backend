import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_session():
    # TODO: login as professor, POST /sessions with valid courseId
    # TODO: assert 201, session id returned, status == "active"
    pass


@pytest.mark.asyncio
async def test_create_session_as_student_fails():
    # TODO: login as student, POST /sessions
    # TODO: assert 403
    pass


@pytest.mark.asyncio
async def test_register_token():
    # TODO: create session, POST /sessions/{id}/token with valid BLE payload
    # TODO: assert 200, tokenId and expiresAt returned
    pass


@pytest.mark.asyncio
async def test_register_invalid_signature():
    # TODO: POST /sessions/{id}/token with tampered sig
    # TODO: assert 400 or appropriate error
    pass


@pytest.mark.asyncio
async def test_end_session():
    # TODO: create session, POST /sessions/{id}/end
    # TODO: assert status == "ended", endedAt is set
    pass
