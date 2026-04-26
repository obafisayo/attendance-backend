from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.dependencies import require_student
from app.database import get_db
from app.schemas.attendance import MarkAttendanceRequest, MarkAttendanceResponse, StudentHistoryResponse
from app.services import attendance as attendance_service

router = APIRouter()


@router.post("", response_model=MarkAttendanceResponse)
async def mark_attendance(
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
):
    records, total_sessions = await attendance_service.get_student_history(
        db, student_id, course_id, from_date, to_date
    )
    return StudentHistoryResponse(records=records, total_sessions=total_sessions)
