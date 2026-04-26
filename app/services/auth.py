from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, LoginRequest

_MAX_ATTEMPTS = 5
_LOCKOUT_MINUTES = 15


async def create_user(db: AsyncSession, body: RegisterRequest) -> User:
    if body.role == "student" and not body.matric_no:
        raise HTTPException(status_code=422, detail="matric_no is required for students")

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

    # Same generic error regardless of whether user exists (prevents enumeration)
    _invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user:
        raise _invalid

    # Check lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked. Try again after {user.locked_until.strftime('%H:%M UTC')}",
        )

    if not verify_password(body.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= _MAX_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MINUTES)
        await db.commit()
        raise _invalid

    # Successful login — reset counters
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(db: AsyncSession, user_id: str, old_password: str, new_password: str) -> None:
    import uuid
    user = await db.get(User, uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    user.password_hash = hash_password(new_password)
    await db.commit()


def build_token_pair(user: User) -> tuple[str, str]:
    payload = {"sub": str(user.id), "role": user.role}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    return access, refresh
