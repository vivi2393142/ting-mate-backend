from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class UserInfo(BaseModel):
    """User information for activity logs"""

    id: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None


class Action(str, Enum):
    """Activity log action types"""

    # User Settings
    UPDATE_USER_SETTINGS = "UPDATE_USER_SETTINGS"

    # Task Management
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    UPDATE_TASK_STATUS = "UPDATE_TASK_STATUS"
    DELETE_TASK = "DELETE_TASK"

    # Shared Notes
    CREATE_SHARED_NOTE = "CREATE_SHARED_NOTE"
    UPDATE_SHARED_NOTE = "UPDATE_SHARED_NOTE"
    DELETE_SHARED_NOTE = "DELETE_SHARED_NOTE"

    # Safe Zones
    UPSERT_SAFE_ZONE = "UPSERT_SAFE_ZONE"
    DELETE_SAFE_ZONE = "DELETE_SAFE_ZONE"

    # User Links
    ADD_USER_LINK = "ADD_USER_LINK"
    REMOVE_USER_LINK = "REMOVE_USER_LINK"

    # Role Transition
    TRANSITION_USER_ROLE = "TRANSITION_USER_ROLE"


def is_personal_action(action: Action) -> bool:
    """Check if an action is personal (doesn't require target_user_id)"""
    personal_actions = {
        Action.UPDATE_USER_SETTINGS,
        Action.ADD_USER_LINK,
        Action.REMOVE_USER_LINK,
        Action.TRANSITION_USER_ROLE,
    }
    return action in personal_actions


def is_shared_action(action: Action) -> bool:
    """Check if an action is shared (requires target_user_id)"""
    shared_actions = {
        Action.CREATE_TASK,
        Action.UPDATE_TASK,
        Action.UPDATE_TASK_STATUS,
        Action.DELETE_TASK,
        Action.CREATE_SHARED_NOTE,
        Action.UPDATE_SHARED_NOTE,
        Action.DELETE_SHARED_NOTE,
        Action.UPSERT_SAFE_ZONE,
        Action.DELETE_SAFE_ZONE,
    }
    return action in shared_actions


class ActivityLog(BaseModel):
    """Activity log entry"""

    id: str
    user_id: str
    target_user_id: Optional[str] = None
    action: Action
    detail: Optional[Dict[str, Any]] = None
    timestamp: datetime


class ActivityLogCreate(BaseModel):
    """Create activity log entry"""

    user_id: str
    target_user_id: Optional[str] = None
    action: Action
    detail: Optional[Dict[str, Any]] = None


class ActivityLogResponse(BaseModel):
    """Activity log response with complete user information"""

    id: str
    user: UserInfo
    target_user: Optional[UserInfo] = None
    action: Action
    detail: Optional[Dict[str, Any]] = None
    timestamp: datetime


class ActivityLogListResponse(BaseModel):
    """List of activity logs with pagination"""

    logs: List[ActivityLogResponse]
    total: int
    limit: int
    offset: int


class ActivityLogFilter(BaseModel):
    """Filter for activity logs"""

    actions: Optional[list[Action]] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0


class AvailableActionsResponse(BaseModel):
    """Response model for available actions"""

    actions: List[str]
