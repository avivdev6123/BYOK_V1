PRICING = {
    ("openai", "gpt-4o-mini"): {"in_per_1m": 0.05, "out_per_1m": 0.15},
    ("google", "gemini-1.5-flash"): {"in_per_1m": 0.10, "out_per_1m": 0.40},
    ("openai", "gpt-4o"): {"in_per_1m": 5.00, "out_per_1m": 15.00},  # expensive fallback
}

def estimate_cost_usd(provider: str, model: str, in_tokens: int, out_tokens: int) -> float:
    p = PRICING.get((provider, model))
    if not p:
        return 1e9
    return (in_tokens / 1_000_000) * p["in_per_1m"] + (out_tokens / 1_000_000) * p["out_per_1m"]
