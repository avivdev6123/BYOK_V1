# BYOK Router

## Project Overview

BYOK (Bring Your Own Key) is an LLM routing and orchestration platform. It accepts user prompts, classifies them using an LLM (Gemini), then deterministically routes to the best provider/model based on cost, latency, and capability constraints. Supports fallback chains and cost tracking.

**Current state**: Milestone 3B (enhanced model scoring with task-type nudges and capability bonuses). Branch: `milestone_3b`.

## Tech Stack

- **Framework**: FastAPI + Uvicorn (async)
- **Validation**: Pydantic v2
- **ORM**: SQLAlchemy 2.0 with SQLite (`byok.db`)
- **LLM Providers**: Google Gemini (primary, via `google-genai`), OpenAI (stub)
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Linting**: ruff
- **Python**: 3.x (see `pyproject.toml` for exact version)

## Project Structure

```
app/
├── api/v1/              # FastAPI route handlers (HTTP layer only)
│   ├── routes_generate.py       # POST /v1/generate
│   ├── routes_prompts.py        # POST/GET /v1/prompts
│   ├── routes_route_to_model.py # POST /v1/route
│   └── routes_usage.py          # GET /v1/usage
├── db/                  # Database layer
│   ├── base.py                  # SQLAlchemy declarative base
│   ├── session.py               # DB connection + get_db() dependency
│   ├── models.py                # User, Budget, RequestLog, ProviderKey
│   ├── prompt_models.py         # Prompt table (Milestone 1-2)
│   └── model_catalog_models.py  # ModelCatalog table (Milestone 3)
├── providers/           # LLM provider adapters (abstract base + implementations)
│   ├── base.py                  # ProviderAdapter ABC
│   ├── gemini_adapter.py
│   └── openai_adapter.py
├── schemas/             # Pydantic request/response models
│   ├── prompts.py               # PromptProfile, PromptCreateRequest
│   ├── routing.py               # RouteConstraints, ModelCandidate, RouteDecision
│   └── generate.py              # GenerateRequest, GenerateResponse
├── services/            # Business logic (no HTTP concerns)
│   ├── gemini_profiler.py       # LLM-based prompt classification
│   ├── model_selector.py        # Deterministic scoring + ranking
│   ├── deterministic_router.py  # Profile -> RouteDecision pipeline
│   ├── router.py                # Route + generate with fallback chain
│   ├── cost.py                  # Token-based cost estimation
│   ├── model_catalog_repo.py    # Load catalog from DB
│   ├── model_catalog.py         # Static model registry
│   ├── LLM_completion.py        # Generic LLM completion client
│   └── validator.py             # JSON validation utility
├── utils/
│   └── token_estimator.py       # Heuristic token counting (len/4)
└── main.py              # App initialization, middleware, router registration
docs/                    # Milestone docs, system context, engineering checklist
tests/unit/              # Unit tests (pytest-asyncio)
```

## Essential Commands

```bash
make run          # Start dev server (uvicorn with reload)
make test         # Run pytest
make lint         # Run ruff
pytest -v         # Verbose test output
pytest --cov=app  # With coverage
```

## Environment Variables

- `GEMINI_API_KEY` - Required for prompt profiling and Gemini generation
- Copy `.env.example` to `.env` and fill in values

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/prompts` | Ingest + profile a prompt |
| GET | `/v1/prompts` | List recent prompts |
| GET | `/v1/prompts/{id}` | Get prompt with profile |
| POST | `/v1/route` | Deterministic model routing |
| POST | `/v1/generate` | Route + generate with fallback |
| GET | `/v1/usage` | Cost tracking & analytics |

## Database

SQLite file at project root (`byok.db`). Tables: `users`, `budgets`, `request_logs`, `prompts`, `provider_keys`, `models_catalog`. Tables are auto-created on startup via `Base.metadata.create_all()` in `app/db/session.py`.

## Testing

Tests live in `tests/unit/`. Async tests use `@pytest.mark.asyncio`. Config in `pytest.ini` sets `--maxfail=1` and coverage reporting. Current tests cover: fallback chain, Pydantic validation, cost estimation, JSON validation.

## Milestones

| # | Status | Description |
|---|--------|-------------|
| 1 | Done | Prompt ingestion + DB storage |
| 2 | Done | Gemini-based prompt profiling with JSON schema validation |
| 3A | Done | Model catalog DB + deterministic routing engine |
| 3B | In progress | Enhanced scoring (task nudges, capability bonuses) |
| 4 | Planned | Cost & policy enforcement |
| 5 | Planned | Safety & compliance |
| 6 | Planned | Learning router (meta-model) |

## Commit Convention

Prefix commits with milestone: `Milestone N: description`

## Additional Documentation

When working on specific topics, consult these files:

- `.claude/docs/architectural_patterns.md` - Layered architecture, dependency injection, provider adapter pattern, deterministic routing engine, validation layers, error handling conventions, database patterns
- `docs/BYOK_context.md` - Project vision, goals, and milestone roadmap
- `docs/BYOK_SYSTEM_CONTEXT.md` - Canonical system description for AI context
- `docs/checklist.md` - Engineering discipline rules (pre-steps, safety, git workflow)
- `docs/MILESTONE_2.md` - Prompt profiling architecture and validation details
