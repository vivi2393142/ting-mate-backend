from typing import Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str  # Provided by frontend, must be valid UUID
    email: Optional[EmailStr] = None


class UserDB(User):
    hashed_password: Optional[str] = None
