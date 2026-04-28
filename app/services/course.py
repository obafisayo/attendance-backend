import uuid
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.orm import aliased

from app.models.course import Course, Enrollment
from app.models.session import Session
from app.models.attendance import Attendance
from app.models.user import User
from app.schemas.course import CourseOut, CreateCourseRequest, UpdateCourseRequest, StudentStatsRecord


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


async def create_course(db: AsyncSession, professor_id: str, body: CreateCourseRequest) -> Course:
    course = Course(
        code=body.code.strip().upper(),
        name=body.name.strip(),
        professor_id=uuid.UUID(professor_id),
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def get_course_by_id(db: AsyncSession, course_id: str) -> Course | None:
    return await db.get(Course, uuid.UUID(course_id))


async def update_course(db: AsyncSession, course: Course, body: UpdateCourseRequest) -> Course:
    if body.code is not None:
        course.code = body.code.strip().upper()
    if body.name is not None:
        course.name = body.name.strip()
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course: Course) -> None:
    session_count = (await db.execute(
        select(func.count()).where(Session.course_id == course.id)
    )).scalar_one()
    if session_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a course that has existing sessions. End all sessions first.",
        )
    enrollments = (await db.execute(
        select(Enrollment).where(Enrollment.course_id == course.id)
    )).scalars().all()
    for e in enrollments:
        await db.delete(e)
    await db.delete(course)
    await db.commit()


async def get_course_stats(
    db: AsyncSession, course_id: str
) -> tuple[int, list[StudentStatsRecord]]:
    course_uuid = uuid.UUID(course_id)

    total_sessions: int = (await db.execute(
        select(func.count()).where(
            Session.course_id == course_uuid,
            Session.status == "ended",
        )
    )).scalar_one() or 0

    # Single query: all enrolled students + their attended count via LEFT JOIN
    ended_session_ids = select(Session.id).where(
        Session.course_id == course_uuid,
        Session.status == "ended",
    ).scalar_subquery()

    AttendanceAlias = aliased(Attendance)

    rows = (await db.execute(
        select(
            User,
            func.count(AttendanceAlias.id).label("attended"),
        )
        .join(Enrollment, Enrollment.student_id == User.id)
        .outerjoin(
            AttendanceAlias,
            (AttendanceAlias.student_id == User.id) &
            (AttendanceAlias.session_id.in_(ended_session_ids)),
        )
        .where(Enrollment.course_id == course_uuid)
        .group_by(User.id)
        .order_by(User.full_name)
    )).all()

    records: list[StudentStatsRecord] = []
    for user, attended in rows:
        records.append(StudentStatsRecord(
            student_id=user.id,
            student_name=user.full_name,
            matric_no=user.matric_no,
            sessions_attended=attended,
            total_sessions=total_sessions,
            percentage=round(attended / total_sessions * 100, 1) if total_sessions > 0 else 0.0,
        ))

    return total_sessions, records


async def enroll_student(db: AsyncSession, course_id: str, identifier: str) -> User:
    """Enroll a student by email or matric number."""
    from sqlalchemy import or_
    user = (await db.execute(
        select(User).where(
            User.role == "student",
            or_(User.email == identifier, User.matric_no == identifier),
        )
    )).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    course_uuid = uuid.UUID(course_id)
    existing = (await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == user.id,
            Enrollment.course_id == course_uuid,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already enrolled")

    db.add(Enrollment(student_id=user.id, course_id=course_uuid))
    await db.commit()
    return user


async def remove_student(db: AsyncSession, course_id: str, student_id: str) -> None:
    enrollment = (await db.execute(
        select(Enrollment).where(
            Enrollment.course_id == uuid.UUID(course_id),
            Enrollment.student_id == uuid.UUID(student_id),
        )
    )).scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    await db.delete(enrollment)
    await db.commit()


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
        q = q.where(Session.started_at >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.where(Session.started_at <= datetime.fromisoformat(to_date))

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
