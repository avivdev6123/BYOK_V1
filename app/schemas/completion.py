"""
app/schemas/completion.py
-------------------------
Milestone 3B: Completion pipeline schemas.

Request: prompt_id (references an already-profiled prompt)
Response: LLM output + routing metadata
"""

from pydantic import BaseModel, Field

from app.schemas.routing import RouteDecision


class CompletionRequest(BaseModel):
    prompt_id: int = Field(ge=1)


class CompletionResponse(BaseModel):
    prompt_id: int
    text: str
    provider: str
    model: str
    attempts: int = Field(ge=1)
    route_decision: RouteDecision