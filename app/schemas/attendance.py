from pydantic import BaseModel
from typing import Literal
import uuid
from datetime import datetime


class MarkAttendanceRequest(BaseModel):
    token: str  # 6-char token received from BLE broadcast


class AttendanceRecord(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    student_id: uuid.UUID
    marked_at: datetime

    model_config = {"from_attributes": True}


class MarkAttendanceResponse(BaseModel):
    success: bool
    markedAt: datetime | None = None
    error: Literal["invalid_token", "already_marked", "session_ended"] | None = None


class StudentAttendanceRecord(BaseModel):
    session_id: uuid.UUID
    course_code: str
    course_name: str
    marked_at: datetime


class StudentHistoryResponse(BaseModel):
    records: list[StudentAttendanceRecord]
    total_sessions: int | None = None  # populated when course_id filter is provided


class ProfessorAttendanceRecord(BaseModel):
    student_id: uuid.UUID
    student_name: str | None
    marked_at: datetime
    token_id: str


class SessionAttendanceResponse(BaseModel):
    records: list[ProfessorAttendanceRecord]
