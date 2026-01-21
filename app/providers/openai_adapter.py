from app.providers.base import ProviderAdapter

class OpenAIAdapter(ProviderAdapter):
    async def generate(self, prompt: str, max_output_tokens: int, require_json: bool) -> str:
        # intentionally sometimes invalid JSON to demonstrate fallback
        if require_json:
            return '{"ok": true, "provider": "openai", "model": "gpt-4o-mini"'  # missing }
        return "Stub OpenAI response"
