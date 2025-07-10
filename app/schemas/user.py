from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class Role(str, Enum):
    CARERECEIVER = "CARERECEIVER"
    CAREGIVER = "CAREGIVER"


class User(BaseModel):
    id: str  # Provided by frontend, must be valid UUID
    email: Optional[EmailStr] = None
    role: Role


class UserDB(User):
    hashed_password: Optional[str] = None


class UserTextSize(str, Enum):
    STANDARD = "STANDARD"
    LARGE = "LARGE"


class UserDisplayMode(str, Enum):
    FULL = "FULL"
    SIMPLE = "SIMPLE"


class UserLink(BaseModel):
    email: EmailStr
    name: str


class UserSettingsResponse(BaseModel):
    name: str
    textSize: UserTextSize
    displayMode: UserDisplayMode
    reminder: dict | None
    linked: List[UserLink]


class UserSettingsUpdateRequest(BaseModel):
    name: Optional[str] = None
    textSize: Optional[UserTextSize] = None
    displayMode: Optional[UserDisplayMode] = None
    reminder: Optional[dict] = None


class UserMeResponse(BaseModel):
    email: Optional[EmailStr] = None
    role: Role
    settings: UserSettingsResponse
