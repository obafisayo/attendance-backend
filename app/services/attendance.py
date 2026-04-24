import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.attendance import Attendance
from app.models.session import Session, SessionToken
from app.models.user import User
from app.core.security import verify_ble_signature
from app.schemas.attendance import MarkAttendanceRequest, MarkAttendanceResponse, ProfessorAttendanceRecord

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

    # TODO: Step 2 — fetch session by body.s, return "session_ended" if not active
    # TODO: Step 3 — fetch SessionToken where token_id == body.t and session matches
    #               return "invalid_token" if not found or expired
    # TODO: Step 4 — verify_ble_signature(s=body.s, t=body.t, ts=body.ts, sig=body.sig)
    #               return "invalid_signature" if fails
    # TODO: Step 5 — check Attendance for (session_id, student_id) uniqueness
    #               return "already_marked" if exists
    # TODO: Step 6 — insert Attendance row, set token.used = True, commit
    # TODO: return MarkAttendanceResponse(success=True, markedAt=record.marked_at)
    raise NotImplementedError


async def get_student_history(
    db: AsyncSession,
    student_id: str,
    course_id: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list:
    # TODO: query attendance JOIN sessions JOIN courses WHERE student_id = student_id
    # TODO: apply course_id filter if provided
    # TODO: apply from_date / to_date filters on attendance.marked_at
    # TODO: return list of StudentAttendanceRecord
    raise NotImplementedError


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
