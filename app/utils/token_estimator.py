import math

def estimate_tokens(text: str) -> int:
    # fast heuristic for MVP
    return max(1, math.ceil(len(text) / 4))
