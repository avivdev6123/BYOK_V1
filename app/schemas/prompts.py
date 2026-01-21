"""
Pydantic schemas for Prompt API.

These classes define:
- What the user sends (request)
- What the API returns (response)
They also automatically generate Swagger documentation.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class PromptCreateRequest(BaseModel):
    """
    Request body when a user submits a prompt.
    """
    # Username of the caller (MVP identity)
    username: str = Field(default="demo", min_length=1)

    # The actual prompt text
    prompt: str = Field(min_length=1)


class PromptCreateResponse(BaseModel):
    """
    Response after storing a prompt.
    """
    # Database ID of the stored prompt
    prompt_id: int

    # Simple status indicator
    status: str = "stored"


class PromptReadResponse(BaseModel):
    """
    Response when fetching a stored prompt.
    """
    prompt_id: int
    username: str
    raw_prompt: str
    created_at: datetime
