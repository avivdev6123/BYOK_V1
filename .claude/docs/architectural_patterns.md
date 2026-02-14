# Architectural Patterns & Design Decisions

## Layered Architecture

The codebase follows a strict layered design:

```
API Routes (app/api/v1/routes_*.py)
    ↓ Depends()
Services (app/services/*.py)
    ↓
ORM Models (app/db/*.py)
    ↓
SQLite (byok.db)
```

Business logic never lives in route handlers. Routes handle HTTP concerns (status codes, error responses); services handle domain logic. See `app/api/v1/routes_prompts.py` for the pattern.

## Dependency Injection via FastAPI Depends()

Database sessions are injected into route handlers using `Depends(get_db)` from `app/db/session.py:11`. Services are instantiated at module level (e.g., `GeminiPromptProfiler()` in `app/api/v1/routes_prompts.py`). No global mutable state.

## Provider Adapter Pattern

Abstract base class `ProviderAdapter` (`app/providers/base.py`) defines the contract:

- `generate(prompt, max_output_tokens, require_json) -> str`

Concrete adapters: `GeminiAdapter` (`app/providers/gemini_adapter.py`), `OpenAIAdapter` (`app/providers/openai_adapter.py`). New providers implement this interface.

## Deterministic Routing Engine

The routing pipeline is a pure function with no randomness:

1. `PromptProfile` (from LLM profiling) is converted to `RouteConstraints` in `DeterministicRouter` (`app/services/deterministic_router.py`)
2. `ModelSelector.select()` (`app/services/model_selector.py`) applies hard filters then soft scoring
3. Hard filters: capability requirements (web, code, JSON, latency) eliminate non-qualifying models
4. Soft scoring: weighted sum of cost_tier, latency_tier, provider_preference, task_nudges, capability_bonuses
5. Deterministic tie-break: sort by `(score, provider_rank, key, model)` ensures reproducibility

Scoring weights are configurable via `SelectionConfig` dataclass in `app/services/model_selector.py`.

## Fallback Chain

`route_and_generate()` in `app/services/router.py` builds a fallback chain of top 3 candidates. If the primary model fails, it retries with the next candidate. Each attempt is tracked in the response.

## Validation Layers

Validation occurs at multiple boundaries:

1. **API input**: FastAPI + Pydantic automatic validation on request bodies (`app/schemas/`)
2. **LLM output**: `GeminiPromptProfiler` (`app/services/gemini_profiler.py`) validates Gemini's JSON response against `PromptProfile` schema before storage
3. **Routing constraints**: `ModelSelector` filters by hard constraints before scoring
4. **JSON responses**: `Validator` service (`app/services/validator.py`) checks `require_json` responses

Core principle from `docs/checklist.md`: treat all AI/LLM output as untrusted input.

## Pydantic Schema Conventions

- Request models: `*Request` suffix (e.g., `PromptCreateRequest`)
- Response models: `*Response` suffix (e.g., `PromptReadWithProfileResponse`)
- Internal domain objects: No suffix (e.g., `PromptProfile`, `RouteConstraints`, `ModelCandidate`)
- All schemas live in `app/schemas/` with one file per domain area

## Database Patterns

- SQLAlchemy ORM with declarative base (`app/db/base.py`)
- Session factory via `get_db()` generator in `app/db/session.py`
- JSON columns store validated Pydantic dicts (validate before write, reconstruct on read)
- Nullable columns for backward compatibility when adding new fields (e.g., `prompt_profile_json`)
- Tables: `users`, `budgets`, `request_logs`, `prompts`, `provider_keys`, `models_catalog`
- Model definitions split across `app/db/models.py`, `app/db/prompt_models.py`, `app/db/model_catalog_models.py`

## Error Handling Convention

HTTP status codes follow a consistent pattern across all routes:

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Invalid user input | Empty prompt |
| 404 | Resource not found | Unknown prompt ID |
| 422 | Valid request, no result | No models match constraints |
| 500 | Internal error | Empty model catalog |
| 502 | External provider failure | Gemini returns invalid JSON |

Services raise exceptions or return error indicators; route handlers translate to HTTP responses.

## Cost Tracking

Every request is logged with estimated cost in `RequestLog`. Token estimation uses a simple heuristic (`len(text) / 4`) in `app/utils/token_estimator.py`. Pricing is defined per (provider, model) tuple in `app/services/cost.py`.

## API Versioning

All routes are prefixed with `/v1/` and grouped by tags (`generate`, `usage`, `prompts`, `model_routing`). Router registration happens in `app/main.py`.

## Milestone-Driven Development

Features are scoped to milestones. Each milestone has documentation in `docs/`, a commit message prefix (`Milestone N: ...`), and follows the engineering checklist in `docs/checklist.md`.