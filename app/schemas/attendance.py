from pydantic import BaseModel
from typing import Literal
import uuid
from datetime import datetime


class MarkAttendanceRequest(BaseModel):
    # raw BLE payload shape — must match what the mobile app broadcasts
    s: str   # session ID
    t: str   # token ID
    ts: int  # timestamp in milliseconds
    sig: str # truncated SHA256 (first 10 chars)

    # TODO: add face verification fields when ML is integrated
    # face_frames: list[str] | None = None  # base64-encoded frames
    # face_embedding: list[float] | None = None


class AttendanceRecord(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    student_id: uuid.UUID
    marked_at: datetime

    model_config = {"from_attributes": True}


class MarkAttendanceResponse(BaseModel):
    success: bool
    markedAt: datetime | None = None
    error: Literal["invalid_token", "already_marked", "session_ended", "stale_token", "invalid_signature", "not_enrolled"] | None = None


class StudentAttendanceRecord(BaseModel):
    session_id: uuid.UUID
    course_code: str
    course_name: str
    marked_at: datetime


class StudentHistoryResponse(BaseModel):
    records: list[StudentAttendanceRecord]


class ProfessorAttendanceRecord(BaseModel):
    student_id: uuid.UUID
    student_name: str | None
    marked_at: datetime
    token_id: str


class SessionAttendanceResponse(BaseModel):
    records: list[ProfessorAttendanceRecord]
