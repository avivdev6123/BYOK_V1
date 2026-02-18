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
You are a prompt classifier. Output ONLY valid JSON — no markdown, no code fences, no comments.

Classify the user's prompt into one of these task types:

- "web_search": The prompt asks about current events, real-time data, live information,
  or anything that requires browsing the internet to answer accurately.
  Examples: "What's the weather in NYC?", "Latest news about AI regulation",
  "Find the current price of Bitcoin".

- "coding": The prompt asks to write, debug, review, refactor, or explain code.
  Also applies to technical implementation questions.
  Examples: "Write a Python function to sort a list", "Fix this SQL query",
  "How do I implement a binary tree in Java?", "Review this code for bugs".

- "text_generation": The prompt asks to create original text content — emails,
  essays, stories, marketing copy, or general creative/informational writing.
  Examples: "Write an email to my manager", "Draft a blog post about AI",
  "Generate a product description".

- "summarization": The prompt provides existing text and asks for a shorter version,
  key points, or a condensed overview.
  Examples: "Summarize this article", "Give me the key takeaways from this report",
  "TL;DR of this document".

- "extraction": The prompt asks to pull specific data, entities, or structured
  information out of provided text.
  Examples: "Extract all dates from this paragraph", "List the companies mentioned",
  "Parse this resume into JSON fields".

Set the flags:
- "needs_web": true ONLY if the prompt requires live internet access to answer.
- "needs_code": true ONLY if the prompt involves writing or reasoning about code.
- "output_format": "json" if the user explicitly asks for JSON output, otherwise "text".
- "urgency": "fast" if the user indicates time pressure or wants a quick answer, otherwise "normal".
- "confidence": your confidence in the classification (0.0 to 1.0).

JSON schema:
{
  "task_type": "web_search | text_generation | coding | summarization | extraction",
  "needs_web": true/false,
  "needs_code": true/false,
  "output_format": "text | json",
  "urgency": "fast | normal",
  "confidence": 0.0 to 1.0
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
        # Strip markdown code fences if Gemini wraps the JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[1]  # remove first line (```json)
            text = text.rsplit("```", 1)[0]  # remove closing ```
            text = text.strip()
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