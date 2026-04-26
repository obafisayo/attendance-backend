import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import require_student
from app.database import get_db
from app.models.course import Course, Enrollment

router = APIRouter()


class SelfEnrollRequest(BaseModel):
    course_id: uuid.UUID


@router.post("", status_code=status.HTTP_201_CREATED)
async def self_enroll(
    body: SelfEnrollRequest,
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    course = await db.get(Course, body.course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    existing = (await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == uuid.UUID(student_id),
            Enrollment.course_id == body.course_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already enrolled")

    db.add(Enrollment(student_id=uuid.UUID(student_id), course_id=body.course_id))
    await db.commit()
    return {"course_id": str(body.course_id), "course_code": course.code, "course_name": course.name}


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def self_unenroll(
    course_id: str,
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    enrollment = (await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == uuid.UUID(student_id),
            Enrollment.course_id == uuid.UUID(course_id),
        )
    )).scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    await db.delete(enrollment)
    await db.commit()
