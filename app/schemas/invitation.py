from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.schemas.user import Role


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"


class Invitation(BaseModel):
    id: str
    inviter_id: str
    invitation_code: str
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime


class InvitationCreate(BaseModel):
    inviter_id: str


class InvitationResponse(BaseModel):
    invitation_code: str
    qr_code_url: Optional[str] = None
    expires_at: datetime


class InvitationInfo(BaseModel):
    inviter_name: str
    inviter_role: Role
    expires_at: datetime


class AcceptInvitationResponse(BaseModel):
    message: str
    linked_user: dict
