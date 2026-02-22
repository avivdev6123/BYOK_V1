"""
app/schemas/keys.py
-------------------
Milestone 4: API key management request/response schemas.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class KeyCreateRequest(BaseModel):
    provider: Literal["gemini", "openai", "anthropic"]
    api_key: str = Field(min_length=1)


class KeyResponse(BaseModel):
    id: int
    provider: str
    api_key_masked: str
    status: str
    validated_at: Optional[datetime] = None
    discovered_models: Optional[list[str]] = None
    created_at: datetime


class KeyListResponse(BaseModel):
    keys: list[KeyResponse]