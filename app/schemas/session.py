from pydantic import BaseModel
from typing import Literal
import uuid
from datetime import datetime


class CreateSessionRequest(BaseModel):
    courseId: uuid.UUID


class SessionTokenRequest(BaseModel):
    t: str  # 6-char token ID broadcast over BLE


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
