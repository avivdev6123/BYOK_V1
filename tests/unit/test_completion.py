"""
tests/unit/test_completion.py
-----------------------------
Unit tests for the completion service (Milestone 3B).

Uses mock LLMCompletionClient and in-memory DB to avoid real API calls.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.prompt_models import Prompt
from app.db.model_catalog_models import ModelCatalog
from app.services.completion_service import execute_completion
from app.services.LLM_completion import LLMCompletionClient, LLMResult


@pytest.fixture
def db():
    """In-memory SQLite DB with prompt and catalog tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed catalog: 3 MVP models
    session.add_all([
        ModelCatalog(
            key="gemini_flash", provider="gemini", model="models/gemini-2.5-flash",
            cost_tier="low", latency_hint="fast",
            supports_web=True, supports_json=True, good_for_code=True,
        ),
        ModelCatalog(
            key="openai_mini", provider="openai", model="gpt-4o-mini",
            cost_tier="low", latency_hint="fast",
            supports_web=False, supports_json=True, good_for_code=False,
        ),
        ModelCatalog(
            key="claude_sonnet", provider="anthropic", model="claude-sonnet-4-5-20250929",
            cost_tier="medium", latency_hint="fast",
            supports_web=False, supports_json=True, good_for_code=True,
        ),
    ])

    # Seed a profiled prompt (coding task)
    session.add(Prompt(
        username="test",
        raw_prompt="Write a Python function to sort a list",
        prompt_profile_json={
            "task_type": "coding",
            "needs_web": False,
            "needs_code": True,
            "output_format": "text",
            "urgency": "normal",
            "confidence": 0.95,
        },
    ))

    # Seed a prompt without profile
    session.add(Prompt(
        username="test",
        raw_prompt="No profile prompt",
        prompt_profile_json=None,
    ))

    session.commit()
    yield session
    session.close()


def test_completion_happy_path(db):
    """First candidate succeeds — should return on first attempt."""
    client = MagicMock(spec=LLMCompletionClient)
    client.generate.return_value = LLMResult(text="def sort_list(lst): return sorted(lst)")

    result = execute_completion(prompt_id=1, db=db, client=client)

    assert result.prompt_id == 1
    assert result.attempts == 1
    assert result.text == "def sort_list(lst): return sorted(lst)"
    # Coding task should route to anthropic (preferred provider)
    assert result.provider == "anthropic"
    assert "coding" in result.route_decision.reason
    client.generate.assert_called_once()


def test_completion_fallback(db):
    """First candidate fails, second succeeds."""
    client = MagicMock(spec=LLMCompletionClient)
    client.generate.side_effect = [
        RuntimeError("Provider down"),
        LLMResult(text="def sort_list(lst): return sorted(lst)"),
    ]

    result = execute_completion(prompt_id=1, db=db, client=client)

    assert result.attempts == 2
    assert len(result.text) > 0
    assert client.generate.call_count == 2


def test_completion_all_fail(db):
    """All candidates fail — should raise RuntimeError."""
    client = MagicMock(spec=LLMCompletionClient)
    client.generate.side_effect = RuntimeError("Provider down")

    with pytest.raises(RuntimeError, match="All .* attempts failed"):
        execute_completion(prompt_id=1, db=db, client=client)


def test_completion_prompt_not_found(db):
    """Non-existent prompt_id — should raise LookupError."""
    client = MagicMock(spec=LLMCompletionClient)

    with pytest.raises(LookupError, match="not found"):
        execute_completion(prompt_id=999, db=db, client=client)


def test_completion_no_profile(db):
    """Prompt exists but has no profile — should raise ValueError."""
    client = MagicMock(spec=LLMCompletionClient)

    with pytest.raises(ValueError, match="no profile"):
        execute_completion(prompt_id=2, db=db, client=client)