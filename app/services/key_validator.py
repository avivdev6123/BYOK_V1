"""
app/services/key_validator.py
-----------------------------
Validates API keys by making lightweight calls to each provider's SDK.
Returns validation result with discovered models.
"""

from typing import Any

from google import genai
from openai import OpenAI
from anthropic import Anthropic


def validate_key(provider: str, api_key: str) -> dict[str, Any]:
    """
    Validate an API key by calling the provider's API.

    Returns:
        {"valid": bool, "error": str | None, "models": list[str]}
    """
    if provider == "gemini":
        return _validate_gemini(api_key)
    elif provider == "openai":
        return _validate_openai(api_key)
    elif provider == "anthropic":
        return _validate_anthropic(api_key)
    return {"valid": False, "error": f"Unknown provider: {provider}", "models": []}


def _validate_gemini(api_key: str) -> dict[str, Any]:
    try:
        client = genai.Client(api_key=api_key)
        models = []
        for model in client.models.list():
            models.append(model.name)
        return {"valid": True, "error": None, "models": models}
    except Exception as e:
        return {"valid": False, "error": str(e), "models": []}


def _validate_openai(api_key: str) -> dict[str, Any]:
    try:
        client = OpenAI(api_key=api_key)
        response = client.models.list()
        models = [m.id for m in response.data]
        return {"valid": True, "error": None, "models": models}
    except Exception as e:
        return {"valid": False, "error": str(e), "models": []}


def _validate_anthropic(api_key: str) -> dict[str, Any]:
    try:
        client = Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        return {"valid": True, "error": None, "models": [
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-6",
        ]}
    except Exception as e:
        return {"valid": False, "error": str(e), "models": []}