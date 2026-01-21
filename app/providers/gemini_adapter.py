import json
from app.providers.base import ProviderAdapter

class GeminiAdapter(ProviderAdapter):
    async def generate(self, prompt: str, max_output_tokens: int, require_json: bool) -> str:
        if require_json:
            return json.dumps({"ok": True, "provider": "google", "model": "gemini-1.5-flash"})
        return "Stub Gemini response"
