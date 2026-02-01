"""
model_catalog.py
----------------
Central registry for provider model identifiers.

Why this exists:
- Avoid hardcoding model strings in routing rules.
- Keep model names and defaults in one place.
- Prepare for future capabilities (cost, web support, JSON mode, etc.).
"""

from dataclasses import dataclass
from typing import Literal


ProviderName = Literal["gemini", "openai"]


@dataclass(frozen=True)
class ModelRef:
    """
    A single model reference.

    provider: which LLM provider
    model: provider-specific model identifier string
    """
    provider: ProviderName
    model: str


class ModelCatalog:
    """
    Minimal model catalog for Milestone 3.

    In later milestones this can expand into:
    - capabilities (supports_web, supports_json_mode, etc.)
    - pricing metadata
    - max tokens
    - context window
    """

    # Gemini defaults
    GEMINI_FAST = ModelRef(provider="gemini", model="models/gemini-1.5-flash")
    GEMINI_STRONG = ModelRef(provider="gemini", model="models/gemini-1.5-pro")

    # (Optional placeholders for later)
    OPENAI_FAST = ModelRef(provider="openai", model="gpt-4o-mini")
    OPENAI_STRONG = ModelRef(provider="openai", model="gpt-4o")

    @classmethod
    def fast_default(cls) -> ModelRef:
        """Default fast/cheap model."""
        return cls.GEMINI_FAST

    @classmethod
    def strong_default(cls) -> ModelRef:
        """Default strong model."""
        return cls.GEMINI_STRONG