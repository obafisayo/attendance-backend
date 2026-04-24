import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RefreshResponse, RegisterRequest, UserOut
from app.services.auth import authenticate_user, build_token_pair, create_user

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, body)
    access, refresh = build_token_pair(user)
    return AuthResponse(user=UserOut.model_validate(user), token=access, refreshToken=refresh)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body)
    access, refresh = build_token_pair(user)
    return AuthResponse(user=UserOut.model_validate(user), token=access, refreshToken=refresh)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    return


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refreshToken)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user = await db.get(User, uuid.UUID(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access, refresh_token = build_token_pair(user)
    return RefreshResponse(token=access, refreshToken=refresh_token)
