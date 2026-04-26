import uuid
from pydantic import BaseModel


class CreateCourseRequest(BaseModel):
    code: str
    name: str


class UpdateCourseRequest(BaseModel):
    code: str | None = None
    name: str | None = None


class CourseOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    studentCount: int = 0

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    courses: list[CourseOut]


class StudentStatsRecord(BaseModel):
    student_id: uuid.UUID
    student_name: str | None
    matric_no: str | None
    sessions_attended: int
    total_sessions: int
    percentage: float


class CourseStatsResponse(BaseModel):
    course_id: uuid.UUID
    total_sessions: int
    students: list[StudentStatsRecord]


class BulkEnrollResponse(BaseModel):
    enrolled: int
    already_enrolled: int
    not_found: list[str]
