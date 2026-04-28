from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from app.core.dependencies import require_student
from app.database import get_db
from app.schemas.attendance import MarkAttendanceRequest, MarkAttendanceResponse, StudentHistoryResponse
from app.services import attendance as attendance_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("", response_model=MarkAttendanceResponse)
@limiter.limit("60/minute")
async def mark_attendance(
    request: Request,
    body: MarkAttendanceRequest,
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    # TODO: (future) trigger face verification before inserting attendance
    #       call ml_service.verify_face(student_id, face_frames) — only mark if verified
    return await attendance_service.mark_attendance(db, body, student_id)


@router.get("/me", response_model=StudentHistoryResponse)
async def get_my_attendance(
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    course_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    records, total_sessions = await attendance_service.get_student_history(
        db, student_id, course_id, from_date, to_date, limit, offset
    )
    return StudentHistoryResponse(records=records, total_sessions=total_sessions)
