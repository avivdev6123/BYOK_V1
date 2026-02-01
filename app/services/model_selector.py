# app/services/model_selector.py

from typing import List

from app.schemas.routing import RouteConstraints, ModelCandidate
from app.db.model_catalog_models import ModelCatalog

_COST_ORDER = {"low": 0, "medium": 1, "high": 2}
_LATENCY_ORDER = {"fast": 0, "normal": 1}


class ModelSelector:
    """
    Pure deterministic ranking engine.
    No DB logic, no LLM calls, no side effects.
    """

    def __init__(self, catalog: List[ModelCatalog]):
        self.catalog = catalog

    def select(self, constraints: RouteConstraints) -> List[ModelCandidate]:
        candidates: list[ModelCandidate] = []

        for m in self.catalog:
            if constraints.needs_web and not m.supports_web:
                continue
            if constraints.needs_code and not m.good_for_code:
                continue
            if constraints.output_format == "json" and not m.supports_json:
                continue
            if constraints.latency_tier == "fast" and m.latency_hint != "fast":
                continue
            if _COST_ORDER[m.cost_tier] > _COST_ORDER[constraints.max_cost_tier]:
                continue

            score = (
                _COST_ORDER[m.cost_tier] * 10
                + _LATENCY_ORDER[m.latency_hint]
            )

            candidates.append(
                ModelCandidate(
                    key=m.key,
                    provider=m.provider,
                    model=m.model,
                    cost_tier=m.cost_tier,
                    latency_tier=m.latency_hint,
                    score=float(score),
                    reason="Matches constraints and ranked by cost/latency",
                )
            )

        candidates.sort(key=lambda c: (c.score, c.provider, c.key))
        return candidates