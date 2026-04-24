import hashlib
import json
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    payload["type"] = "access"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload["exp"] = expire
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    # TODO: handle token revocation (blocklist in Redis or DB) when logout is implemented
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


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
