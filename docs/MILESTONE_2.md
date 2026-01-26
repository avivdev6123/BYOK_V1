# Milestone 2 — Prompt Profiling with Gemini (JSON Extraction)

## Goal
Classify each user prompt into a structured JSON profile using a single LLM call and validate it with Pydantic.

---

## What Was Added (with Code References)

### 1. Gemini LLM Integration
**Purpose:** Call a real LLM once to classify the prompt into structured JSON.

**Code:**
- `app/services/gemini_profiler.py`
  - Class: `GeminiPromptProfiler`
  - Method: `profile(raw_prompt: str) -> PromptProfile`
  - Uses: `google.genai` SDK
  - Enforces strict JSON-only output and schema compliance.

---

### 2. Prompt Profile Schema (Pydantic)
**Purpose:** Enforce strong typing, enum constraints, and numeric ranges on LLM output.

**Code:**
- `app/schemas/prompts.py`
  - Class: `PromptProfile`
  - Enforces:
    - Enum fields: `task_type`, `output_format`, `urgency`
    - Boolean fields: `needs_web`, `needs_code`
    - Range validation: `confidence ∈ [0, 1]`

---

### 3. Database Storage of JSON Profile
**Purpose:** Persist structured LLM understanding for routing and analytics.

**Code:**
- `app/db/prompt_models.py`
  - Column: `prompt_profile_json: JSON`
- SQLite / SQLAlchemy JSON serialization

---

### 4. Prompt Ingestion + Profiling API
**Purpose:** Extend the existing ingestion endpoint to run profiling and store results.

**Code:**
- `app/api/v1/routes_prompts.py`
  - Endpoint: `POST /v1/prompts`
    - Calls `GeminiPromptProfiler.profile()`
    - Validates with `PromptProfile`
    - Stores JSON in `Prompt.prompt_profile_json`
  - Endpoint: `GET /v1/prompts/{id}`
    - Rehydrates JSON into `PromptProfile` object

---

## JSON Profile Schema

Defined in: `app/schemas/prompts.py`

```json
{
  "task_type": "web_search | text_generation | coding | summarization | extraction",
  "needs_web": true,
  "needs_code": false,
  "output_format": "text | json",
  "urgency": "fast | normal",
  "confidence": 0.0
}
```


## Architecture Changes

### Before (Milestone 1)

Flow:

1. Client sends request to `POST /v1/prompts`
2. API stores raw prompt in database
3. API returns prompt ID

Characteristics:
- No semantic understanding
- No structure
- No classification
- No routing signal

---

### After (Milestone 2)

Flow:

1. Client sends request to `POST /v1/prompts`
2. API calls Gemini via `GeminiPromptProfiler`
3. LLM returns structured JSON classification
4. JSON is parsed and validated by `PromptProfile` (Pydantic)
5. Structured profile is stored in `prompt_profile_json`
6. API returns both raw prompt and semantic profile

Characteristics:
- Machine-readable intent
- Strict schema validation
- Persistent semantic layer
- Ready for routing and policy engines

---

### New Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `GeminiPromptProfiler` | Convert natural language prompt into structured intent JSON |
| `PromptProfile` (Pydantic) | Enforce schema, types, enums, and numeric constraints |
| `routes_prompts.py` | Orchestrate profiling, validation, storage, and response |
| `Prompt` ORM model | Persist both raw text and structured semantic profile |

## Validation & Safety

### What Is Validated

| Layer | File | Validation |
|------|------|------------|
| JSON syntax | `app/services/gemini_profiler.py` | Rejects non-JSON LLM output |
| Schema | `app/schemas/prompts.py` | Enforces enums, booleans, numeric ranges |
| API input | FastAPI + Pydantic | Rejects empty or malformed requests |
| Persistence | `app/db/prompt_models.py` | Stores only structured JSON |

### Failure Handling

| Failure Type | Handling |
|---------------|----------|
| LLM returns non-JSON | HTTP 502 (Bad Gateway) |
| Missing / invalid fields | Pydantic `ValidationError` → HTTP 502 |
| Enum mismatch | Request rejected before DB write |
| Out-of-range confidence | Blocked by schema constraints |

This guarantees:
- No invalid AI output enters the system
- No unsafe routing decisions
- No silent data corruption
- Deterministic failure behavior

---

## How To Test

### 1. Start Server

```bash
uvicorn app.main:app --reload
```

### 2. Send Prompt
```bash
curl -X POST http://127.0.0.1:8000/v1/prompts \
-H "Content-Type: application/json" \
-d '{
"username": "demo",
"prompt": "Explain Python TypeError"
}'
```
### 3. Expected Response (Example)
```json
{
"prompt_id": 12,
"username": "demo",
"raw_prompt": "Explain Python TypeError",
"prompt_profile_json": {
"task_type": "coding",
"needs_web": false,
"needs_code": true,
"output_format": "text",
"urgency": "normal",
"confidence": 0.84
}
}
```

### 4. Retrieve Stored Profile
```bash
curl http://127.0.0.1:8000/v1/prompts/12
```

## Future Extensions

### Milestone 3 — Intelligent Routing
- Route by:
    - Task type
    - Latency class
    - Model capability
    - Cost tier
    - Web vs offline needs

### Milestone 4 — Cost & Policy Engine
- Enforce:
   - Budget caps
   - Provider quotas
   - User plans
   - SLA constraints

### Milestone 5 — Safety & Compliance
- Add:
   - Risk classification
   - PII detection
   - Content policy checks
   - Audit logs

### Milestone 6 — Learning Router
- Train a meta-model to:
   - Predict best provider
   - Optimize quality / cost / latency
   - Adapt to traffic patterns
   - Self-improve routing strategy
