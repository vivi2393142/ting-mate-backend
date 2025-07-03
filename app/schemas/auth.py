from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import User


# TODO: Update examples to match the real data
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., example="test@example.com")
    password: str = Field(..., example="Test123!")
    anonymous_id: Optional[str] = None


class RegisterResponse(BaseModel):
    message: str
    user: User


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="user")


class LoginResponse(BaseModel):
    access_token: str


class TokenPayload(BaseModel):
    sub: str  # user email
