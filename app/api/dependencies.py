"""
app/api/dependencies.py
-----------------------
Milestone 4: FastAPI auth dependencies.

get_current_user: required auth (raises 401)
get_optional_user: optional auth (returns None if no header)
"""

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.services.auth_service import get_user_from_token


def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """Extract Bearer token from Authorization header, resolve to User."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization[7:]
    try:
        return get_user_from_token(token, db)
    except LookupError as e:
        raise HTTPException(status_code=401, detail=str(e))


def get_optional_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User | None:
    """Same as get_current_user but returns None if no auth header present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        return get_user_from_token(token, db)
    except LookupError:
        return None