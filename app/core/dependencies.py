from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, is_token_blocked
from app.database import get_db

bearer_scheme = HTTPBearer()


async def _decode_and_check(token: str, db: AsyncSession) -> dict:
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    jti = payload.get("jti")
    if jti and await is_token_blocked(db, jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    return payload


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    payload = await _decode_and_check(credentials.credentials, db)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_id


async def require_professor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    payload = await _decode_and_check(credentials.credentials, db)
    if payload.get("role") != "professor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Professors only")
    return payload["sub"]


async def require_student(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> str:
    payload = await _decode_and_check(credentials.credentials, db)
    if payload.get("role") != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Students only")
    return payload["sub"]
