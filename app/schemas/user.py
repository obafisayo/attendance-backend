import uuid
from pydantic import BaseModel


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    matric_no: str | None

    model_config = {"from_attributes": True}
