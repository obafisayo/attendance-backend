from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, LoginRequest


async def create_user(db: AsyncSession, body: RegisterRequest) -> User:
    if body.role == "student" and not body.matric_no:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="matric_no is required for students")

    existing_email = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if body.matric_no:
        existing_matric = (await db.execute(select(User).where(User.matric_no == body.matric_no))).scalar_one_or_none()
        if existing_matric:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Matric number already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
        full_name=body.full_name,
        matric_no=body.matric_no,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, body: LoginRequest) -> User:
    user = (
        await db.execute(select(User).where(User.email == body.email, User.role == body.role))
    ).scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return user


def build_token_pair(user: User) -> tuple[str, str]:
    payload = {"sub": str(user.id), "role": user.role}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    return access, refresh
