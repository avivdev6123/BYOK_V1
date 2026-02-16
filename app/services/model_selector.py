# app/services/model_selector.py
# ------------------------------
# Milestone 3B: Deterministic scoring with:
# - task_type weighting
# - provider preference
# - deterministic tie-break + more informative per-candidate reasons
# """
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from app.schemas.routing import (
    RouteConstraints,
    ModelCandidate,
    ProviderName,
    TaskType
)
from app.db.model_catalog_models import ModelCatalog

_COST_ORDER = {"low": 0, "medium": 1, "high": 2}
_LATENCY_ORDER = {"fast": 0, "normal": 1}


@dataclass(frozen=True)
class SelectionConfig():
    """
    +    Deterministic tie-break + preference configuration.
    +
    +    - provider_preference: when everything else is equal, prefer earlier providers
    +    - weights: keep them small + stable to preserve determinism
    +    """
    provider_preference: Sequence[ProviderName] = ("gemini", "openai")
    # Score weights (lower score = better)
    w_cost: float = 10.0
    w_latency: float = 1.0
    w_provider_pref: float = 0.1

    # Task bonuses/penalties (added to score; negative = better)
    bonus_code_good: float = -0.5
    bonus_web_supported: float = -0.5
    bonus_json_supported: float = -0.2

    # Light preferences by task type (optional, but useful)
    # (These are additive nudges, not hard filters)
    task_type_nudges: dict[TaskType, float] = field(default_factory=lambda: {
        "coding": -0.2,
        "summarization": 0.0,
        "text_generation": 0.0,
        "extraction": -0.1,
        "web_search": -0.1,
    })


class ModelSelector:
    """
        Pure deterministic ranking engine.
        - No DB logic
        - No LLM calls
        - No side effects
    """

    def __init__(self, catalog: List[ModelCatalog], config: SelectionConfig | None = None):
        self.catalog = catalog
        self.config = config if config is not None else SelectionConfig()

    def select(self, constraints: RouteConstraints) -> List[ModelCandidate]:
        candidates: List[ModelCandidate] = []

        for m in self.catalog:
            # ---------- HARD FILTERS (must satisfy) ----------
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

            # ---------- SCORE (lower = better) ----------
            provider_rank = self._provider_rank(m.provider)
            cost_part = _COST_ORDER[m.cost_tier] * self.config.w_cost
            latency_part = _LATENCY_ORDER[m.latency_hint] * self.config.w_latency
            provider_part = provider_rank * self.config.w_provider_pref

            task_nudge = float(self.config.task_type_nudges.get(constraints.task_type, 0.0))

            bonuses = 0.0
            if constraints.task_type == "coding" and m.good_for_code:
                bonuses += self.config.bonus_code_good
            if constraints.needs_web and m.supports_web:
                bonuses += self.config.bonus_web_supported
            if constraints.output_format == "json" and m.supports_json:
                bonuses += self.config.bonus_json_supported

            total_score = cost_part + latency_part + provider_part + task_nudge + bonuses

            reason = self._build_reason(
                constraints=constraints,
                model=m,
                provider_rank=provider_rank,
                cost_part=cost_part,
                latency_part=latency_part,
                provider_part=provider_part,
                task_nudge=task_nudge,
                bonuses=bonuses,
                total=total_score,
            )

            candidates.append(
                ModelCandidate(
                    key=m.key,
                    provider=m.provider,
                    model=m.model,
                    cost_tier=m.cost_tier,
                    latency_tier=m.latency_hint,
                    score=float(total_score),
                    reason=reason,
                )
            )

        # Deterministic sorting:
        # 1) total score
        # 2) provider preference
        # 3) stable tie-break by key + model
        candidates.sort(key=lambda c: (c.score, self._provider_rank(c.provider), c.key, c.model))
        return candidates

    def _provider_rank(self, provider: ProviderName) -> int:
        try:
            return list(self.config.provider_preference).index(provider)
        except ValueError:
            return 999

    def _build_reason(
        self,
        *,
        constraints: RouteConstraints,
        model: ModelCatalog,
        provider_rank: int,
        cost_part: float,
        latency_part: float,
        provider_part: float,
        task_nudge: float,
        bonuses: float,
        total: float,
    ) -> str:
        bits: list[str] = []
        bits.append(f"passes filters for task_type={constraints.task_type}")
        bits.append(f"cost={model.cost_tier}({cost_part:.1f})")
        bits.append(f"latency={model.latency_hint}({latency_part:.1f})")
        bits.append(f"provider_pref_rank={provider_rank}({provider_part:.1f})")
        if task_nudge != 0:
            bits.append(f"task_nudge={task_nudge:.1f}")
        if bonuses != 0:
            bits.append(f"bonuses={bonuses:.1f}")
        bits.append(f"total={total:.3f}")
        return " | ".join(bits)
