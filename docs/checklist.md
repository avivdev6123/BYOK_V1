# BYOK Engineering Checklist

This checklist defines the rules and guardrails for building BYOK as a
production-grade LLM routing platform.

Use it before, during, and after every milestone.

---

## 0) Pre-steps Before Starting a New Milestone

- [ ] Create a new git branch: `milestone-<n>-<name>`
- [ ] Read previous milestone doc: `docs/milestones/milestone<n-1>.md`
- [ ] Define the new milestone goal in `docs/milestones/milestone<n>.md`
- [ ] Write clear success criteria (“Demo = …”)
- [ ] Run the app locally: `uvicorn app.main:app --reload`
- [ ] Verify `/health` returns OK
- [ ] Verify Swagger loads and existing endpoints work
- [ ] Confirm database tables exist and match ORM models
- [ ] Ensure environment variables (API keys) are loaded
- [ ] Freeze scope for the milestone (no feature creep)

---

## 1) When Creating or Modifying a Data Model (SQLAlchemy)

- [ ] Update ORM model in `app/db/*.py`
- [ ] Ensure model is imported so SQLAlchemy registers it
- [ ] Decide migration strategy:
  - [ ] Dev reset (drop DB)
  - [ ] Migration (Alembic later)
- [ ] Verify table and columns exist in SQLite
- [ ] Mark backward-compatible fields as `nullable=True`
- [ ] Add indexes to frequently queried columns
- [ ] Store JSON as dict, not Pydantic objects
- [ ] Validate data with Pydantic before persisting

---

## 2) When Creating or Updating Pydantic Schemas

- [ ] Define request models
- [ ] Define response models
- [ ] Enforce:
  - [ ] Enums via `Literal`
  - [ ] String length limits
  - [ ] Numeric ranges with `Field(ge, le)`
- [ ] Attach schemas to endpoints with `response_model=...`
- [ ] Test invalid payloads (expect ValidationError)
- [ ] Confirm Swagger reflects schema accurately

---

## 3) When Creating a New Endpoint (FastAPI)

- [ ] Define contract:
  - [ ] Method
  - [ ] Path
  - [ ] Request body
  - [ ] Response body
  - [ ] Error codes
- [ ] Place endpoint in correct router module
- [ ] Use dependency injection (`Depends(get_db)`)
- [ ] Validate input (empty, type, bounds)
- [ ] Handle not-found with 404
- [ ] Wrap external calls in try/except
- [ ] Return 502 for provider failures
- [ ] Test:
  - [ ] Happy path
  - [ ] Failure path

---

## 4) When Integrating an External LLM Provider

- [ ] Provider logic lives in `app/services/`
- [ ] API keys from environment only
- [ ] One call per request unless explicitly required
- [ ] Strict output format (JSON only)
- [ ] Schema validation before persistence
- [ ] Log provider errors
- [ ] Never trust raw LLM output

---

## 5) Before Committing and Pushing to GitHub

- [ ] Application runs without errors
- [ ] All endpoints respond
- [ ] Remove debug code (`pdb`, fake mocks, prints)
- [ ] Update milestone documentation
- [ ] Ensure:
  - [ ] Architecture section
  - [ ] Validation & Safety
  - [ ] How To Test
  - [ ] Future Extensions
- [ ] `git status` is clean
- [ ] Commit message is milestone-quality

---

## 6) Git Workflow

- [ ] `git add -A`
- [ ] `git commit -m "Milestone N: <description>"`
- [ ] `git push -u origin milestone-N`
- [ ] Open PR to `main`
- [ ] Merge after review
- [ ] (Optional) Tag release: `v0.N`

---

## 7) Safety Rules (Never Break These)

- [ ] Never store unvalidated LLM output
- [ ] Never swallow provider errors
- [ ] Never mix routing logic inside API routers
- [ ] Never rename fields without migration plan
- [ ] Never depend on chat memory — update docs instead
- [ ] Always treat AI output as untrusted input

---

## 8) Documentation Discipline

Every milestone must have:

- Goal
- Code references (files + classes)
- Architecture changes
- Validation & safety
- How to test
- Future roadmap

Documentation is part of the system, not an afterthought.

---

This checklist turns BYOK into a **production-grade AI infrastructure project**, not a demo.