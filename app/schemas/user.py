from datetime import datetime
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


# Emergency Contact schemas
class ContactMethod(str, Enum):
    PHONE = "PHONE"
    WHATSAPP = "WHATSAPP"


class EmergencyContact(BaseModel):
    id: str
    name: str
    phone: str
    methods: List[ContactMethod]


class EmergencyContactCreate(BaseModel):
    id: str
    name: str
    phone: str
    methods: List[ContactMethod]


class EmergencyContactUpdate(BaseModel):
    id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    methods: Optional[List[ContactMethod]] = None


# Location schemas
class Location(BaseModel):
    latitude: float
    longitude: float


# AddressData schema for SafeZone
class AddressData(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


# Safe Zone schemas
class SafeZone(BaseModel):
    location: AddressData
    radius: int  # in meters


# Shared Note schemas
class SharedNote(BaseModel):
    id: str
    carereceiver_id: str
    title: str
    content: Optional[str] = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class SharedNoteCreate(BaseModel):
    title: str
    content: Optional[str] = None


class SharedNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class UserSettingsResponse(BaseModel):
    name: str
    textSize: UserTextSize
    displayMode: UserDisplayMode
    reminder: dict | None
    linked: List[UserLink]
    emergency_contacts: Optional[List[EmergencyContact]] = None
    safe_zone: Optional[SafeZone] = None
    allow_share_location: bool = False


class UserSettingsUpdateRequest(BaseModel):
    name: Optional[str] = None
    textSize: Optional[UserTextSize] = None
    displayMode: Optional[UserDisplayMode] = None
    reminder: Optional[dict] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    safe_zone: Optional[SafeZone] = None
    allow_share_location: Optional[bool] = None


class UserMeResponse(BaseModel):
    email: Optional[EmailStr] = None
    role: Role
    settings: UserSettingsResponse
