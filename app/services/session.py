from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session, SessionToken
from app.core.security import verify_ble_signature


async def create_session(db: AsyncSession, course_id: str, professor_id: str) -> Session:
    # TODO: check for existing active session on this course — raise if found
    # TODO: insert Session row
    # TODO: commit + refresh, return session
    raise NotImplementedError


async def register_token(
    db: AsyncSession,
    session: Session,
    t: str,
    ts: int,
    sig: str,
) -> SessionToken:
    # TODO: verify signature with verify_ble_signature(s=str(session.id), t=t, ts=ts, sig=sig)
    # TODO: insert SessionToken with expires_at = now + 25s
    # TODO: commit + refresh, return token
    raise NotImplementedError


async def end_session(db: AsyncSession, session: Session) -> Session:
    # TODO: set session.status = "ended", session.ended_at = now()
    # TODO: commit + refresh, return session
    raise NotImplementedError


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    # TODO: return session by id or None
    raise NotImplementedError
