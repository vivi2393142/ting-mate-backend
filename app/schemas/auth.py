from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import User


# TODO: Update examples to match the real data
class RegisterRequest(BaseModel):
    id: str = Field(..., description="User id provided by frontend, must be valid UUID")
    email: EmailStr = Field(..., json_schema_extra={"example": "test@example.com"})
    role: str = Field(
        ..., description="User role, must be 'CARERECEIVER' or 'CAREGIVER'"
    )
    password: str = Field(..., min_length=6, json_schema_extra={"example": "Test123!"})


class RegisterResponse(BaseModel):
    message: str
    user: User
    access_token: str
    anonymous_id: str


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "user@example.com"})
    password: str = Field(..., json_schema_extra={"example": "user"})


class LoginResponse(BaseModel):
    anonymous_id: str
    access_token: str


class TokenPayload(BaseModel):
    sub: str  # user email
