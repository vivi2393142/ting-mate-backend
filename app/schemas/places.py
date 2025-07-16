from typing import Any, Optional

from pydantic import BaseModel


class PlaceSearchRequest(BaseModel):
    query: str
    language: Optional[str] = "en"
    region: Optional[str] = None


class PlaceSearchResponse(BaseModel):
    results: Any  # Directly proxy Google API results
