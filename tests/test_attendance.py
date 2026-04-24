import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_mark_attendance_success():
    # TODO: setup — professor creates session + registers token
    # TODO: login as student, POST /attendance with matching BLE payload
    # TODO: assert success=True, markedAt present
    pass


@pytest.mark.asyncio
async def test_mark_attendance_duplicate():
    # TODO: mark attendance once, then attempt again with same student
    # TODO: assert error == "already_marked"
    pass


@pytest.mark.asyncio
async def test_mark_attendance_stale_token():
    # TODO: send BLE payload with ts = now - 60_000 (60s old)
    # TODO: assert error == "stale_token"
    pass


@pytest.mark.asyncio
async def test_mark_attendance_invalid_signature():
    # TODO: send BLE payload with tampered sig
    # TODO: assert error == "invalid_signature"
    pass


@pytest.mark.asyncio
async def test_mark_attendance_ended_session():
    # TODO: end the session first, then attempt to mark attendance
    # TODO: assert error == "session_ended"
    pass


@pytest.mark.asyncio
async def test_student_attendance_history():
    # TODO: mark attendance for student in 2+ sessions
    # TODO: GET /attendance/me
    # TODO: assert both records present
    pass
