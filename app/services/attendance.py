import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.attendance import Attendance
from app.models.course import Course, Enrollment
from app.models.session import Session, SessionToken
from app.models.user import User
from app.schemas.attendance import (
    MarkAttendanceRequest,
    MarkAttendanceResponse,
    ProfessorAttendanceRecord,
    StudentAttendanceRecord,
)


async def mark_attendance(
    db: AsyncSession,
    body: MarkAttendanceRequest,
    student_id: str,
) -> MarkAttendanceResponse:
    # Step 1 — look up the token by the 6-char BLE token ID
    token = (await db.execute(
        select(SessionToken).where(
            SessionToken.token_id == body.token,
            SessionToken.expires_at > datetime.now(timezone.utc),
            SessionToken.used == False,  # noqa: E712
        )
    )).scalar_one_or_none()
    if not token:
        return MarkAttendanceResponse(success=False, error="invalid_token")

    # Step 2 — fetch session, check active
    session = await db.get(Session, token.session_id)
    if session is None or session.status != "active":
        return MarkAttendanceResponse(success=False, error="session_ended")

    # Step 3 — check duplicate
    dup = (await db.execute(
        select(Attendance).where(
            Attendance.session_id == session.id,
            Attendance.student_id == uuid.UUID(student_id),
        )
    )).scalar_one_or_none()
    if dup:
        return MarkAttendanceResponse(success=False, error="already_marked")

    # Step 4 — insert attendance, mark token used, auto-enroll if first time
    record = Attendance(session_id=session.id, student_id=uuid.UUID(student_id), token_id=body.token)
    token.used = True
    db.add(record)

    existing_enrollment = (await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == uuid.UUID(student_id),
            Enrollment.course_id == session.course_id,
        )
    )).scalar_one_or_none()
    if not existing_enrollment:
        db.add(Enrollment(student_id=uuid.UUID(student_id), course_id=session.course_id))

    await db.commit()
    await db.refresh(record)
    return MarkAttendanceResponse(success=True, markedAt=record.marked_at)  # type: ignore[arg-type]


async def get_student_history(
    db: AsyncSession,
    student_id: str,
    course_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> tuple[list[StudentAttendanceRecord], int | None]:
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
    records = [
        StudentAttendanceRecord(
            session_id=a.session_id,
            course_code=c.code,
            course_name=c.name,
            marked_at=a.marked_at,
        )
        for a, s, c in rows
    ]

    total_sessions: int | None = None
    if course_id:
        total_sessions = (await db.execute(
            select(func.count()).where(
                Session.course_id == uuid.UUID(course_id),
                Session.status == "ended",
            )
        )).scalar_one() or 0

    return records, total_sessions


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
