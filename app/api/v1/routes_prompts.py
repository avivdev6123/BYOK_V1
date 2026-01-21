"""
API routes for Prompt intake (Milestone 1).

Responsibilities:
- Receive user prompt
- Store it in database
- Return its ID
- Allow retrieval by ID
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.prompt_models import Prompt
from app.schemas.prompts import (
    PromptCreateRequest,
    PromptCreateResponse,
    PromptReadResponse,
)

# Router object to be mounted in main.py
router = APIRouter()


@router.post("/prompts", response_model=PromptCreateResponse)
def create_prompt(
    req: PromptCreateRequest,
    db: Session = Depends(get_db)
) -> PromptCreateResponse:
    """
    Step 1 in the BYOK flow:

    - User sends a prompt
    - We save it to the database
    - We return its unique ID

    No LLM, no routing yet.
    This is pure data ingestion.
    """

    # Create ORM object
    row = Prompt(username=req.username, raw_prompt=req.prompt)

    # Persist to database
    db.add(row)
    db.commit()
    db.refresh(row)  # Load generated ID

    return PromptCreateResponse(prompt_id=row.id)

@router.get("/prompts")
def list_prompts(db: Session = Depends(get_db)):
    """
    Return a list of stored prompts.
    This allows browsing in the browser at /v1/prompts.
    """
    rows = db.query(Prompt).order_by(Prompt.id.desc()).limit(20).all()
    return [
        {
            "id": r.id,
            "username": r.username,
            "created_at": r.created_at.isoformat()
        }
        for r in rows
    ]

@router.get("/prompts/{prompt_id}", response_model=PromptReadResponse)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> PromptReadResponse:
    """
    Retrieve a stored prompt by its ID.
    Useful for:
    - Debugging
    - Building later steps (profiling, routing, execution)
    """

    # Query by primary key
    row = db.query(Prompt).filter(Prompt.id == prompt_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return PromptReadResponse(
        prompt_id=row.id,
        username=row.username,
        raw_prompt=row.raw_prompt,
        created_at=row.created_at,
    )
