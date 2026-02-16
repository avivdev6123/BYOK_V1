"""
tests/unit/test_deterministic_router.py
---------------------------------------
Unit tests for the DeterministicRouter + ModelSelector pipeline.

Uses in-memory ModelCatalog objects (no DB) to test routing logic in isolation.
"""

import pytest

from app.db.model_catalog_models import ModelCatalog
from app.schemas.prompts import PromptProfile
from app.services.model_selector import ModelSelector
from app.services.deterministic_router import DeterministicRouter


def _build_catalog():
    """MVP catalog: gemini (web), openai (text), anthropic (code)."""
    return [
        ModelCatalog(
            id=1, key="gemini_flash", provider="gemini", model="models/gemini-2.5-flash",
            cost_tier="low", latency_hint="fast",
            supports_web=True, supports_json=True, good_for_code=True,
        ),
        ModelCatalog(
            id=2, key="openai_mini", provider="openai", model="gpt-4o-mini",
            cost_tier="low", latency_hint="fast",
            supports_web=False, supports_json=True, good_for_code=False,
        ),
        ModelCatalog(
            id=3, key="claude_sonnet", provider="anthropic", model="claude-sonnet-4-5-20250929",
            cost_tier="medium", latency_hint="fast",
            supports_web=False, supports_json=True, good_for_code=True,
        ),
    ]


def _make_router(catalog=None):
    if catalog is None:
        catalog = _build_catalog()
    selector = ModelSelector(catalog=catalog)
    return DeterministicRouter(selector=selector)


def _make_profile(**overrides) -> PromptProfile:
    defaults = {
        "task_type": "text_generation",
        "needs_web": False,
        "needs_code": False,
        "output_format": "text",
        "urgency": "normal",
        "confidence": 0.9,
    }
    defaults.update(overrides)
    return PromptProfile(**defaults)


# ---- MVP task_type -> provider mapping ----

def test_coding_routes_to_anthropic():
    router = _make_router()
    decision = router.route(_make_profile(task_type="coding", needs_code=True))

    assert decision.selected is not None
    assert decision.selected.provider == "anthropic"
    assert decision.selected.key == "claude_sonnet"
    assert "preferred provider" in decision.reason


def test_web_search_routes_to_gemini():
    router = _make_router()
    decision = router.route(_make_profile(task_type="web_search", needs_web=True))

    assert decision.selected is not None
    assert decision.selected.provider == "gemini"
    assert decision.selected.key == "gemini_flash"
    assert "preferred provider" in decision.reason


def test_text_generation_routes_to_openai():
    router = _make_router()
    decision = router.route(_make_profile(task_type="text_generation"))

    assert decision.selected is not None
    assert decision.selected.provider == "openai"
    assert decision.selected.key == "openai_mini"
    assert "preferred provider" in decision.reason


def test_summarization_routes_to_openai():
    router = _make_router()
    decision = router.route(_make_profile(task_type="summarization"))

    assert decision.selected is not None
    assert decision.selected.provider == "openai"


def test_extraction_routes_to_openai():
    router = _make_router()
    decision = router.route(_make_profile(task_type="extraction"))

    assert decision.selected is not None
    assert decision.selected.provider == "openai"


# ---- Fallback behavior ----

def test_fallback_when_preferred_provider_missing():
    """If anthropic is not in catalog, coding should fall back to next best."""
    catalog = [c for c in _build_catalog() if c.provider != "anthropic"]
    router = _make_router(catalog)
    decision = router.route(_make_profile(task_type="coding", needs_code=True))

    assert decision.selected is not None
    # Should fall back to gemini (has good_for_code=True)
    assert decision.selected.provider == "gemini"
    assert "fallback" in decision.reason


# ---- No candidates ----

def test_no_candidates_when_constraints_unsatisfiable():
    """Web search with no web-capable models should return no candidates."""
    catalog = [c for c in _build_catalog() if not c.supports_web]
    router = _make_router(catalog)
    decision = router.route(_make_profile(task_type="web_search", needs_web=True))

    assert decision.selected is None
    assert decision.candidates == []
    assert "No model" in decision.reason


def test_empty_catalog():
    router = _make_router(catalog=[])
    decision = router.route(_make_profile())

    assert decision.selected is None
    assert decision.candidates == []


# ---- Candidates list ----

def test_all_passing_candidates_returned():
    """Route decision should include all candidates that pass hard filters."""
    router = _make_router()
    decision = router.route(_make_profile(task_type="text_generation"))

    # All 3 models pass filters for a basic text_generation prompt
    assert len(decision.candidates) == 3
    assert decision.selected is not None


# ---- Constraints mapping ----

def test_urgency_fast_maps_to_latency_fast():
    router = _make_router()
    decision = router.route(_make_profile(urgency="fast"))

    assert decision.constraints.latency_tier == "fast"


def test_urgency_normal_maps_to_latency_normal():
    router = _make_router()
    decision = router.route(_make_profile(urgency="normal"))

    assert decision.constraints.latency_tier == "normal"