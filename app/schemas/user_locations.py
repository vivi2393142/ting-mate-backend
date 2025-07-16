from datetime import datetime

from pydantic import BaseModel


class UserLocationCreate(BaseModel):
    latitude: float
    longitude: float


class UserLocationResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    timestamp: datetime


class ShouldGetLocationResponse(BaseModel):
    can_get_location: bool
