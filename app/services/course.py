import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from app.models.course import Course, Enrollment
from app.models.session import Session
from app.models.attendance import Attendance
from app.models.user import User
from app.schemas.course import CourseOut


async def get_courses_for_professor(db: AsyncSession, professor_id: str) -> list[CourseOut]:
    rows = (await db.execute(
        select(Course, func.count(Enrollment.student_id).label("cnt"))
        .outerjoin(Enrollment, Enrollment.course_id == Course.id)
        .where(Course.professor_id == uuid.UUID(professor_id))
        .group_by(Course.id)
    )).all()
    return [CourseOut(id=c.id, code=c.code, name=c.name, studentCount=cnt) for c, cnt in rows]


async def get_courses_for_student(db: AsyncSession, student_id: str) -> list[CourseOut]:
    EnrollmentMe = aliased(Enrollment)
    EnrollmentAll = aliased(Enrollment)

    rows = (await db.execute(
        select(Course, func.count(EnrollmentAll.student_id).label("cnt"))
        .join(EnrollmentMe, (EnrollmentMe.course_id == Course.id) & (EnrollmentMe.student_id == uuid.UUID(student_id)))
        .outerjoin(EnrollmentAll, EnrollmentAll.course_id == Course.id)
        .group_by(Course.id)
    )).all()
    return [CourseOut(id=c.id, code=c.code, name=c.name, studentCount=cnt) for c, cnt in rows]


async def export_course_attendance(
    db: AsyncSession,
    course_id: str,
    from_date: str | None,
    to_date: str | None,
) -> list[dict]:
    q = (
        select(User.full_name, User.matric_no, Session.started_at, Attendance.marked_at)
        .join(Attendance, Attendance.student_id == User.id)
        .join(Session, Session.id == Attendance.session_id)
        .where(Session.course_id == uuid.UUID(course_id))
    )
    if from_date:
        q = q.where(Session.started_at >= from_date)
    if to_date:
        q = q.where(Session.started_at <= to_date)

    rows = (await db.execute(q)).all()
    return [
        {
            "student_name": full_name,
            "matric_no": matric_no,
            "session_date": started_at,
            "marked_at": marked_at,
        }
        for full_name, matric_no, started_at, marked_at in rows
    ]
