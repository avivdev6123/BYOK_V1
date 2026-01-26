"""
API routes for Prompt intake (Milestone 1 + Milestone 2).

Responsibilities:
- Receive user prompt
- Store it in database
- Run ONE LLM call to classify the prompt into a JSON profile (Milestone 2)
- Store prompt_profile_json in DB
- Allow retrieval by ID (including stored profile)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# DB session dependency (FastAPI injects a DB session into each request)
from app.db.session import get_db

# ORM model (prompts table)
from app.db.prompt_models import Prompt

# Pydantic schemas (request + response)
from app.schemas.prompts import (
    PromptCreateRequest,
    PromptCreateWithProfileResponse,
    PromptReadWithProfileResponse,
    PromptProfile,
)

# Gemini profiler service (real LLM call)
from app.services.gemini_profiler import GeminiPromptProfiler


# Router object to be mounted in main.py
router = APIRouter()

# Create ONE profiler instance at import time
# This avoids re-initializing the Gemini client on every request
profiler = GeminiPromptProfiler()


@router.post("/prompts", response_model=PromptCreateWithProfileResponse)
def create_prompt(
    req: PromptCreateRequest,
    db: Session = Depends(get_db)
) -> PromptCreateWithProfileResponse:
    """
    Milestone 2 behavior:

    - User sends a prompt
    - We call Gemini ONCE to generate a JSON profile for the prompt
    - We store both the raw prompt and the JSON profile in the database
    - We return the stored record + profile
    """

    # ----------------------------
    # 1) Validate input + normalize
    # ----------------------------

    # Keep using the Milestone 1 field name "prompt"
    raw_prompt = req.prompt.strip()

    # Extra safety: avoid empty prompt after stripping spaces
    if not raw_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    # ----------------------------
    # 2) Call Gemini profiler ONCE
    # ----------------------------
    # This returns a PromptProfile Pydantic object (already validated)
    try:
        profile: PromptProfile = profiler.profile(raw_prompt)
    except Exception as e:
        # If Gemini fails or returns invalid JSON, return 502 (bad gateway)
        # because we depend on an external provider.
        raise HTTPException(status_code=502, detail=f"Profiler failed: {str(e)}")

    # ----------------------------
    # 3) Store prompt + profile in DB
    # ----------------------------

    # Create ORM object
    row = Prompt(
        username=req.username,
        raw_prompt=raw_prompt,
        # Store JSON as a python dict in DB (SQLAlchemy JSON type handles serialization)
        prompt_profile_json=profile.model_dump()
    )

    # Persist to database
    db.add(row)
    db.commit()
    db.refresh(row)  # Load generated ID and stored fields

    # ----------------------------
    # 4) Return response
    # ----------------------------

    return PromptCreateWithProfileResponse(
        prompt_id=row.id,
        username=row.username,
        raw_prompt=row.raw_prompt,
        prompt_profile_json=profile,
    )


@router.get("/prompts")
def list_prompts(db: Session = Depends(get_db)):
    """
    Return a list of stored prompts (latest 20).
    Helpful for quick browsing.
    """
    rows = db.query(Prompt).order_by(Prompt.id.desc()).limit(20).all()

    return [
        {
            "id": r.id,
            "username": r.username,
            "created_at": r.created_at.isoformat(),
            # Show whether the profile exists (useful while debugging migrations)
            "has_profile": bool(r.prompt_profile_json),
        }
        for r in rows
    ]


@router.get("/prompts/{prompt_id}", response_model=PromptReadWithProfileResponse)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> PromptReadWithProfileResponse:
    """
    Retrieve a stored prompt by its ID (Milestone 2).

    Returns:
    - raw prompt fields
    - created_at
    - stored prompt_profile_json (if exists)
    """

    # Query by primary key
    row = db.query(Prompt).filter(Prompt.id == prompt_id).first()

    # If row doesn't exist, return 404
    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Convert stored JSON (dict) back into PromptProfile (validated)
    profile_obj = None
    if row.prompt_profile_json:
        profile_obj = PromptProfile(**row.prompt_profile_json)

    return PromptReadWithProfileResponse(
        prompt_id=row.id,
        username=row.username,
        raw_prompt=row.raw_prompt,
        created_at=row.created_at,
        prompt_profile_json=profile_obj,
    )