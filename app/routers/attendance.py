from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.dependencies import require_student
from app.database import get_db
from app.schemas.attendance import MarkAttendanceRequest, MarkAttendanceResponse, StudentHistoryResponse

router = APIRouter()


@router.post("", response_model=MarkAttendanceResponse)
async def mark_attendance(
    body: MarkAttendanceRequest,
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Core attendance endpoint. Validates BLE token and records attendance.

    Validation order:
      1. Check timestamp freshness (reject if older than 30s)
      2. Fetch session by body.s — return session_ended if not active
      3. Look up body.t in session_tokens — return invalid_token if not found/expired
      4. Verify signature with verify_ble_signature()  — return invalid_signature if wrong
      5. Check for duplicate (session_id, student_id) — return already_marked if exists
      6. Insert Attendance row, mark token used=True
    """
    # TODO: implement steps 1–6 above
    # TODO: (future) trigger face verification here before inserting attendance
    #       call ml_service.verify_face(student_id, face_frames) — only mark if verified
    raise NotImplementedError


@router.get("/me", response_model=StudentHistoryResponse)
async def get_my_attendance(
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    course_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    # TODO: query attendance joined with sessions + courses for this student
    # TODO: apply optional filters: course_id, from_date, to_date
    # TODO: return StudentHistoryResponse
    raise NotImplementedError
