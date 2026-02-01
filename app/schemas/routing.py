"""
app/schemas/routing.py
----------------------
Milestone 3: Deterministic Routing Engine schemas.

Goal:
- Input: PromptProfile (Milestone 2 output)
- Output: RouteDecision:
  - constraints (what we need)
  - ranked candidates (what matches)
  - selected (the chosen model)
"""

from typing import Literal
from pydantic import BaseModel, Field

from app.schemas.prompts import PromptProfile


# Providers we support in the router (expand later)
ProviderName = Literal["gemini", "openai"]

# Simple tiers (used for deterministic ranking & future policy engines)
CostTier = Literal["low", "medium", "high"]
LatencyTier = Literal["fast", "normal"]


class RouteConstraints(BaseModel):
    """
    Machine-readable constraints derived from PromptProfile.
    Used to filter catalog models.
    """

    needs_web: bool
    needs_code: bool
    output_format: Literal["text", "json"]
    latency_tier: LatencyTier

    # Max cost tier allowed (future: user/org budgets can set this)
    max_cost_tier: CostTier = "high"


class ModelCandidate(BaseModel):
    """
    A single candidate model that matches constraints.
    """

    provider: ProviderName
    model: str = Field(min_length=1)

    # Stable ID from catalog (useful for analytics / DB storage later)
    key: str = Field(min_length=1)

    # Deterministic scoring (lower is better, but we store float for flexibility)
    score: float = Field(ge=0.0)

    # Explainability for why it was included / ranked
    reason: str = Field(min_length=1)

    # Useful metadata
    cost_tier: CostTier
    latency_tier: LatencyTier


class RouteDecision(BaseModel):
    """
    Router output.

    - constraints: what the prompt needs
    - candidates: ranked options (best first)
    - selected: chosen option (usually candidates[0])
    - reason: human-friendly explanation (high-level)
    """

    constraints: RouteConstraints
    candidates: list[ModelCandidate] = []
    selected: ModelCandidate | None = None
    reason: str = Field(min_length=1)


class RouteRequest(BaseModel):
    """
    POST /v1/route body.
    The router does NOT call any provider. It only decides.
    """

    profile: PromptProfile


class RouteResponse(BaseModel):
    """
    POST /v1/route response.
    """

    decision: RouteDecision