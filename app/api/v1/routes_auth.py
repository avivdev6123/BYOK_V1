"""
app/api/v1/routes_auth.py
-------------------------
Milestone 4: Authentication endpoints.

POST /auth/register — create a new user
POST /auth/login    — authenticate and get session token
POST /auth/logout   — invalidate session token
GET  /auth/me       — get current user info
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.api.dependencies import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
)
from app.services.auth_service import register_user, login_user, logout

router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user = register_user(req.username, req.password, db)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    # Auto-login after registration
    _, token = login_user(req.username, req.password, db)
    return AuthResponse(user_id=user.id, username=user.username, session_token=token)


@router.post("/auth/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    try:
        user, token = login_user(req.username, req.password, db)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return AuthResponse(user_id=user.id, username=user.username, session_token=token)


@router.post("/auth/logout")
def logout_endpoint(
    _user: User = Depends(get_current_user),
    authorization: str = Header(..., alias="Authorization"),
):
    token = authorization[7:]  # strip "Bearer "
    logout(token)
    return {"status": "logged out"}


@router.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(user_id=user.id, username=user.username)