from pydantic import BaseModel
import uuid


class CourseOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    studentCount: int = 0

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    courses: list[CourseOut]
