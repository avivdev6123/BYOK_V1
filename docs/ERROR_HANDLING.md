# BYOK Router — Error Handling Reference

This document describes all errors the application handles across the backend API, LLM provider interactions, and the Streamlit chat UI.

---

## 1. API Route Handlers

### POST /v1/prompts — Prompt Ingestion & Profiling

| HTTP Status | Error Type | Module | Condition | Error Message | Source |
|-------------|-----------|--------|-----------|---------------|--------|
| 400 | `HTTPException` | `fastapi` | Prompt is empty after trimming whitespace | "Prompt cannot be empty" | `app/api/v1/routes_prompts.py:72` |
| 502 | `HTTPException` (wraps `Exception`) | `fastapi` | Gemini profiler fails (API error, invalid JSON, rate limit) | "Profiler failed: {error details}" | `app/api/v1/routes_prompts.py:82` |
| 404 | `HTTPException` | `fastapi` | GET by ID — prompt not found | "Prompt not found" | `app/api/v1/routes_prompts.py:153` |

### POST /v1/completions — Route + Execute LLM

| HTTP Status | Error Type | Module | Condition | Error Message | Source |
|-------------|-----------|--------|-----------|---------------|--------|
| 404 | `HTTPException` (wraps `LookupError`) | `fastapi` (wraps `builtins`) | Prompt ID does not exist in the database | "Prompt {id} not found" | `app/api/v1/routes_completion.py:30` |
| 422 | `HTTPException` (wraps `ValueError`) | `fastapi` (wraps `builtins`) | Prompt exists but has no profile | "Prompt {id} has no profile — run profiling first" | `app/api/v1/routes_completion.py:32` |
| 422 | `HTTPException` (wraps `ValueError`) | `fastapi` (wraps `builtins`) | No models match the routing constraints | "No models match constraints for prompt {id}: {reason}" | `app/api/v1/routes_completion.py:32` |
| 502 | `HTTPException` (wraps `RuntimeError`) | `fastapi` (wraps `builtins`) | Model catalog is empty (no models seeded) | "Model catalog is empty. Seed models_catalog table." | `app/api/v1/routes_completion.py:34` |
| 502 | `HTTPException` (wraps `RuntimeError`) | `fastapi` (wraps `builtins`) | All fallback attempts failed | "All {n} attempts failed. Last error: {error}" | `app/api/v1/routes_completion.py:34` |

### POST /v1/route — Deterministic Routing (no LLM call)

| HTTP Status | Error Type | Module | Condition | Error Message | Source |
|-------------|-----------|--------|-----------|---------------|--------|
| 500 | `HTTPException` | `fastapi` | Model catalog is empty | "Model catalog is empty. Seed models_catalog table." | `app/api/v1/routes_route_to_model.py:19` |
| 422 | `HTTPException` | `fastapi` | No model selected after routing | Route decision reason | `app/api/v1/routes_route_to_model.py:29` |

### POST /v1/generate — Legacy Route + Generate

| HTTP Status | Error Type | Module | Condition | Error Message | Source |
|-------------|-----------|--------|-----------|---------------|--------|
| 400 | `HTTPException` (wraps `Exception`) | `fastapi` (wraps `builtins`) | Any exception from the legacy pipeline | Error message from exception | `app/api/v1/routes_generate.py:12` |

### GET /v1/usage — Cost Tracking

| HTTP Status | Error Type | Module | Condition | Error Message | Source |
|-------------|-----------|--------|-----------|---------------|--------|
| 200 | None (returns error in body) | N/A | User not found | `{"error": "user not found"}` | `app/api/v1/routes_usage.py:14` |

---

## 2. Service Layer Errors

### Completion Service (`app/services/completion_service.py`)

| Error Type | Module | Condition | Behavior | Source |
|------------|--------|-----------|----------|--------|
| `LookupError` | `builtins` | Prompt ID not in database | Raised to route handler (mapped to 404) | `app/services/completion_service.py:33` |
| `ValueError` | `builtins` | No profile on prompt | Raised to route handler (mapped to 422) | `app/services/completion_service.py:36` |
| `RuntimeError` | `builtins` | Empty model catalog | Raised to route handler (mapped to 502) | `app/services/completion_service.py:43` |
| `ValueError` | `builtins` | No candidates match constraints | Raised to route handler (mapped to 422) | `app/services/completion_service.py:50` |
| `Exception` (any) | various | LLM provider call fails | Caught silently, moves to next fallback candidate | `app/services/completion_service.py:78` |
| `RuntimeError` | `builtins` | All fallback candidates exhausted | Raised to route handler (mapped to 502) | `app/services/completion_service.py:81` |

### Gemini Profiler (`app/services/gemini_profiler.py`)

| Error Type | Module | Condition | Behavior | Source |
|------------|--------|-----------|----------|--------|
| `RuntimeError` | `builtins` | `GEMINI_API_KEY` not set | Raised at profiler initialization | `app/services/gemini_profiler.py:26` |
| `RuntimeError` (wraps `JSONDecodeError`) | `builtins` (wraps `json`) | Gemini response is not valid JSON | Raised after JSON parsing attempt | `app/services/gemini_profiler.py:108` |
| `RuntimeError` (wraps `ValidationError`) | `builtins` (wraps `pydantic`) | JSON does not match PromptProfile schema | Raised after Pydantic validation | `app/services/gemini_profiler.py:113` |

### LLM Completion Client (`app/services/LLM_completion.py`)

| Error Type | Module | Condition | Behavior | Source |
|------------|--------|-----------|----------|--------|
| `RuntimeError` | `builtins` | `GEMINI_API_KEY` not set | Raised on first Gemini call | `app/services/LLM_completion.py:44` |
| `RuntimeError` | `builtins` | `OPENAI_API_KEY` not set | Raised on first OpenAI call | `app/services/LLM_completion.py:52` |
| `RuntimeError` | `builtins` | `ANTHROPIC_API_KEY` not set | Raised on first Anthropic call | `app/services/LLM_completion.py:60` |
| `ValueError` | `builtins` | Unsupported provider name | Raised immediately | `app/services/LLM_completion.py:71` |
| SDK exceptions (uncaught) | `google.genai`, `openai`, `anthropic` | Provider API errors (rate limits, auth, network) | Bubble up to completion service fallback logic | `app/services/LLM_completion.py:76-100` |

### Legacy Router (`app/services/router.py`)

| Error Type | Module | Condition | Behavior | Source |
|------------|--------|-----------|----------|--------|
| `RuntimeError` | `builtins` | No models satisfy constraints after filtering | Raised to route handler | `app/services/router.py:42` |
| `RuntimeError` | `builtins` | No models satisfy `max_cost_usd` constraint | Raised to route handler | `app/services/router.py:53` |
| `Exception` (any) | various | Adapter generate or JSON validation fails | Caught, moves to next fallback candidate | `app/services/router.py:78` |
| `RuntimeError` | `builtins` | All fallback attempts exhausted | Raised to route handler | `app/services/router.py:81` |

---

## 3. LLM Provider Errors

These errors originate from the provider SDKs during LLM calls. They are not caught by the completion client — instead they bubble up to the completion service, which uses them to trigger fallback to the next candidate.

| Provider | Error Type | Module | Trigger |
|----------|-----------|--------|---------|
| Gemini | `ResourceExhausted` | `google.api_core.exceptions` | Free-tier quota exceeded (20 req/day) |
| Gemini | `InvalidArgument` | `google.api_core.exceptions` | Bad model name or invalid request |
| Gemini | `PermissionDenied` | `google.api_core.exceptions` | Invalid or revoked API key |
| OpenAI | `RateLimitError` | `openai` | Rate limit or quota exceeded |
| OpenAI | `AuthenticationError` | `openai` | Invalid API key |
| OpenAI | `APIConnectionError` | `openai` | Network/timeout error |
| Anthropic | `RateLimitError` | `anthropic` | Rate limit exceeded |
| Anthropic | `AuthenticationError` | `anthropic` | Invalid API key |
| Anthropic | `APIConnectionError` | `anthropic` | Network/timeout error |

---

## 4. Streamlit Chat UI Errors

The UI catches HTTP errors from the backend and displays user-friendly messages.

### Rate Limit Detection (`ui/chat.py`)

The `format_rate_limit_error()` function (`ui/chat.py:23`) parses error responses for rate limit indicators (keywords: `429`, `quota`, `rate`). When detected, it shows a warning with a link to the provider's account management page:

| Provider | Account Management URL | Source |
|----------|----------------------|--------|
| Gemini | https://aistudio.google.com/apikey | `ui/chat.py:18` |
| OpenAI | https://platform.openai.com/account/billing | `ui/chat.py:19` |
| Anthropic | https://console.anthropic.com/settings/billing | `ui/chat.py:20` |

**Example message:** "The **gemini** API has reached its usage limit. Please upgrade your plan in the provider's account management: [gemini account](https://aistudio.google.com/apikey)"

### Profiling Step Errors (Step 1)

| Condition | Error Type | Module | Display Type | Message | Source |
|-----------|-----------|--------|-------------|---------|--------|
| HTTP error with rate limit keywords | HTTP 429/502 response | `requests` | `st.warning()` | Friendly message with provider account link | `ui/chat.py:115-116` |
| HTTP error (other) | HTTP 4xx/5xx response | `requests` | `st.error()` | "Profiling failed: {detail}" | `ui/chat.py:118` |
| Network/connection failure | `RequestException` | `requests` | `st.error()` | "Profiling failed: {exception}" | `ui/chat.py:122` |

### Completion Step Errors (Step 2)

| Condition | Error Type | Module | Display Type | Message | Source |
|-----------|-----------|--------|-------------|---------|--------|
| HTTP error with rate limit keywords | HTTP 429/502 response | `requests` | `st.warning()` | Friendly message with provider account link | `ui/chat.py:142-143` |
| HTTP error (other) | HTTP 4xx/5xx response | `requests` | `st.error()` | "Completion failed: {detail}" | `ui/chat.py:145` |
| Network/connection failure | `RequestException` | `requests` | `st.error()` | "Completion failed: {exception}" | `ui/chat.py:149` |

All UI errors call `st.stop()` to halt further execution for that message.

---

## 5. Fallback Strategy

### Backend

The completion service (`app/services/completion_service.py:59-81`) implements a fallback chain:

1. Route the prompt to get ranked candidates
2. Try the top-ranked (selected) model first
3. On failure (any `Exception`), catch and try the next candidate
4. Up to `MAX_FALLBACK_ATTEMPTS` (3) total attempts
5. If all fail, raise `RuntimeError` with the last error

### UI

No client-side fallback. On any error `st.stop()` halts execution. The user can retry by sending the prompt again.

---

## 6. HTTP Status Code Summary

| Code | Meaning | Error Type | Module | Used For |
|------|---------|-----------|--------|----------|
| 400 | Bad Request | `HTTPException` | `fastapi` | Empty prompt, legacy pipeline errors |
| 404 | Not Found | `HTTPException` (from `LookupError`) | `fastapi` (from `builtins`) | Prompt ID doesn't exist |
| 405 | Method Not Allowed | Built-in | `fastapi` | Wrong HTTP method on endpoint |
| 422 | Unprocessable Entity | `HTTPException` (from `ValueError`) | `fastapi` (from `builtins`) | Missing profile, no matching models |
| 500 | Internal Server Error | `HTTPException` | `fastapi` | Empty catalog at route level |
| 502 | Bad Gateway | `HTTPException` (from `RuntimeError`) | `fastapi` (from `builtins`) | External provider failures, profiler errors, all fallbacks exhausted |
