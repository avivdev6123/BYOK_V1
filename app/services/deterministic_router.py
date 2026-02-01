# app/services/deterministic_router.py

from app.schemas.prompts import PromptProfile
from app.schemas.routing import RouteConstraints, RouteDecision
from app.services.model_selector import ModelSelector


class DeterministicRouter:
    """
    Converts semantic intent (PromptProfile) into a routing decision.
    """

    def __init__(self, selector: ModelSelector):
        self.selector = selector

    def route(self, profile: PromptProfile) -> RouteDecision:
        constraints = RouteConstraints(
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

        return RouteDecision(
            constraints=constraints,
            candidates=candidates,
            selected=candidates[0],
            reason="Selected lowest cost / lowest latency model that satisfies constraints",
        )