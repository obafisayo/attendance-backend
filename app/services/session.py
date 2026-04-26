import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session, SessionToken


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    return await db.get(Session, uuid.UUID(session_id))


async def create_session(db: AsyncSession, course_id: str, professor_id: str) -> Session:
    existing = (
        await db.execute(
            select(Session).where(
                Session.course_id == uuid.UUID(course_id),
                Session.status == "active",
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active session already exists for this course",
        )

    session = Session(
        course_id=uuid.UUID(course_id),
        professor_id=uuid.UUID(professor_id),
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def register_token(
    db: AsyncSession,
    session: Session,
    t: str,
) -> SessionToken:
    token = SessionToken(
        session_id=session.id,
        token_id=t,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=25),
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def end_session(db: AsyncSession, session: Session) -> Session:
    session.status = "ended"
    session.ended_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(session)
    return session
