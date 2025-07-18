from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class NotificationCategory(str, Enum):
    """Notification category for frontend to determine refresh logic"""

    TASK = "TASK"
    USER_SETTING = "USER_SETTING"
    SAFEZONE = "SAFEZONE"
    SYSTEM = "SYSTEM"


class NotificationLevel(str, Enum):
    GENERAL = "GENERAL"
    WARNING = "WARNING"
    ERROR = "ERROR"


class NotificationData(BaseModel):
    """Notification data structure"""

    id: str
    user_id: str
    category: NotificationCategory
    message: str  # User-facing message
    payload: Optional[Dict[str, Any]] = None  # Extra data for frontend logic
    level: NotificationLevel = NotificationLevel.GENERAL
    is_read: bool = False
    created_at: datetime
