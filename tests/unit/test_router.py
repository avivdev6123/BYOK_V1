import pytest
from app.schemas.generate import GenerateRequest, GenerateConstraints
from app.services.router import route_and_generate

@pytest.mark.asyncio
async def test_router_falls_back_to_valid_json_provider():
    req = GenerateRequest(
        prompt="Return JSON with ok/provider/model",
        constraints=GenerateConstraints(require_json=True, latency="fast", max_output_tokens=64),
    )
    res = await route_and_generate(req)

    # OpenAI stub returns invalid JSON, so router should fall back to google stub
    assert res.provider == "google"
    assert res.model == "gemini-1.5-flash"
    assert res.attempts >= 2
