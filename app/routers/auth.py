import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user_id
from app.core.security import block_token, decode_token, is_token_blocked
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    UserOut,
)
from app.services.auth import authenticate_user, build_token_pair, change_password, create_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, body)
    access, refresh = build_token_pair(user)
    return AuthResponse(user=UserOut.model_validate(user), token=access, refreshToken=refresh)


@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body)
    access, refresh = build_token_pair(user)
    return AuthResponse(user=UserOut.model_validate(user), token=access, refreshToken=refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        await block_token(db, auth_header[7:])


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refreshToken)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await is_token_blocked(db, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    await block_token(db, body.refreshToken)
    access, refresh_token = build_token_pair(user)
    return RefreshResponse(token=access, refreshToken=refresh_token)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password_endpoint(
    body: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await change_password(db, user_id, body.old_password, body.new_password)
