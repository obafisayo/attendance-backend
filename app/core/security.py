import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _make_token(data: dict, token_type: str, expire: datetime) -> str:
    payload = data.copy()
    payload["exp"] = expire
    payload["type"] = token_type
    payload["jti"] = str(uuid.uuid4())
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _make_token(data, "access", expire)


def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _make_token(data, "refresh", expire)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def is_token_blocked(db: AsyncSession, jti: str) -> bool:
    from app.models.blocklist import TokenBlocklist
    row = await db.get(TokenBlocklist, jti)
    return row is not None


async def block_token(db: AsyncSession, token: str) -> None:
    from app.models.blocklist import TokenBlocklist
    try:
        payload = decode_token(token)
    except JWTError:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    existing = await db.get(TokenBlocklist, jti)
    if not existing:
        db.add(TokenBlocklist(jti=jti, expires_at=expires_at))
        await db.commit()


def verify_ble_signature(s: str, t: str, ts: int, sig: str) -> bool:
    """
    Recomputes the SHA256 signature the mobile app generates and compares.

    Mobile app (services/crypto.ts) does:
        SHA256(JSON.stringify({s, t, ts}) + ENCRYPTION_KEY).slice(0, 10)

    JSON.stringify produces keys in insertion order: {s, t, ts}
    """
    payload_str = json.dumps({"s": s, "t": t, "ts": ts}, separators=(",", ":"))
    raw = payload_str + settings.ENCRYPTION_KEY
    computed = hashlib.sha256(raw.encode()).hexdigest()[:10]
    return computed == sig
