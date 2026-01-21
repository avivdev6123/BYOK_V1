import json
import math
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


# -----------------------------
# 1) Data models
# -----------------------------
@dataclass(frozen=True)
class Constraints:
    require_json: bool = False
    max_cost_usd: Optional[float] = None
    latency: str = "standard"  # "fast" | "standard"


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    supports_json: bool
    latency: str
    context_tokens: int
    in_per_1m: float
    out_per_1m: float
    reliability_score: float  # used for fallback preference


@dataclass
class BudgetWallet:
    monthly_budget_usd: float
    spent_usd: float = 0.0

    def remaining(self) -> float:
        return max(0.0, self.monthly_budget_usd - self.spent_usd)

    def can_afford(self, est_cost: float) -> bool:
        return est_cost <= self.remaining()

    def spend(self, amount: float) -> None:
        self.spent_usd += amount


# -----------------------------
# 2) Helpers: token + cost
# -----------------------------
def estimate_tokens(text: str) -> int:
    # Simple heuristic for the simulation
    return max(1, math.ceil(len(text) / 4))


def estimate_cost_usd(spec: ModelSpec, in_tokens: int, out_tokens: int) -> float:
    return (in_tokens / 1_000_000) * spec.in_per_1m + (out_tokens / 1_000_000) * spec.out_per_1m


def validate_json(text: str) -> None:
    json.loads(text)


# -----------------------------
# 3) Fake provider calls (simulate behavior)
# -----------------------------
class FakeProvider:
    """
    Simulates LLM calls.
    Cheap model sometimes returns invalid JSON to trigger fallback.
    """

    async def generate(self, spec: ModelSpec, prompt: str, max_output_tokens: int, require_json: bool) -> str:
        # "Cheap" model intentionally returns invalid JSON when require_json=True
        if spec.model == "cheap-fast" and require_json:
            return '{"ok": true, "note": "oops missing quote}'  # invalid JSON

        # More reliable model returns valid JSON
        if require_json:
            return json.dumps({"ok": True, "provider": spec.provider, "model": spec.model})

        return f"Hello from {spec.provider}/{spec.model}"


# -----------------------------
# 4) Router: filter → score → choose → fallback
# -----------------------------
async def byok_generate(
    prompt: str,
    constraints: Constraints,
    wallet: BudgetWallet,
    catalog: List[ModelSpec],
    provider: FakeProvider,
    max_output_tokens: int = 200,
) -> Dict[str, Any]:
    in_tokens = estimate_tokens(prompt)
    out_tokens = max_output_tokens

    # Apply policy: clamp max output tokens for safety
    max_output_tokens = min(max_output_tokens, 500)
    out_tokens = max_output_tokens

    # Step A: filter by capabilities/constraints
    candidates = []
    for m in catalog:
        if constraints.require_json and not m.supports_json:
            continue
        if constraints.latency == "fast" and m.latency != "fast":
            continue
        if in_tokens + out_tokens > m.context_tokens:
            continue
        candidates.append(m)

    if not candidates:
        return {"status": "error", "reason": "No models satisfy constraints."}

    # Step B: compute estimated cost, filter by max_cost and wallet budget
    scored = []
    for m in candidates:
        est = estimate_cost_usd(m, in_tokens, out_tokens)
        if constraints.max_cost_usd is not None and est > constraints.max_cost_usd:
            continue
        if not wallet.can_afford(est):
            continue
        # Score: prefer cheaper, then more reliable
        score = (est, -m.reliability_score)
        scored.append((score, est, m))

    if not scored:
        return {
            "status": "error",
            "reason": f"No affordable models. Remaining budget: ${wallet.remaining():.4f}",
        }

    scored.sort(key=lambda x: x[0])

    # Primary + fallback chain (top 3)
    chain = [m for _, _, m in scored[:3]]

    # Step C: attempt with fallback
    attempts = []
    last_error = None
    for m in chain:
        est_cost = estimate_cost_usd(m, in_tokens, out_tokens)

        try:
            text = await provider.generate(m, prompt, max_output_tokens, constraints.require_json)

            if constraints.require_json:
                validate_json(text)

            # "Spend" money only if we succeed (simplification)
            wallet.spend(est_cost)

            return {
                "status": "ok",
                "text": text,
                "provider": m.provider,
                "model": m.model,
                "input_tokens_est": in_tokens,
                "output_tokens_est": out_tokens,
                "estimated_cost_usd": round(est_cost, 8),
                "wallet_remaining_usd": round(wallet.remaining(), 6),
                "attempts": attempts + [{"provider": m.provider, "model": m.model, "result": "success"}],
            }

        except Exception as e:
            last_error = e
            attempts.append(
                {"provider": m.provider, "model": m.model, "result": f"failed: {type(e).__name__}"}
            )

    return {
        "status": "error",
        "reason": f"All attempts failed. Last error: {last_error}",
        "attempts": attempts,
    }


# -----------------------------
# 5) Run demo
# -----------------------------
if __name__ == "__main__":
    import asyncio

    catalog = [
        ModelSpec(
            provider="openai",
            model="cheap-fast",
            supports_json=True,
            latency="fast",
            context_tokens=32_000,
            in_per_1m=0.10,
            out_per_1m=0.30,
            reliability_score=0.70,
        ),
        ModelSpec(
            provider="openai",
            model="reliable-standard",
            supports_json=True,
            latency="standard",
            context_tokens=128_000,
            in_per_1m=0.20,
            out_per_1m=0.80,
            reliability_score=0.95,
        ),
        ModelSpec(
            provider="google",
            model="mid-fast",
            supports_json=True,
            latency="fast",
            context_tokens=128_000,
            in_per_1m=0.12,
            out_per_1m=0.40,
            reliability_score=0.85,
        ),
    ]

    wallet = BudgetWallet(monthly_budget_usd=0.01)  # tiny budget to show policy works
    constraints = Constraints(require_json=True, max_cost_usd=0.005, latency="fast")
    prompt = "Return JSON with keys ok, provider, model."

    result = asyncio.run(byok_generate(prompt, constraints, wallet, catalog, FakeProvider()))
    print("\n=== BYOK Simulation Result ===")
    print(json.dumps(result, indent=2))
