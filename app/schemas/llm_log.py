from typing import Optional

from pydantic import BaseModel


class LLMLogCreate(BaseModel):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    input_text: str
    output_text: Optional[str] = None
