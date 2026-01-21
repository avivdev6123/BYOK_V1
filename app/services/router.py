from app.schemas.generate import GenerateRequest, GenerateResponse
from app.utils.token_estimator import estimate_tokens
from app.services.cost import estimate_cost_usd
from app.services.validator import validate_json
from app.providers.openai_adapter import OpenAIAdapter
from app.providers.gemini_adapter import GeminiAdapter

MODEL_CATALOG = [
    {"provider": "openai", "model": "gpt-4o-mini", "supports_json": True, "latency": "fast", "context": 128000},
    {"provider": "google", "model": "gemini-1.5-flash", "supports_json": True, "latency": "fast", "context": 128000},
    {"provider": "openai", "model": "gpt-4o", "supports_json": True, "latency": "standard", "context": 128000},
]

ADAPTERS = {
    "openai": OpenAIAdapter(),
    "google": GeminiAdapter(),
}

async def route_and_generate(req: GenerateRequest) -> GenerateResponse:
    prompt = req.prompt
    c = req.constraints

    in_tokens = estimate_tokens(prompt)
    out_tokens = c.max_output_tokens

    # 1) filter candidates
    candidates = []
    for m in MODEL_CATALOG:
        if c.require_json and not m["supports_json"]:
            continue
        if c.latency == "fast" and m["latency"] != "fast":
            continue
        if c.allowed_providers and m["provider"] not in c.allowed_providers:
            continue
        if c.blocked_providers and m["provider"] in c.blocked_providers:
            continue
        if in_tokens + out_tokens > m["context"]:
            continue
        candidates.append(m)

    if not candidates:
        raise RuntimeError("No models satisfy constraints.")

    # 2) score by estimated cost, then pick cheapest
    scored = []
    for m in candidates:
        est = estimate_cost_usd(m["provider"], m["model"], in_tokens, out_tokens)
        if c.max_cost_usd is not None and est > c.max_cost_usd:
            continue
        scored.append((est, m))

    if not scored:
        raise RuntimeError("No models satisfy max_cost_usd constraint.")

    scored.sort(key=lambda x: x[0])
    chain = [m for _, m in scored[:3]]  # primary + 2 fallbacks max

    # 3) execute with fallback
    attempts = 0
    last_err: Exception | None = None

    for m in chain:
        attempts += 1
        adapter = ADAPTERS[m["provider"]]
        try:
            text = await adapter.generate(prompt, out_tokens, c.require_json)
            if c.require_json:
                validate_json(text)
            est = estimate_cost_usd(m["provider"], m["model"], in_tokens, out_tokens)
            return GenerateResponse(
                text=text,
                provider=m["provider"],
                model=m["model"],
                estimated_cost_usd=round(est, 8),
                attempts=attempts,
                metadata={"input_tokens_est": in_tokens, "output_tokens_est": out_tokens, "fallback_chain": chain},
            )
        except Exception as e:
            last_err = e

    raise RuntimeError(f"All attempts failed. Last error: {last_err}")
