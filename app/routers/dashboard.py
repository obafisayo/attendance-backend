import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_professor
from app.database import get_db
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
