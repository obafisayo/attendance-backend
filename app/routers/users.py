import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id
from app.database import get_db
from app.models.user import User
from app.schemas.user import ProfileResponse, UpdateProfileRequest

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    await db.commit()
    await db.refresh(user)
    return user
