from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, LoginRequest


async def create_user(db: AsyncSession, body: RegisterRequest) -> User:
    # TODO: check duplicate email with select(User).where(User.email == body.email)
    # TODO: check duplicate matric_no for students
    # TODO: build User model instance, hash password
    # TODO: db.add(user), await db.commit(), await db.refresh(user)
    # TODO: return user
    raise NotImplementedError


async def authenticate_user(db: AsyncSession, body: LoginRequest) -> User:
    # TODO: fetch user by email and role
    # TODO: verify password — return None if wrong (caller raises 401)
    # TODO: return user
    raise NotImplementedError


def build_token_pair(user: User) -> tuple[str, str]:
    payload = {"sub": str(user.id), "role": user.role}
    access = create_access_token(payload)
    refresh = create_refresh_token(payload)
    return access, refresh
