from app.services.cost import estimate_cost_usd

def test_cost_estimation():
    cost = estimate_cost_usd("openai", "gpt-4o-mini", 1000, 500)
    assert abs(cost - 0.000125) < 1e-9
