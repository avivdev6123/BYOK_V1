### A. Project structure
```code
app/
  api/v1/routes_prompts.py
  services/gemini_profiler.py
  schemas/prompts.py
  db/prompt_models.py
  db/session.py
  main.py
```

### B. Core models & fields
```code
DB Table: prompts
Columns:
- id (int, PK)
- username (str)
- raw_prompt (text)
- created_at (datetime)
- prompt_profile_json (json)

Pydantic:
- PromptProfile
  - task_type
  - needs_web
  - needs_code
  - output_format
  - urgency
  - confidence
```

### C. Key classes
```code
GeminiPromptProfiler (app/services/gemini_profiler.py)
Prompt (SQLAlchemy model)
PromptProfile (Pydantic)
```

### D. API contracts
```code
POST /v1/prompts
GET /v1/prompts/{id}
```

# Use a “Memory Bootstrap Prompt” 
At the start of any new chat, paste something like:
```prompt
Load project context from the following canonical description and treat it as source-of-truth for file names, models, DB schema, and APIs:
```
Then paste your BYOK_SYSTEM_CONTEXT.md.