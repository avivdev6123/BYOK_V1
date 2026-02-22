"""
API route for LLM completion (Milestone 3B + Milestone 4 per-user keys).

Accepts a prompt_id (already profiled), routes to the best model,
executes the LLM call with fallback, and returns the response.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.api.dependencies import get_optional_user
from app.schemas.completion import CompletionRequest, CompletionResponse
from app.services.completion_service import execute_completion
from app.services.key_service import build_user_keys
from app.services.LLM_completion import LLMCompletionClient

router = APIRouter()


@router.post("/completions", response_model=CompletionResponse)
def create_completion(
    req: CompletionRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> CompletionResponse:
    user_keys = build_user_keys(user.id, db) if user else None
    client = LLMCompletionClient(keys=user_keys)
    try:
        return execute_completion(req.prompt_id, db, client)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))