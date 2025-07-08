from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AssistantConversationCreate(BaseModel):
    conversation_id: str
    user_id: str
    intent_type: Optional[str] = None
    llm_result: Optional[Dict[str, Any]] = None
    turn_count: int = 1


class AssistantConversationUpdate(BaseModel):
    intent_type: Optional[str] = None
    llm_result: Optional[Dict[str, Any]] = None
    turn_count: Optional[int] = None


class AssistantConversationResponse(BaseModel):
    conversation_id: str
    user_id: str
    intent_type: Optional[str] = None
    llm_result: Optional[Dict[str, Any]] = None
    turn_count: int
    created_at: datetime
    updated_at: datetime
