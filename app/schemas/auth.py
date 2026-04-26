import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator


def _require_strong_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    return v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "professor"]
    full_name: str
    matric_no: str | None = None  # required for students

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return _require_strong_password(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "professor"]


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_policy(cls, v: str) -> str:
        return _require_strong_password(v)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    full_name: str | None

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserOut
    token: str
    refreshToken: str


class RefreshRequest(BaseModel):
    refreshToken: str


class RefreshResponse(BaseModel):
    token: str
    refreshToken: str
