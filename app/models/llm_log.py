from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LLMLogCreate(BaseModel):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    input_text: str
    output_text: Optional[str] = None


class LLMLogResponse(BaseModel):
    id: int
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    created_at: datetime
    input_text: str
    output_text: Optional[str] = None
