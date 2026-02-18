"""
tests/unit/test_gemini_profiler.py
----------------------------------
Unit tests for Gemini profiler response parsing.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.gemini_profiler import GeminiPromptProfiler


VALID_PROFILE = {
    "task_type": "text_generation",
    "needs_web": False,
    "needs_code": False,
    "output_format": "text",
    "urgency": "normal",
    "confidence": 0.95,
}


def _make_profiler_with_mock_response(response_text: str) -> GeminiPromptProfiler:
    """Create a profiler with a mocked Gemini client that returns the given text."""
    with patch.object(GeminiPromptProfiler, "__init__", lambda self, **kwargs: None):
        profiler = GeminiPromptProfiler()
        profiler.client = MagicMock()
        profiler.model_name = "models/gemini-2.5-flash"

        mock_response = MagicMock()
        mock_response.text = response_text
        profiler.client.models.generate_content.return_value = mock_response

        return profiler


def test_parse_clean_json():
    """Gemini returns clean JSON without code fences."""
    profiler = _make_profiler_with_mock_response(json.dumps(VALID_PROFILE))
    result = profiler.profile("test prompt")

    assert result.task_type == "text_generation"
    assert result.confidence == 0.95


def test_parse_json_wrapped_in_code_fences():
    """Gemini wraps JSON in ```json ... ``` markdown fences."""
    wrapped = f"```json\n{json.dumps(VALID_PROFILE, indent=2)}\n```"
    profiler = _make_profiler_with_mock_response(wrapped)
    result = profiler.profile("test prompt")

    assert result.task_type == "text_generation"
    assert result.confidence == 0.95


def test_parse_json_with_python_booleans():
    """Gemini returns Python-style True/False instead of JSON true/false."""
    text = '{"task_type": "coding", "needs_web": False, "needs_code": True, "output_format": "text", "urgency": "fast", "confidence": 0.8}'
    profiler = _make_profiler_with_mock_response(text)
    result = profiler.profile("test prompt")

    assert result.task_type == "coding"
    assert result.needs_web is False
    assert result.needs_code is True


def test_parse_invalid_json_raises():
    """Gemini returns garbage — should raise RuntimeError."""
    profiler = _make_profiler_with_mock_response("This is not JSON at all")

    with pytest.raises(RuntimeError, match="did not return valid JSON"):
        profiler.profile("test prompt")


def test_parse_valid_json_bad_schema_raises():
    """Gemini returns valid JSON but wrong schema — should raise RuntimeError."""
    bad_schema = '{"foo": "bar"}'
    profiler = _make_profiler_with_mock_response(bad_schema)

    with pytest.raises(RuntimeError, match="does not match schema"):
        profiler.profile("test prompt")