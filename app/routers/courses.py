import csv
import io
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, require_professor
from app.database import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseListResponse
from app.services import course as course_service

router = APIRouter()


@router.get("", response_model=CourseListResponse)
async def list_courses(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if user.role == "professor":
        courses = await course_service.get_courses_for_professor(db, user_id)
    else:
        courses = await course_service.get_courses_for_student(db, user_id)

    return CourseListResponse(courses=courses)


@router.get("/{course_id}/attendance/export")
async def export_attendance(
    course_id: str,
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
    format: Literal["csv", "xlsx"] = Query("csv"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    course = await db.get(Course, uuid.UUID(course_id))
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if str(course.professor_id) != professor_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your course")

    records = await course_service.export_course_attendance(db, course_id, from_date, to_date)

    filename = f"attendance_{course.code}"

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student Name", "Matric No", "Session Date", "Marked At"])
        for r in records:
            writer.writerow([
                r["student_name"],
                r["matric_no"],
                r["session_date"].isoformat() if r["session_date"] else "",
                r["marked_at"].isoformat() if r["marked_at"] else "",
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["Student Name", "Matric No", "Session Date", "Marked At"])
    for r in records:
        ws.append([
            r["student_name"],
            r["matric_no"],
            r["session_date"].isoformat() if r["session_date"] else "",
            r["marked_at"].isoformat() if r["marked_at"] else "",
        ])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}.xlsx"'},
    )
