from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any

LatencyTier = Literal["fast", "standard"]

class GenerateConstraints(BaseModel):
    require_json: bool = False
    latency: LatencyTier = "standard"
    max_cost_usd: Optional[float] = Field(default=None, ge=0)
    max_output_tokens: int = Field(default=256, ge=1, le=4096)
    allowed_providers: Optional[List[str]] = None
    blocked_providers: Optional[List[str]] = None

class GenerateRequest(BaseModel):
    username: str = "demo"
    prompt: str
    constraints: GenerateConstraints = GenerateConstraints()

class GenerateResponse(BaseModel):
    text: str
    provider: str
    model: str
    estimated_cost_usd: float
    attempts: int
    metadata: Dict[str, Any] = {}

