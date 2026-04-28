from pydantic import BaseModel, field_validator, model_validator
import uuid

from app.schemas.auth import _validate_password


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    password: str | None = None
    old_password: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str | None) -> str | None:
        if v is not None:
            _validate_password(v)
        return v

    @model_validator(mode="after")
    def password_requires_old(self) -> "UpdateProfileRequest":
        if self.password is not None and not self.old_password:
            raise ValueError("old_password is required when changing password")
        return self


class ProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    matric_no: str | None

    model_config = {"from_attributes": True}
