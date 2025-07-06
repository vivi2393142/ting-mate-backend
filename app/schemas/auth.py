from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import User


# TODO: Update examples to match the real data
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "test@example.com"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "Test123!"})
    anonymous_id: Optional[str] = None


class RegisterResponse(BaseModel):
    message: str
    user: User


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "user@example.com"})
    password: str = Field(..., json_schema_extra={"example": "user"})


class LoginResponse(BaseModel):
    access_token: str


class TokenPayload(BaseModel):
    sub: str  # user email
