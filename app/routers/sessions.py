import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_professor
from app.database import get_db
from app.models.course import Course
from app.models.session import Session
from app.schemas.attendance import SessionAttendanceResponse
from app.schemas.session import CreateSessionRequest, SessionOut, SessionTokenOut, SessionTokenRequest
from app.services import attendance as attendance_service
from app.services import session as session_service

router = APIRouter()


def _to_session_out(session: Session) -> SessionOut:
    return SessionOut(
        id=session.id,
        courseId=session.course_id,
        status=session.status,
        startedAt=session.started_at,
        endedAt=session.ended_at,
    )


async def _get_owned_session(
    session_id: str,
    professor_id: str,
    db: AsyncSession,
) -> Session:
    session = await session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if str(session.professor_id) != professor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Session)
        .where(Session.professor_id == uuid.UUID(professor_id))
        .order_by(Session.started_at.desc())
    )).scalars().all()
    return [_to_session_out(s) for s in rows]


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    course = await db.get(Course, body.courseId)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if str(course.professor_id) != professor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your course")

    session = await session_service.create_session(db, str(body.courseId), professor_id)
    return _to_session_out(session)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_owned_session(session_id, professor_id, db)
    return _to_session_out(session)


@router.post("/{session_id}/token", response_model=SessionTokenOut)
async def register_token(
    session_id: str,
    body: SessionTokenRequest,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_owned_session(session_id, professor_id, db)

    if session.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not active")

    token = await session_service.register_token(db, session, body.t)
    return SessionTokenOut(tokenId=token.token_id, expiresAt=token.expires_at)


@router.post("/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_owned_session(session_id, professor_id, db)
    session = await session_service.end_session(db, session)
    return _to_session_out(session)


@router.get("/{session_id}/attendance", response_model=SessionAttendanceResponse)
async def get_session_attendance(
    session_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_owned_session(session_id, professor_id, db)
    records = await attendance_service.get_session_attendance(db, str(session.id))
    return SessionAttendanceResponse(records=records)
