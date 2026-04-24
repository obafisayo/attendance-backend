from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id, require_student
from app.database import get_db

router = APIRouter()


@router.post("/face/enroll")
async def enroll_face(
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    image: UploadFile = File(...),
):
    """
    Student submits a clear face photo during onboarding.
    Backend extracts embedding and stores it against their user record.
    """
    # TODO: read image bytes from upload
    # TODO: call face_service.extract_embedding(image_bytes)
    # TODO: store embedding in users.face_embedding (add column to model first)
    # TODO: return { enrolled: true }
    raise NotImplementedError


@router.post("/face/verify")
async def verify_face(
    student_id: str = Depends(require_student),
    db: AsyncSession = Depends(get_db),
    image: UploadFile = File(...),
):
    """
    Internal — called during attendance marking to confirm identity.
    You may not need to expose this as a public route if attendance.py calls it directly.
    """
    # TODO: fetch stored embedding for student_id
    # TODO: extract embedding from uploaded image
    # TODO: compare embeddings — return { match: bool, confidence: float }
    raise NotImplementedError
