from pydantic import BaseModel, EmailStr
from typing import Literal
import uuid


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "professor"]
    full_name: str
    matric_no: str | None = None  # required for students


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "professor"]


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
