# Milestone 3 — Model Catalog, Deterministic Routing & LLM Completion

## Goal
Build the full pipeline: classify a prompt (Milestone 2), route it to the best LLM provider/model, and execute the completion with fallback support.

---

## What Was Added (with Code References)

### 1. Model Catalog (Milestone 3A)
**Purpose:** Database-backed registry of available models with capability flags and cost/latency tiers.

**Code:**
- `app/db/model_catalog_models.py`
  - Class: `ModelCatalog`
  - Fields: `key`, `provider`, `model`, `cost_tier`, `latency_hint`, `supports_web`, `supports_json`, `good_for_code`
- `app/services/model_catalog_repo.py`
  - Function: `load_catalog(db) -> list[ModelCatalog]`

**MVP Catalog (3 models):**

| Key | Provider | Model | Web | Code | Cost | Latency |
|-----|----------|-------|-----|------|------|---------|
| gemini_flash | gemini | models/gemini-2.5-flash | yes | yes | low | fast |
| openai_mini | openai | gpt-4o-mini | no | no | low | fast |
| claude_sonnet | anthropic | claude-sonnet-4-5-20250929 | no | yes | medium | fast |

---

### 2. Model Selector — Scoring Engine (Milestone 3A/3B)
**Purpose:** Pure deterministic ranking engine. Applies hard filters then soft scoring.

**Code:**
- `app/services/model_selector.py`
  - Class: `ModelSelector`
  - Method: `select(constraints: RouteConstraints) -> List[ModelCandidate]`
  - Dataclass: `SelectionConfig` — tunable weights for cost, latency, provider preference, task nudges, capability bonuses

**Hard Filters** (`model_selector.py:72-81`):
- `needs_web` → requires `supports_web=True`
- `needs_code` → requires `good_for_code=True`
- `output_format=json` → requires `supports_json=True`
- `latency_tier=fast` → requires `latency_hint=fast`
- `cost_tier` ≤ `max_cost_tier`

**Soft Scoring** (lower = better):
- Weighted sum: `cost_tier * w_cost + latency * w_latency + provider_pref * w_provider_pref + task_nudge + bonuses`
- Deterministic tie-break: sort by `(score, provider_rank, key, model)`

---

### 3. Deterministic Router (Milestone 3A/3B)
**Purpose:** Converts a `PromptProfile` into a `RouteDecision` with ranked candidates.

**Code:**
- `app/services/deterministic_router.py`
  - Class: `DeterministicRouter`
  - Method: `route(profile: PromptProfile) -> RouteDecision`

**MVP Task-Type Routing Map** (`deterministic_router.py:8-14`):

| Task Type | Preferred Provider | Rationale |
|-----------|--------------------|-----------|
| web_search | gemini | Best web/grounding support |
| coding | anthropic | Best code generation |
| text_generation | openai | Fast, cheap text generation |
| summarization | openai | Fast, cheap text processing |
| extraction | openai | Fast, cheap data extraction |

The router promotes the preferred provider to the top of the candidates list. If the preferred provider isn't available (filtered out by hard constraints), it falls back to the next best candidate by score.

---

### 4. Routing Schemas (Milestone 3A)
**Purpose:** Pydantic models for the routing pipeline.

**Code:**
- `app/schemas/routing.py`
  - `RouteConstraints` — machine-readable constraints derived from `PromptProfile`
  - `ModelCandidate` — a scored candidate model
  - `RouteDecision` — full routing output (constraints, candidates, selected, reason)
  - `RouteRequest` / `RouteResponse` — API contract for `POST /v1/route`

---

### 5. Route Endpoint (Milestone 3A)
**Purpose:** Expose deterministic routing as a standalone API (no LLM call).

**Code:**
- `app/api/v1/routes_route_to_model.py`
  - Endpoint: `POST /v1/route`
  - Input: `RouteRequest` (contains `PromptProfile`)
  - Output: `RouteResponse` (contains `RouteDecision`)

---

### 6. LLM Completion Client (Milestone 3B)
**Purpose:** Generic client that dispatches to the correct provider SDK.

**Code:**
- `app/services/LLM_completion.py`
  - Class: `LLMCompletionClient`
  - Method: `generate(prompt, provider, model) -> str`
  - Supports: Gemini (`google-genai`), OpenAI (`openai`), Anthropic (`anthropic`)
  - Lazy client initialization per provider (first call creates the SDK client)
  - API keys from environment: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

---

### 7. Completion Service (Milestone 3B)
**Purpose:** Orchestrator that ties routing + execution together with fallback.

**Code:**
- `app/services/completion_service.py`
  - Function: `execute_completion(prompt_id, db, client) -> CompletionResponse`
  - Pipeline:
    1. Load `Prompt` from DB (validate exists + has profile)
    2. Reconstruct `PromptProfile` from stored JSON
    3. Load model catalog, run `DeterministicRouter.route()`
    4. Execute LLM call on selected model
    5. On failure, fall back to next candidate (up to 3 attempts)
    6. Return response with text, provider, model, attempts, and full route decision

---

### 8. Completion Endpoint (Milestone 3B)
**Purpose:** Full pipeline endpoint — route a profiled prompt and execute the LLM call.

**Code:**
- `app/api/v1/routes_completion.py`
  - Endpoint: `POST /v1/completions`
  - Input: `CompletionRequest` (`prompt_id`)
  - Output: `CompletionResponse` (text, provider, model, attempts, route_decision)
  - Errors: 404 (prompt not found), 422 (no profile / no candidates), 502 (all providers failed)
- `app/schemas/completion.py`
  - `CompletionRequest`, `CompletionResponse`

---

### 9. Profiler Prompt Refinement (Milestone 3B)
**Purpose:** Align the Gemini profiler's classification with the routing logic.

**Code:**
- `app/services/gemini_profiler.py`
  - Updated system instruction with clear task_type definitions and examples
  - Each task_type description matches the routing map (web_search→gemini, coding→anthropic, text/summarization/extraction→openai)
  - Tightened boolean flag guidance (`needs_web`, `needs_code`)

---

## Architecture — Full Pipeline

```
Client
  │
  ▼
POST /v1/prompts          ← Milestone 1+2
  │ Store prompt + call Gemini profiler
  │ Return prompt_id + PromptProfile
  ▼
POST /v1/completions      ← Milestone 3B
  │
  ├─ 1. Load prompt + profile from DB
  ├─ 2. DeterministicRouter.route(profile)
  │     ├─ Convert profile → RouteConstraints
  │     ├─ ModelSelector.select(constraints)  ← hard filters + soft scoring
  │     └─ Promote preferred provider by task_type
  ├─ 3. LLMCompletionClient.generate(prompt, provider, model)
  │     ├─ Try selected model
  │     ├─ On failure → try fallback #2
  │     └─ On failure → try fallback #3
  └─ 4. Return CompletionResponse
```

---

## Dependencies Added

| Package | Purpose |
|---------|---------|
| `google-genai` | Gemini SDK for profiling + completion |
| `openai` | OpenAI SDK for GPT-4o-mini completion |
| `anthropic` | Anthropic SDK for Claude completion |
| `python-dotenv` | Load `.env` file for API keys |

---

## Environment Variables

| Variable | Required For |
|----------|-------------|
| `GEMINI_API_KEY` | Prompt profiling + Gemini completion |
| `OPENAI_API_KEY` | OpenAI completion |
| `ANTHROPIC_API_KEY` | Claude completion |

Stored in `.env` at project root (gitignored). Loaded via `dotenv` in `app/main.py`.

---

## Tests Added

### `tests/unit/test_completion.py` (5 tests)
- `test_completion_happy_path` — First candidate succeeds, routes coding→anthropic
- `test_completion_fallback` — First fails, second succeeds
- `test_completion_all_fail` — All candidates fail, raises RuntimeError
- `test_completion_prompt_not_found` — Non-existent prompt_id returns LookupError
- `test_completion_no_profile` — Prompt without profile returns ValueError

### `tests/unit/test_deterministic_router.py` (11 tests)
- `test_coding_routes_to_anthropic` — coding task → anthropic
- `test_web_search_routes_to_gemini` — web_search task → gemini
- `test_text_generation_routes_to_openai` — text_generation → openai
- `test_summarization_routes_to_openai` — summarization → openai
- `test_extraction_routes_to_openai` — extraction → openai
- `test_fallback_when_preferred_provider_missing` — Preferred provider absent, falls back by score
- `test_no_candidates_when_constraints_unsatisfiable` — Web search with no web models → empty
- `test_empty_catalog` — Empty catalog → no candidates
- `test_all_passing_candidates_returned` — All qualifying models in candidates list
- `test_urgency_fast_maps_to_latency_fast` — Urgency→latency mapping
- `test_urgency_normal_maps_to_latency_normal` — Urgency→latency mapping

---

## How To Test

### 1. Start Server
```bash
make run
```

### 2. Profile a Prompt
```bash
curl -X POST http://127.0.0.1:8000/v1/prompts \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "prompt": "Write a Python function to sort a list"}'
```

### 3. Execute Completion
```bash
curl -X POST http://127.0.0.1:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{"prompt_id": 1}'
```

### 4. Expected Response (Example)
```json
{
  "prompt_id": 1,
  "text": "def sort_list(lst):\n    return sorted(lst)",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "attempts": 1,
  "route_decision": {
    "constraints": { "task_type": "coding", "needs_code": true, "..." : "..." },
    "candidates": [ "..." ],
    "selected": { "provider": "anthropic", "key": "claude_sonnet", "..." : "..." },
    "reason": "Selected anthropic:claude_sonnet — preferred provider for task_type=coding"
  }
}
```

### 5. Run Unit Tests
```bash
make test
```

---

## Future Extensions

### Milestone 4 — Cost & Policy Engine
- Budget caps per user/org
- Provider quotas and rate limiting
- SLA constraints

### Milestone 5 — Safety & Compliance
- Risk classification
- PII detection
- Content policy checks

### Milestone 6 — Learning Router
- Meta-model for self-improving routing
- Quality/cost/latency optimization
- Traffic pattern adaptation