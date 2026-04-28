import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_professor
from app.database import get_db
from app.models.attendance import Attendance
from app.models.course import Course, Enrollment
from app.models.session import Session

router = APIRouter()


@router.get("/summary")
async def professor_summary(
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    prof_uuid = uuid.UUID(professor_id)

    total_courses: int = (await db.execute(
        select(func.count(Course.id)).where(Course.professor_id == prof_uuid)
    )).scalar_one() or 0

    now = datetime.now(timezone.utc)
    sessions_this_month: int = (await db.execute(
        select(func.count(Session.id))
        .join(Course, Session.course_id == Course.id)
        .where(
            Course.professor_id == prof_uuid,
            func.year(Session.started_at) == now.year,
            func.month(Session.started_at) == now.month,
        )
    )).scalar_one() or 0

    total_students: int = (await db.execute(
        select(func.count(func.distinct(Enrollment.student_id)))
        .join(Course, Enrollment.course_id == Course.id)
        .where(Course.professor_id == prof_uuid)
    )).scalar_one() or 0

    return {
        "total_courses": total_courses,
        "sessions_this_month": sessions_this_month,
        "total_students": total_students,
    }


@router.get("/analytics")
async def professor_analytics(
    professor_id: str = Depends(require_professor),
    db: AsyncSession = Depends(get_db),
):
    prof_uuid = uuid.UUID(professor_id)

    courses_result = await db.execute(
        select(Course).where(Course.professor_id == prof_uuid)
    )
    courses = courses_result.scalars().all()

    result = []
    for course in courses:
        total_sessions: int = (await db.execute(
            select(func.count(Session.id)).where(
                Session.course_id == course.id,
                Session.status == "ended",
            )
        )).scalar_one() or 0

        total_students: int = (await db.execute(
            select(func.count(Enrollment.student_id)).where(
                Enrollment.course_id == course.id
            )
        )).scalar_one() or 0

        if total_sessions > 0 and total_students > 0:
            total_possible = total_sessions * total_students
            total_attended: int = (await db.execute(
                select(func.count(Attendance.id))
                .join(Session, Attendance.session_id == Session.id)
                .where(Session.course_id == course.id)
            )).scalar_one() or 0
            attendance_rate = round((total_attended / total_possible) * 100, 1)
        else:
            attendance_rate = 0.0

        result.append({
            "course_id": str(course.id),
            "course_code": course.code,
            "course_name": course.name,
            "attendance_rate": attendance_rate,
            "total_sessions": total_sessions,
            "total_students": total_students,
        })

    # Sort by attendance_rate ascending so lowest-performing courses show first
    result.sort(key=lambda c: c["attendance_rate"])

    return {"courses": result}
