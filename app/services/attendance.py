import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.attendance import Attendance
from app.models.course import Course, Enrollment
from app.models.session import Session, SessionToken
from app.models.user import User
from app.core.security import verify_ble_signature
from app.schemas.attendance import (
    MarkAttendanceRequest,
    MarkAttendanceResponse,
    ProfessorAttendanceRecord,
    StudentAttendanceRecord,
)

TOKEN_FRESHNESS_MS = 30_000  # reject BLE tokens older than 30 seconds


async def mark_attendance(
    db: AsyncSession,
    body: MarkAttendanceRequest,
    student_id: str,
) -> MarkAttendanceResponse:
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

    # Step 1 — freshness check
    if now_ms - body.ts > TOKEN_FRESHNESS_MS:
        return MarkAttendanceResponse(success=False, error="stale_token")

    # Step 2 — fetch session, check active
    session = await db.get(Session, uuid.UUID(body.s))
    if session is None or session.status != "active":
        return MarkAttendanceResponse(success=False, error="session_ended")

    # Step 3 — fetch token, check not expired
    token = (await db.execute(
        select(SessionToken).where(
            SessionToken.session_id == session.id,
            SessionToken.token_id == body.t,
            SessionToken.expires_at > datetime.now(timezone.utc),
        )
    )).scalar_one_or_none()
    if not token:
        return MarkAttendanceResponse(success=False, error="invalid_token")

    # Step 4 — verify BLE signature
    if not verify_ble_signature(s=body.s, t=body.t, ts=body.ts, sig=body.sig):
        return MarkAttendanceResponse(success=False, error="invalid_signature")

    # Step 5 — check enrollment
    enrollment = (await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == uuid.UUID(student_id),
            Enrollment.course_id == session.course_id,
        )
    )).scalar_one_or_none()
    if not enrollment:
        return MarkAttendanceResponse(success=False, error="not_enrolled")

    # Step 6 — check duplicate
    dup = (await db.execute(
        select(Attendance).where(
            Attendance.session_id == session.id,
            Attendance.student_id == uuid.UUID(student_id),
        )
    )).scalar_one_or_none()
    if dup:
        return MarkAttendanceResponse(success=False, error="already_marked")

    # Step 7 — insert attendance, mark token used
    record = Attendance(session_id=session.id, student_id=uuid.UUID(student_id), token_id=body.t)
    token.used = True
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return MarkAttendanceResponse(success=True, markedAt=record.marked_at)  # type: ignore[arg-type]


async def get_student_history(
    db: AsyncSession,
    student_id: str,
    course_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[StudentAttendanceRecord]:
    q = (
        select(Attendance, Session, Course)
        .join(Session, Attendance.session_id == Session.id)
        .join(Course, Session.course_id == Course.id)
        .where(Attendance.student_id == uuid.UUID(student_id))
    )
    if course_id:
        q = q.where(Course.id == uuid.UUID(course_id))
    if from_date:
        q = q.where(Attendance.marked_at >= from_date)
    if to_date:
        q = q.where(Attendance.marked_at <= to_date)

    rows = (await db.execute(q)).all()
    return [
        StudentAttendanceRecord(
            session_id=a.session_id,
            course_code=c.code,
            course_name=c.name,
            marked_at=a.marked_at,
        )
        for a, s, c in rows
    ]


async def get_session_attendance(db: AsyncSession, session_id: str) -> list[ProfessorAttendanceRecord]:
    result = await db.execute(
        select(Attendance, User)
        .join(User, User.id == Attendance.student_id)
        .where(Attendance.session_id == uuid.UUID(session_id))
    )
    return [
        ProfessorAttendanceRecord(
            student_id=att.student_id,
            student_name=usr.full_name,
            marked_at=att.marked_at,
            token_id=att.token_id,
        )
        for att, usr in result.all()
    ]
