from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_professor
from app.database import get_db
from app.schemas.session import CreateSessionRequest, SessionOut, SessionTokenOut, SessionTokenRequest
from app.schemas.attendance import SessionAttendanceResponse

router = APIRouter()


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    # TODO: verify the course belongs to this professor — raise 403 if not
    # TODO: check no other active session exists for this course — raise 409 if so
    # TODO: insert Session row with status="active"
    # TODO: return SessionOut
    raise NotImplementedError


@router.post("/{session_id}/token", response_model=SessionTokenOut)
async def register_token(
    session_id: str,
    body: SessionTokenRequest,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    # TODO: verify session exists and belongs to this professor — raise 403/404
    # TODO: verify session status == "active" — raise 400 if ended
    # TODO: verify BLE signature with verify_ble_signature(s=session_id, t=body.t, ts=body.ts, sig=body.sig)
    # TODO: insert SessionToken row with expires_at = now + 25 seconds
    # TODO: return SessionTokenOut
    raise NotImplementedError


@router.post("/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    # TODO: verify session belongs to this professor — raise 403/404
    # TODO: set status="ended", ended_at=now()
    # TODO: return SessionOut
    raise NotImplementedError


@router.get("/{session_id}/attendance", response_model=SessionAttendanceResponse)
async def get_session_attendance(
    session_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    # TODO: verify session belongs to this professor — raise 403/404
    # TODO: join attendance + users to fetch student name, marked_at, token_id
    # TODO: return SessionAttendanceResponse
    raise NotImplementedError
