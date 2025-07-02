from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    anonymous_id: str


class RegisterResponse(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="user")


class LoginResponse(BaseModel):
    access_token: str


class TokenPayload(BaseModel):
    sub: str  # user email
