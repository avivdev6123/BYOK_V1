"""
gemini_profiler.py
------------------
Milestone 2: LLM JSON extraction (prompt profiling) using Gemini (Google AI Studio).

Uses the new official google-genai SDK (not the deprecated google.generativeai).
"""

import os
import json

from google import genai
from pydantic import ValidationError

from app.schemas.prompts import PromptProfile


class GeminiPromptProfiler:
    """
    Prompt profiler that uses Gemini to classify prompts into a JSON profile.
    """

    def __init__(self, model_name: str = "models/gemini-2.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY environment variable")

        # Initialize Gemini client
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def profile(self, raw_prompt: str) -> PromptProfile:
        """
        Call Gemini once and return a validated PromptProfile.
        """

        system_instruction = """
        You are a strict JSON generator.


        Rules:
        - Output ONLY valid JSON.
        - No markdown.
        - No code fences.
        - No comments.
        - No trailing commas.
        - All keys in double quotes.
        - Use lowercase true/false (JSON), NOT True/False.
        - Use null, NOT None.


        Schema:
        {
        "task_type": "web_search | text_generation | coding | summarization | extraction",
        "needs_web": true/false,
        "needs_code": true/false,
        "output_format": "text | json",
        "urgency": "fast | normal",
        "confidence": number between 0 and 1
        }
        """

        user_prompt = f"""
Classify this prompt:

\"\"\"{raw_prompt}\"\"\"
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[system_instruction, user_prompt],
        )

        text = (response.text or "").strip()
        # Convert Python booleans to JSON booleans if Gemini slips
        text = (text.replace("True", "true").replace("False", "false")
                .replace("None", "null"))
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(f"Gemini did not return valid JSON:\n{text}")

        try:
            profile = PromptProfile(**data)
        except ValidationError as e:
            raise RuntimeError(f"Gemini JSON does not match schema:\n{data}") from e

        return profile