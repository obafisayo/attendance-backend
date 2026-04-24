from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RefreshResponse, RegisterRequest

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # TODO: check if email already exists — raise 409 if so
    # TODO: if role == "student", validate matric_no is present — raise 422 if missing
    # TODO: hash password with hash_password() from core.security
    # TODO: insert new User row
    # TODO: create access + refresh tokens with create_access_token / create_refresh_token
    #       include {"sub": str(user.id), "role": user.role} in token payload
    # TODO: return AuthResponse
    raise NotImplementedError


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    # TODO: fetch user by email — raise 401 if not found
    # TODO: verify role matches — raise 401 if mismatch
    # TODO: verify password with verify_password() from core.security — raise 401 if wrong
    # TODO: create access + refresh tokens
    # TODO: return AuthResponse
    raise NotImplementedError


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    # TODO: optionally blocklist the token (store jti in Redis or a revoked_tokens table)
    # TODO: for now, client just discards the token — this endpoint is a no-op placeholder
    return


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    # TODO: decode body.refreshToken — raise 401 if invalid or expired
    # TODO: verify token type == "refresh"
    # TODO: fetch user from DB to confirm they still exist and role hasn't changed
    # TODO: issue new access + refresh token pair
    # TODO: return RefreshResponse
    raise NotImplementedError
