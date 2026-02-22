"""
app/api/v1/routes_keys.py
-------------------------
Milestone 4: API key management endpoints.

POST   /keys                      — store/update a provider API key (validates on save)
GET    /keys                      — list user's keys (masked, with status)
DELETE /keys/{provider}            — remove a stored key
POST   /keys/{provider}/revalidate — re-check an existing key
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.api.dependencies import get_current_user
from app.schemas.keys import KeyCreateRequest, KeyResponse, KeyListResponse
from app.services.key_service import store_key, get_user_keys, delete_key, revalidate_key

router = APIRouter()


def _key_to_response(key) -> KeyResponse:
    return KeyResponse(
        id=key.id,
        provider=key.provider,
        api_key_masked=key.api_key_masked,
        status=key.status or "pending",
        validated_at=key.validated_at,
        discovered_models=key.discovered_models,
        created_at=key.created_at,
    )


@router.post("/keys", response_model=KeyResponse, status_code=201)
def add_key(
    req: KeyCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KeyResponse:
    key = store_key(user.id, req.provider, req.api_key, db)
    return _key_to_response(key)


@router.get("/keys", response_model=KeyListResponse)
def list_keys(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KeyListResponse:
    keys = get_user_keys(user.id, db)
    return KeyListResponse(keys=[_key_to_response(k) for k in keys])


@router.delete("/keys/{provider}")
def remove_key(
    provider: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if provider not in ("gemini", "openai", "anthropic"):
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    delete_key(user.id, provider, db)
    return {"status": "deleted", "provider": provider}


@router.post("/keys/{provider}/revalidate", response_model=KeyResponse)
def revalidate(
    provider: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KeyResponse:
    if provider not in ("gemini", "openai", "anthropic"):
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    key = revalidate_key(user.id, provider, db)
    if not key:
        raise HTTPException(status_code=404, detail=f"No key stored for {provider}")
    return _key_to_response(key)