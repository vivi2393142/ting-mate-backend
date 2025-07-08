from datetime import datetime
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel


class IntentType(str, Enum):
    CREATE_TASK = "CREATE_TASK"
    UPDATE_TASK = "UPDATE_TASK"
    DELETE_TASK = "DELETE_TASK"


class AssistantPendingTaskCreate(BaseModel):
    conversation_id: str
    user_id: str
    intent_type: IntentType
    task_data: Dict[str, Any]


class AssistantPendingTaskResponse(BaseModel):
    id: int
    conversation_id: str
    user_id: str
    intent_type: IntentType
    task_data: Dict[str, Any]
    created_at: datetime
