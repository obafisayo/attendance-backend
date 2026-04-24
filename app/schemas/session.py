from pydantic import BaseModel
from typing import Literal
import uuid
from datetime import datetime


class CreateSessionRequest(BaseModel):
    courseId: uuid.UUID


class SessionTokenRequest(BaseModel):
    # exact BLE payload fields the professor app broadcasts
    t: str   # token ID (random string, changes every 20s)
    ts: int  # timestamp in milliseconds
    sig: str # truncated SHA256 signature (first 10 chars)


class SessionOut(BaseModel):
    id: uuid.UUID
    courseId: uuid.UUID
    status: Literal["active", "ended"]
    startedAt: datetime
    endedAt: datetime | None

    model_config = {"from_attributes": True}


class SessionTokenOut(BaseModel):
    tokenId: str
    expiresAt: datetime
