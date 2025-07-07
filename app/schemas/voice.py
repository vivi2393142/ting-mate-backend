from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class VoiceProcessRequest(BaseModel):
    """Voice processing request model"""

    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    encoding: Optional[str] = Field("LINEAR16", description="Audio encoding format")


class VoiceProcessResponse(BaseModel):
    """Voice processing response model"""

    conversation_id: str = Field(..., description="Conversation ID")
    intent_id: str = Field(..., description="Intent ID")
    status: str = Field(..., description="Status: confirmed|incomplete|unknown")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters")
    message: str = Field(..., description="User-facing response message")
    transcript: Optional[str] = Field(None, description="Speech-to-text result")


class VoiceErrorResponse(BaseModel):
    """Voice processing error response model"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
