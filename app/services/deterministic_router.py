# app/services/deterministic_router.py

from app.schemas.prompts import PromptProfile
from app.schemas.routing import RouteConstraints, RouteDecision, TaskType
from app.services.model_selector import ModelSelector

# MVP: task_type -> preferred provider
_TASK_PROVIDER_MAP: dict[TaskType, str] = {
    "web_search": "gemini",
    "coding": "anthropic",
    "text_generation": "openai",
    "summarization": "openai",
    "extraction": "openai",
}


class DeterministicRouter:
    """
    Converts semantic intent (PromptProfile) into a routing decision.

    MVP logic: picks the preferred provider for the task_type,
    falls back to scoring order if the preferred provider isn't available.
    """

    def __init__(self, selector: ModelSelector):
        self.selector = selector

    def route(self, profile: PromptProfile) -> RouteDecision:
        constraints = RouteConstraints(
            task_type=profile.task_type,
            needs_web=profile.needs_web,
            needs_code=profile.needs_code,
            output_format=profile.output_format,
            latency_tier="fast" if profile.urgency == "fast" else "normal",
        )

        candidates = self.selector.select(constraints)

        if not candidates:
            return RouteDecision(
                constraints=constraints,
                candidates=[],
                selected=None,
                reason="No model in catalog satisfies routing constraints",
            )

        # Promote the preferred provider to the top
        preferred_provider = _TASK_PROVIDER_MAP.get(constraints.task_type)
        preferred = None
        if preferred_provider:
            preferred = next(
                (c for c in candidates if c.provider == preferred_provider), None
            )

        if preferred:
            top = preferred
            # Reorder: selected first, then remaining candidates as fallbacks
            remaining = [c for c in candidates if c.key != top.key]
            ordered = [top] + remaining
            reason = (
                f"Selected {top.provider}:{top.key} — "
                f"preferred provider for task_type={constraints.task_type}"
            )
        else:
            top = candidates[0]
            ordered = candidates
            reason = (
                f"Selected {top.provider}:{top.key} (score={top.score:.3f}) — "
                f"fallback (preferred provider not available for task_type={constraints.task_type})"
            )

        return RouteDecision(
            constraints=constraints,
            candidates=ordered,
            selected=top,
            reason=reason,
        )