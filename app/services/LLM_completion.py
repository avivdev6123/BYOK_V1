"""
app/services/LLM_completion.py
------------------------------
Milestone 3B: Generic LLM completion client.

Supports 3 providers (MVP):
- gemini  (google-genai SDK)
- openai  (openai SDK)
- anthropic (anthropic SDK)
"""

import os
from dataclasses import dataclass, field
from typing import Literal

from google import genai
from google.genai import types as genai_types
from openai import OpenAI
from anthropic import Anthropic

ProviderName = Literal["gemini", "openai", "anthropic"]


@dataclass
class LLMResult:
    """Result from an LLM call, including optional web sources."""
    text: str
    sources: list[dict] = field(default_factory=list)


class LLMCompletionClient:
    """
    Generic LLM completion client.
    Dispatches to the correct provider SDK based on provider name.
    """

    def __init__(self):
        self._clients: dict = {}

    def _get_gemini_client(self) -> genai.Client:
        if "gemini" not in self._clients:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("Missing GEMINI_API_KEY")
            self._clients["gemini"] = genai.Client(api_key=api_key)
        return self._clients["gemini"]

    def _get_openai_client(self) -> OpenAI:
        if "openai" not in self._clients:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError("Missing OPENAI_API_KEY")
            self._clients["openai"] = OpenAI(api_key=api_key)
        return self._clients["openai"]

    def _get_anthropic_client(self) -> Anthropic:
        if "anthropic" not in self._clients:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("Missing ANTHROPIC_API_KEY")
            self._clients["anthropic"] = Anthropic(api_key=api_key)
        return self._clients["anthropic"]

    def generate(self, prompt: str, provider: ProviderName, model: str, needs_web: bool = False) -> LLMResult:
        if provider == "gemini":
            return self._generate_gemini(prompt, model, needs_web=needs_web)
        elif provider == "openai":
            return self._generate_openai(prompt, model)
        elif provider == "anthropic":
            return self._generate_anthropic(prompt, model)
        raise ValueError(f"Unsupported provider: {provider}")

    def _generate_gemini(self, prompt: str, model: str, needs_web: bool = False) -> LLMResult:
        client = self._get_gemini_client()

        config = None
        if needs_web:
            config = genai_types.GenerateContentConfig(
                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
            )

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        sources = []
        if needs_web and response.candidates:
            metadata = response.candidates[0].grounding_metadata
            if metadata and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    if chunk.web:
                        sources.append({
                            "title": chunk.web.title or "",
                            "url": chunk.web.uri or "",
                        })

        return LLMResult(text=response.text or "", sources=sources)

    def _generate_openai(self, prompt: str, model: str) -> LLMResult:
        client = self._get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResult(text=response.choices[0].message.content or "")

    def _generate_anthropic(self, prompt: str, model: str) -> LLMResult:
        client = self._get_anthropic_client()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResult(text=response.content[0].text or "")