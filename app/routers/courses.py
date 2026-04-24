from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal, Optional

from app.core.dependencies import get_current_user_id, require_professor
from app.database import get_db
from app.schemas.course import CourseListResponse

router = APIRouter()


@router.get("", response_model=CourseListResponse)
async def list_courses(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # TODO: fetch user role from DB
    # TODO: if professor → return courses where professor_id = user_id
    # TODO: if student → return courses via enrollments table
    # TODO: include studentCount (count of enrollments per course)
    # TODO: return CourseListResponse
    raise NotImplementedError


@router.get("/{course_id}/attendance/export")
async def export_attendance(
    course_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
    format: Literal["csv", "xlsx"] = Query("csv"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    # TODO: verify course belongs to this professor — raise 403/404
    # TODO: query all sessions for course in date range
    # TODO: join attendance + users to build a flat records list
    # TODO: if format == "csv": use csv module to write to BytesIO, return StreamingResponse
    # TODO: if format == "xlsx": use openpyxl to write to BytesIO, return StreamingResponse
    #       columns: Student Name, Matric No, Session Date, Marked At
    # TODO: set Content-Disposition: attachment; filename="attendance_{course_code}.{format}"
    raise NotImplementedError
